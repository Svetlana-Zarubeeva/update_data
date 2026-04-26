from pathlib import Path
from types import TracebackType
from typing import Optional, Any, Tuple, List, Type, Literal

from adbc_driver_postgresql.dbapi import Connection, Cursor, connect
from pyarrow import Schema
from pyarrow.parquet import ParquetWriter

from pipelines.components.connectors.connector import Connector
from pipelines.helpers.parquet_dataset import ParquetDataset
from settings import DATABASE_TO_CONF, Database


class ADBCPostgresConnector(Connector):
    """
    PostgresSQL connector with Apache ADBC driver connection.
    """
    _config_name: Database
    _connection: Optional[Connection] = None
    _cursor: Optional[Cursor] = None

    def __init__(self, config: Database = "data") -> None:
        super().__init__()
        self._config_name = Database(config)

    def connect(self) -> None:
        if not self._connection:
            uri = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(**DATABASE_TO_CONF[self._config_name])
            self._connection = connect(uri)
        if not self._cursor:
            self._cursor = self._connection.cursor()

    def close(self) -> None:
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(self, query: str, *args: Any, **kwargs: Any) -> Optional[List[Tuple[Any, ...]]]:
        """
        Executes query with passed args, kwargs. Returns data fetched from cursor.
        """
        if args and kwargs:
            raise ValueError("Both *args and **kwargs cannot be passed.")

        self._cursor.execute(query, args or kwargs)
        if self._cursor.description:
            return self._cursor.fetchall()

    def execute_to_parquet(
        self,
        query: str,
        *args: Any,
        parquet_path: Path,
        parquet_filename: str = "data.parquet",
        parquet_schema: Optional[Schema] = None,
        parquet_serialize_fields: Optional[List[str]] = None,
        parquet_read_batch_size: Optional[int] = None,
        **kwargs: Any,
    ) -> ParquetDataset:
        """
        Executes query with passed args, kwargs. Streams data into Parquet-file and returns `ParquetDataset` object.
        """
        if args and kwargs:
            raise ValueError("Both *args and **kwargs cannot be passed.")

        parquet_path = Path(parquet_path)
        parquet_path.mkdir(parents=True, exist_ok=True)

        reader = self._cursor.execute(query, args or kwargs).fetch_record_batch()
        parquet_schema = parquet_schema or reader.schema

        with ParquetWriter(parquet_path / parquet_filename, parquet_schema, use_dictionary=False) as writer:
            for batch in reader:
                writer.write_batch(batch)

        dataset = ParquetDataset(
            parquet_path, parquet_schema, clear_if_exists=False,
            serialize_fields=parquet_serialize_fields, batch_size=parquet_read_batch_size,
        )
        return dataset

    def table_exists(self, table: str, schema: Optional[str | Literal["pg_temp"]] = None) -> bool:
        """
        Checks if given table exists in given schema.

        :param table: Name of table to find.
        :param schema: Name of schema where table must be present.
         If `schema=None` will be used name of default schema.
         If `schema="pg_temp"` will be used name of temp schema.
        """
        if schema is None:
            self._cursor.execute("SELECT current_schema FROM current_schema()")
            schema = (self._cursor.fetchone() or (None,))[0]
            if schema is None:
                return False

        if schema == "pg_temp":
            self._cursor.execute("SELECT nspname FROM pg_namespace WHERE oid = pg_my_temp_schema()")
            schema = (self._cursor.fetchone() or (None,))[0]
            if schema is None:
                return False

        self._cursor.execute(
            "SELECT TRUE FROM pg_tables WHERE schemaname = $1 AND tablename = $2", (schema, table)
        )
        return (self._cursor.fetchone() or (False,))[0]

    def __exit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> Optional[bool]:
        if self._connection is not None:
            if (exc_type is None) and (exc_val is None) and (exc_tb is None):
                self._connection.commit()
            else:
                self._connection.rollback()
        self.close()
