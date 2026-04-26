import logging
from pathlib import Path
from typing import ClassVar, Optional, Tuple, Any, Dict, List, Literal

from pyarrow import Schema

from pipelines.components.connectors.adbc_postgres_connector import ADBCPostgresConnector
from pipelines.components.extractors.extractor import Extractor
from pipelines.helpers.parquet_dataset import ParquetDataset


class GenericPostgresToParquetExtractor(Extractor):
    """
    Generic extractor for simple cases. Executes query in PostgresSQL and streams results into local Parquet-file.
    """
    select_query: ClassVar[str] = None
    select_args: ClassVar[Tuple[Any, ...] | Dict[str, Any]] = None
    select_temp_tables: ClassVar[Dict[str, str]] = None
    select_temp_tables_type: ClassVar[Literal["temp", "unlogged"]] = None
    parquet_path: ClassVar[Path] = None
    parquet_schema: ClassVar[Schema] = None
    parquet_serialize_fields: ClassVar[List[str]] = None
    parquet_read_batch_size: ClassVar[int] = None

    def __init__(
        self,
        postgres_connector: ADBCPostgresConnector,
        *,
        select_query: Optional[str] = None,
        select_args: Optional[Tuple[Any, ...] | Dict[str, Any]] = None,
        select_temp_tables: Optional[Dict[str, str]] = None,
        select_temp_tables_type: Optional[Literal["temp", "unlogged"]] = None,
        parquet_path: Optional[Path] = None,
        parquet_schema: Optional[Schema] = None,
        parquet_serialize_fields: Optional[List[str]] = None,
        parquet_read_batch_size: Optional[int] = None,
    ) -> None:
        self._postgres_connector = postgres_connector
        self._select_query = self.__class__.select_query or select_query
        self._select_args = self.__class__.select_args or select_args
        self._select_temp_tables = self.__class__.select_temp_tables or select_temp_tables
        self._select_temp_tables_type = self.__class__.select_temp_tables_type or select_temp_tables_type
        self._parquet_path = self.__class__.parquet_path or parquet_path
        self._parquet_schema = self.__class__.parquet_schema or parquet_schema
        self._parquet_serialize_fields = self.__class__.parquet_serialize_fields or parquet_serialize_fields
        self._parquet_read_batch_size = self.__class__.parquet_read_batch_size or parquet_read_batch_size
        if (self._select_query is None) and (self._parquet_path is None):
            raise ValueError(
                "At least `select_query` and `parquet_path` must be specified in class fields or constructor kwargs."
            )

    def extract(self) -> ParquetDataset:
        with self._postgres_connector as postgres:
            temp_table_type = (self._select_temp_tables_type or "temp").capitalize()

            for name, query in reversed((self._select_temp_tables or {}).items()):
                if postgres.table_exists(name, schema=("pg_temp" if temp_table_type == "temp" else None)):
                    logging.info("%s table `%s` skipped 'cause it's already exists...", temp_table_type, name)
                else:
                    logging.info("%s table `%s` creation started...", temp_table_type, name)
                    postgres.execute(f"CREATE {temp_table_type} TABLE IF NOT EXISTS {name} AS ({query});")
                    logging.info("%s table `%s` successfully created.", temp_table_type, name)

            logging.info("Select query execution started.")
            dataset = postgres.execute_to_parquet(
                self._select_query,
                parquet_path=self._parquet_path,
                parquet_schema=self._parquet_schema,
                parquet_serialize_fields=self._parquet_serialize_fields,
                parquet_read_batch_size=self._parquet_read_batch_size,
                *(self._select_args if isinstance(self._select_args, tuple) else ()),
                **(self._select_args if isinstance(self._select_args, dict) else {}),
            )
            logging.info("Select query successfully executed.")

        return dataset
