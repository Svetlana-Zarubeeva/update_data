import functools
import shutil
import uuid
import time
import logging
from pathlib import Path
from typing import Any, Optional, List, Dict, Set, AsyncIterable, Iterable, Sized, TypeVar, Callable, Iterator, Self

import ujson
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
from pyarrow import Schema, Array
from pyarrow.dataset import dataset, Expression, Dataset

from settings import PARQUET_BATCH_SIZE

_T = TypeVar("_T", bound=Dict[str, Any])


class ParquetDataset(Iterable[_T], Sized):
    _schema: Optional[Schema]
    _dataset: Dataset
    _batch_size: int
    _read_filter: Optional[Expression]
    _serialize_fields: Set[str]
    _remove_after_read: bool

    def __init__(
        self,
        path: str | Path,
        schema: Optional[Schema] = None,
        batch_size: Optional[int] = None,
        read_filter: Optional[Expression] = None,
        serialize_fields: Optional[str | List[str]] = None,
        remove_after_read: bool = False,
        clear_if_exists: bool = False,
        iter_batches_readahead: int = 0,
        iter_fragments_readahead: int = 0,
        iter_use_threads: bool = False,
    ) -> None:
        self.path = Path(path)
        if self.path.exists() and clear_if_exists:
            shutil.rmtree(self.path)
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)
        self._schema = schema
        self._batch_size = batch_size or PARQUET_BATCH_SIZE
        self._read_filter = read_filter
        self._serialize_fields = set([serialize_fields] if isinstance(serialize_fields, str) else (serialize_fields or []))
        self._remove_after_read = remove_after_read
        self._iter_batches_readahead = iter_batches_readahead
        self._iter_fragments_readahead = iter_fragments_readahead
        self._iter_use_threads = iter_use_threads
        self._dataset = dataset(self.path, format="parquet", exclude_invalid_files=True, schema=self._schema)

    def with_override(
        self,
        *,
        batch_size: Optional[int] = None,
        read_filter: Optional[Expression] = None,
        iter_batches_readahead: Optional[int] = None,
        iter_fragments_readahead: Optional[int] = None,
        iter_use_threads: Optional[bool] = None,
    ) -> Self:
        if batch_size is not None:
            self._batch_size = batch_size
        if read_filter is not None:
            self._read_filter = read_filter
        if iter_batches_readahead is not None:
            self._iter_batches_readahead = iter_batches_readahead
        if iter_fragments_readahead is not None:
            self._iter_fragments_readahead = iter_fragments_readahead
        if iter_use_threads is not None:
            self._iter_use_threads = iter_use_threads
        return self

    async def write_from_generator(self, async_gen: AsyncIterable[_T]) -> None:
        """Читает асинхронный генератор и пишет в файлы порциями."""
        batch = []
        count = 0

        async for item in async_gen:
            self._apply_serialization(item)
            batch.append(item)
            if len(batch) >= self._batch_size:
                self._save_batch(batch)
                count += len(batch)
                batch = []
        if batch:
            self._save_batch(batch)
            count += len(batch)
        logging.info(f"💾 Завершено. Сохранено записей (включая ошибки): {count}")

    def _save_batch(self, data):
        """Запись одного батча в уникальный файл."""
        ts = int(time.time() * 1000)
        uid = uuid.uuid4().hex[:6]
        file_name = self.path / f"batch_{ts}_{uid}.parquet"

        try:
            table = pa.Table.from_pylist(data)

            if self._schema is not None:
                for field_name in set(self._schema.names) - set(table.schema.names):
                    dtype = self._schema.field(field_name).type
                    table = table.append_column(field_name, pa.nulls(table.num_rows, type=dtype))
                table = table.select(self._schema.names).cast(self._schema)

            pq.write_table(table, file_name)
            logging.info(f"✅ Файл записан: {file_name.name} ({len(data)} строк)")

            self._dataset = dataset(self.path, format="parquet", exclude_invalid_files=True, schema=self._schema)
        except Exception as e:
            logging.error(f"❌ Ошибка записи батча в {file_name.name}: {e}", exc_info=e)

    def get_max_value(self, column: str) -> Optional[Any]:
        """
        Returns maximum value in passed column of dataset.
        """
        max_value = None
        for values in self._iter_column(column):
            _max_value = pa.compute.max(values).as_py()  # noqa
            max_value = max_value or _max_value
            max_value = _max_value if _max_value > max_value else max_value
        return max_value

    def get_n_unique_values(self, column: str) -> int:
        """
        Returns num unique values in passed column of dataset.
        """
        unique_values = set()
        for values in self._iter_column(column):
            unique_values.update(pc.unique(values).to_pylist())  # noqa
        return len(unique_values)

    def _iter_column(self, column: str) -> Iterator[Array]:
        if "." in column:
            column, field = tuple(column.split("."))
        else:
            field = None
        for batch in self._dataset.to_batches(
            [column], batch_size=self._batch_size, batch_readahead=0, fragment_readahead=0, use_threads=False  # noqa
        ):
            values = batch.column(column)
            if field:
                values = values.field(field)
            yield values

    def __iter__(self) -> Iterator[_T]:
        """Итератор по всем записям во всех файлах для Трансформера."""
        for batch in self._dataset.to_batches(
            filter=self._read_filter, batch_size=self._batch_size, batch_readahead=self._iter_batches_readahead,  # noqa
            fragment_readahead=self._iter_fragments_readahead, use_threads=self._iter_use_threads  # noqa
        ):
            for row in batch.to_pylist():
                self._apply_deserialization(row)
                yield row
        if self._remove_after_read and self.path.exists():
            shutil.rmtree(self.path)

    def __len__(self):
        """Общее кол-во строк во всех файлах."""
        total = 0
        for file in self.path.glob("*.parquet"):
            try:
                meta = pq.read_metadata(file)
                total += meta.num_rows
            except: continue
        return total

    def write_from_sync_generator(self, sync_gen: Iterable[_T]) -> None:
        """Читает синхронный генератор и пишет в файлы порциями."""
        batch = []
        count = 0
        for item in sync_gen:
            self._apply_serialization(item)
            batch.append(item)
            if len(batch) >= self._batch_size:
                self._save_batch(batch)
                count += len(batch)
                batch = []
        if batch:
            self._save_batch(batch)
            count += len(batch)
        logging.info(f"💾 Трансформация завершена. Сохранено записей: {count}")

    def _apply_serialization(self, record: Dict[str, Any]) -> None:
        for key in self._serialize_fields:
            record[key] = ujson.dumps(record.get(key))

    def _apply_deserialization(self, record: Dict[str, Any]) -> None:
        for key in self._serialize_fields:
            record[key] = ujson.loads(record.get(key) or 'null')


def to_parquet(*parquet_args: Any, **parquet_kwargs: Any) -> Callable[[Callable[..., Iterable[_T]]], Callable[..., ParquetDataset[_T]]]:
    """
    Decorates iterator-function to apply streaming into Parquet-file.
    """
    def _wrapped(func: Callable[..., Iterable[_T]]) -> Callable[..., ParquetDataset[_T]]:
        @functools.wraps(func)
        def __wrapped(*args: Any, **kwargs: Any) -> ParquetDataset[_T]:
            parquet_dataset = ParquetDataset(*parquet_args, **parquet_kwargs)
            parquet_dataset.write_from_sync_generator(func(*args, **kwargs))
            return parquet_dataset
        return __wrapped
    return _wrapped
