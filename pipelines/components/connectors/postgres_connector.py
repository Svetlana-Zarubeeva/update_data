import random
import time
from functools import lru_cache
from types import TracebackType
from typing import Optional, Type, Tuple, List, Self, Any, Dict, Iterator, Iterable, TypeVar, Mapping, Set, Literal
import asyncio
import psycopg2
from psycopg2 import extras
from psycopg2.extensions import connection, cursor, Column, TRANSACTION_STATUS_INTRANS

from pipelines.components.connectors.connector import Connector
from settings import POSTGRES_BATCH_SIZE, DATABASE_TO_CONF, Database

FK_TYPE = 'f'
_RowT = TypeVar('_RowT', Tuple[Any, ...], Mapping[str, Any])


class PostgresConnector(Connector):
    _config_name: Database
    _connection: Optional[connection] = None
    _cursor: Optional[cursor] = None

    _default_schema: Optional[str] = None
    _default_table: Optional[str] = None

    def __init__(self, config: Database = "data") -> None:
        super().__init__()
        self._config_name = Database(config)

    def connect(self) -> None:
        if not self._connection:
            self._connection = psycopg2.connect(**DATABASE_TO_CONF[self._config_name])
        if not self._cursor:
            self._cursor = self._connection.cursor()

    def close(self) -> None:
        self._default_schema = None
        self._default_table = None

        if self._cursor:
            self._cursor.close()
            self._cursor = None

        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(self, query: str, *args: Any, cast: Type[_RowT] = tuple, **kwargs: Any) -> Optional[List[_RowT]]:
        """
        Executes query with passed args, kwargs. Returns data fetched from cursor.
        """
        if args and kwargs:
            raise ValueError("Both *args and **kwargs cannot be passed.")

        self._cursor.execute(query, args or kwargs)
        if self._cursor.description is not None:
            return self._cast(self._cursor.description, self._cursor.fetchall(), cast)

    def execute_values(
        self,
        query: str,
        *args: List[Any],
        values_batch_size: Optional[int] = POSTGRES_BATCH_SIZE,
        cast: Type[_RowT] = tuple,
        **kwargs: List[Any],
    ) -> Optional[List[_RowT]]:
        """
        Executes query with passed args, kwargs with `psycopg2.extras.execute_values`. Returns data fetched from cursor.
        """
        if args and kwargs:
            raise ValueError("Both *args and **kwargs cannot be passed.")

        if values_batch_size is None and (args or kwargs):
            if args:
                values_batch_size = len(args[0])
            elif kwargs:
                values_batch_size = len(next(iter(kwargs.values())))
        elif values_batch_size is None:
            values_batch_size = 0

        extras.execute_values(self._cursor, query, args or kwargs, fetch=False, page_size=values_batch_size)
        if self._cursor.description is not None:
            return self._cast(self._cursor.description, self._cursor.fetchall(), cast)

    def ss_execute(
            self,
            query: str,
            *args: Any,
            name: Optional[str] = None,
            batch_size: int = POSTGRES_BATCH_SIZE,
            cast: Type[_RowT] = tuple,
            **kwargs: Any,
    ) -> Iterator[_RowT]:
        """
        Executes query with passed args, kwargs, using server-side-cursor. Iterates data fetched from cursor.
        """
        if args and kwargs:
            raise ValueError("Both *args and **kwargs cannot be passed.")
        if name is None:
            name = f"cursor_{time.time()}_{random.random()}"

        def gen() -> Iterator[Tuple[Any, ...]]:
            with self._connection.cursor(name=name) as ss_cursor:
                ss_cursor.itersize = batch_size
                ss_cursor.execute(query, args or kwargs)

                while True:
                    batch = ss_cursor.fetchmany(batch_size)
                    if len(batch) == 0:
                        break
                    yield from self._cast(ss_cursor.description, batch, cast)

        return gen()

    async def execute_async(
            self,
            query: str,
            *args: Any,
            cast: Type[_RowT] = tuple,
            **kwargs: Any,
    ) -> Optional[List[_RowT]]:
        """
        Asynchronous version of execute.
        Runs a synchronous request in the thread.
        """
        if args and kwargs:
            raise ValueError("Both *args and **kwargs cannot be passed.")

        def run_in_thread():
            self._cursor.execute(query, args or kwargs)
            if self._cursor.description is not None:
                return self._cast(self._cursor.description, self._cursor.fetchall(), cast)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_in_thread)

    def create_temp_table_copy(
            self,
            schema: Optional[str] = None,
            table: Optional[str] = None,
            temp_table: Optional[str] = None,
            unlogged: bool = True,
            drop_copy_if_exists: bool = True,
    ) -> str:
        """
        Creates a DDL copy of table in schema without triggers and FKs.
        """
        schema, table = self._infer_defaults(schema, table)
        temp_table = temp_table or f"{table}_tmp"

        if drop_copy_if_exists:
            self.execute(f"DROP TABLE IF EXISTS {schema}.{temp_table};")

        unlogged_str = "UNLOGGED" if unlogged else ""
        self.execute(f"CREATE {unlogged_str} TABLE {schema}.{temp_table}(LIKE {schema}.{table} INCLUDING ALL);")

        return temp_table

    def insert_upsert(
            self,
            data: list,
            schema: str,
            table: str,
            conflict_columns: list,
            update_columns: list,
            page_size: int = 1000
    ):
        """
            Insert with UPSERT logic: INSERT ... ON CONFLICT (...) DO UPDATE SET ...
        """
        columns = list(data[0].keys())
        col_placeholders = ", ".join(f'"{col}"' for col in columns)
        excluded_cols = ", ".join(f'"{col}" = EXCLUDED."{col}"' for col in update_columns)

        conflict_cols_quoted = ", ".join(f'"{col}"' for col in conflict_columns)

        query = f"""
            INSERT INTO "{schema}"."{table}" ({col_placeholders})
            VALUES %s
            ON CONFLICT ({conflict_cols_quoted}) DO UPDATE SET
            {excluded_cols}
        """

        extras.execute_values(self._cursor, query, [tuple(d[col] for col in columns) for d in data], template=None, page_size=page_size)

    def swap_temp_table_copy(
            self,
            schema: Optional[str] = None,
            table: Optional[str] = None,
            temp_table: Optional[str] = None,
            autocommit: bool = True,
    ):
        """
        Drops original table and replaces it with copy. Also moves or copies all objects from original table to copy.

        **Operation will lock both tables. Tables will be unlocked only after commit or rollback (consider using
        `autocommit` param).**
        """
        if self._connection.status != TRANSACTION_STATUS_INTRANS:
            self.execute("BEGIN;")

        schema, table = self._infer_defaults(schema, table)
        temp_table = temp_table or f"{table}_tmp"
        temp_table_persistence = self._get_table_persistence(schema, temp_table)

        original_triggers = self._get_table_triggers(schema, table)
        original_incoming_fk = self._get_incoming_foreign_keys(schema, table)
        outgoing_fk = self._get_outgoing_foreign_keys(schema, table)

        if temp_table_persistence == 'u':
            self.execute(f"ALTER TABLE {schema}.{temp_table} SET LOGGED;")

        self.execute(f"LOCK TABLE {schema}.{table} IN EXCLUSIVE MODE;")
        self.execute(f"LOCK TABLE {schema}.{temp_table} IN EXCLUSIVE MODE;")

        # moves SERIAL sequences from original table to copy
        for column, sequence in self._get_serial_columns(schema, table):
            self.execute(f"ALTER SEQUENCE {sequence} OWNED BY {schema}.{temp_table}.{column};")
            self.execute(f"ALTER TABLE {schema}.{temp_table} ALTER COLUMN {column} SET DEFAULT nextval(%s::regclass);", sequence)
            self.execute(f"SELECT setval(%s, COALESCE((SELECT MAX({column}) FROM {schema}.{temp_table}), 1))", sequence)

        self.execute(f"ALTER TABLE {schema}.{table} RENAME TO {table}_old;")
        self.execute(f"ALTER TABLE {schema}.{temp_table} RENAME TO {table};")

        # drops incoming FKs from original table to DROP without cascade
        for name, ft_table, _ in self._get_incoming_foreign_keys(schema, f"{table}_old"):
            self.execute(f"ALTER TABLE {schema}.{ft_table} DROP CONSTRAINT {name};")

        # copies incoming FKs from original table to copy
        # after renaming, SQL definitions of original table constrains must works with copy correctly
        for name, ft_table, fk in original_incoming_fk:
            self.execute(f"ALTER TABLE {schema}.{ft_table} ADD CONSTRAINT {name} {fk};")

        # creates triggers from original table in copy
        for trigger in original_triggers:
            self.execute(trigger)

        self.execute(f"DROP TABLE {schema}.{table}_old;")

        # copies outgoing FKs from original table to copy
        for name, fk in outgoing_fk:
            self.execute(f"ALTER TABLE {schema}.{table} ADD CONSTRAINT {name} {fk};")

        if autocommit:
            self._connection.commit()

    def commit(self):
        """
        Применение изменений (транзакций)
        """
        self._connection.commit()

    def rollback(self):
        """
        Отмена изменений (транзакций)
        """
        self._connection.rollback()

    def insert(
            self,
            data: Tuple[Any, ...] | Dict[str, Any] | List[Tuple[Any, ...] | Dict[str, Any]],
            schema: Optional[str] = None,
            table: Optional[str] = None,
            insert_columns: Optional[List[str]] = None,
            returning_columns: Optional[List[str]] = None,
            upsert_on: Optional[str | List[str]] = None,
            upsert_update_columns: str | Literal["*"] | List[str] = "*",
            batch_size: Optional[int] = POSTGRES_BATCH_SIZE,
    ) -> Optional[List[Tuple[Any, ...]]]:
        """
        Inserts passed tuples, named tuples or dicts into specified table.

        :param data: data to insert.
        :param schema: schema of table where data will be inserted.
        :param table: table where data will be inserted.
        :param insert_columns: columns where data will be inserted, if None - columns will not be specified in query.
        :param returning_columns: columns that will be returned by `RETURNING` statement, if None  - `RETURNING` will
        not be specified in query.
        :param upsert_on: columns for `ON CONFLICT(...)` statement.
        :param upsert_update_columns: updated columns for `DO UPDATE SET` statement.
        :param batch_size: insertion batch size, if None - all data will be inserted in one batch.
        """
        schema, table = self._infer_defaults(schema, table)
        batch_size = batch_size or len(data)

        if len(data) == 0:
            return None
        if isinstance(data, (tuple, dict)):
            data = [data]
        if not all(isinstance(record, dict) for record in data) and not all(isinstance(record, tuple) for record in data):
            raise ValueError("Data must be tuple, dict, list of tuples or list of dicts.")

        if isinstance(data[0], dict):
            if insert_columns is None:
                insert_columns = list(data[0].keys())
            for i in range(len(data)):
                data[i] = tuple(data[i].get(column) for column in insert_columns)

        # maybe it's named tuple
        if isinstance(data[0], tuple) and hasattr(data[0], "_fields"):
            if insert_columns is None:
                insert_columns = list(data[0]._fields)  # noqa
            for i in range(len(data)):
                data[i] = tuple(data[i])

        if insert_columns is None:
            insert_columns_str = ""
        else:
            insert_columns_str = "(" + ",".join(insert_columns) + ")"

        if returning_columns is None:
            returning_columns_str = ""
        else:
            returning_columns_str = "RETURNING " + ",".join(returning_columns)

        if upsert_on and upsert_update_columns:
            if isinstance(upsert_on, str):
                upsert_on = [upsert_on]
            if isinstance(upsert_update_columns, str):
                if upsert_update_columns == "*":
                    all_columns = self._table_columns(schema, table) if insert_columns is None else insert_columns
                    upsert_update_columns = list(set(all_columns) - set(upsert_on))
                else:
                    upsert_update_columns = [upsert_update_columns]
            data = self._deduplicate_before_upsert(data, insert_columns, upsert_on)

            upsert_columns_str = (
                    f"ON CONFLICT({','.join(upsert_on)}) DO UPDATE SET " +
                    ",".join(f"{column} = EXCLUDED.{column}" for column in upsert_update_columns)
            )
        else:
            upsert_columns_str = ""

        query = f"""
        INSERT INTO
            {schema}.{table}{insert_columns_str}
        VALUES
            %s
        {upsert_columns_str}
        {returning_columns_str};
        """
        return extras.execute_values(self._cursor, query, data, fetch=(returning_columns is not None), page_size=batch_size)

    def insert_stream(
            self,
            data: Iterable[Tuple[Any, ...] | Dict[str, Any]],
            schema: Optional[str] = None,
            table: Optional[str] = None,
            insert_columns: Optional[List[str]] = None,
            returning_columns: Optional[List[str]] = None,
            upsert_on: Optional[str | List[str]] = None,
            upsert_update_columns: str | Literal["*"] | List[str] = "*",
            batch_size: int = POSTGRES_BATCH_SIZE,
    ) -> Optional[List[Tuple[Any, ...]]]:
        """
        Inserts tuples, named tuples or dicts from given stream into specified table.

        :param data: stream with data to insert.
        :param schema: schema of table where data will be inserted.
        :param table: table where data will be inserted.
        :param insert_columns: columns where data will be inserted, if None - columns will not be specified in query.
        :param returning_columns: columns that will be returned by `RETURNING` statement, if None  - `RETURNING` will
        not be specified in query.
        :param upsert_on: columns for `ON CONFLICT(...)` statement.
        :param upsert_update_columns: updated columns for `DO UPDATE SET` statement.
        :param batch_size: insertion batch size.
        """
        results = None

        batch = []
        for row in data:
            if len(batch) >= batch_size:
                result = self.insert(
                    batch, schema, table, insert_columns, returning_columns, upsert_on, upsert_update_columns, None
                )
                if result is not None:
                    if results is None:
                        results = []
                    results.extend(result)
                batch = []
            batch.append(row)

        if len(batch) > 0:
            self.insert(batch, schema, table, insert_columns, returning_columns, upsert_on, upsert_update_columns, None)

        return results

    def with_defaults(self, schema: Optional[str] = None, table: Optional[str] = None) -> Self:
        self._default_schema = schema
        self._default_table = table
        return self

    def _get_serial_columns(self, schema: str, table: str) -> List[Tuple[str, str]]:
        """
        Returns SERIAL columns of table.
        """
        result = self.execute(
            f"""
            SELECT
                column_name,
                pg_get_serial_sequence(%(schema)s || '.' || %(table)s, column_name)
            FROM
                information_schema.columns
            WHERE
                table_schema = %(schema)s AND
                table_name = %(table)s AND
                pg_get_serial_sequence(%(schema)s || '.' || %(table)s, column_name) IS NOT NULL;
            """,
            schema=schema,
            table=table,
        )
        return result # noqa

    def _get_outgoing_foreign_keys(self, schema: str, table: str) -> List[Tuple[str, str]]:
        """
        Returns outgoing FKs (name and SQL definition) which table references to another tables.
        """
        result = self.execute(
            f"""
            SELECT
                conname,
                pg_get_constraintdef(oid)
            FROM
                pg_constraint
            WHERE
                conrelid = (%s || '.' || %s)::regclass::oid AND contype = %s;
            """,
            schema, table, FK_TYPE
        )
        return result # noqa

    def _get_incoming_foreign_keys(self, schema: str, table: str) -> List[Tuple[str, str, str]]:
        """
        Returns incoming FKs (name, owner table name and SQL definition) which another tables reference to table.
        """
        result = self.execute(
            f"""
            SELECT
                pg_constraint.conname,
                pg_class.relname,
                pg_get_constraintdef(pg_constraint.oid)
            FROM
                pg_constraint
            LEFT JOIN
                pg_class
            ON
                pg_constraint.conrelid = pg_class.oid
            WHERE
                confrelid = (%s || '.' || %s)::regclass::oid AND contype = %s;
            """,
            schema, table, FK_TYPE
        )
        return result # noqa

    def _get_table_persistence(self, schema: str, table: str) -> str:
        """
        Returns table persistence: 'u' - UNLOGGED, 't' - TEMPORARY, 'p' - PERSISTENT.
        """
        result = self.execute(
            f"""
            SELECT 
                relpersistence
            FROM 
                pg_class
            WHERE 
                oid = (%s || '.' || %s)::regclass::oid
            LIMIT 1;
            """,
            schema, table
        )
        return result[0][0]

    def _get_table_triggers(self, schema: str, table: str) -> List[str]:
        """
        Returns SQL definitions of not-system table triggers.
        """
        result = self.execute(
            f"""
            SELECT
                pg_get_triggerdef(oid)
            FROM
                pg_trigger
            WHERE
                tgrelid = (%s || '.' || %s)::regclass::oid AND NOT tgisinternal;
            """,
            schema, table
        )
        return [row[0] for row in result]

    def _infer_defaults(self, schema: Optional[str], table: Optional[str]) -> Tuple[str, str]:
        if (schema is None) and (self._default_schema is None):
            raise ValueError("Schema are not specified.")
        if (table is None) and (self._default_table is None):
            raise ValueError("Table are not specified.")
        if table is None:
            table = self._default_table
        if schema is None:
            schema = self._default_schema
        return schema, table

    @lru_cache
    def _table_columns(self, schema: str, table: str) -> List[str]:
        self._cursor.execute(f"SELECT * FROM {schema}.{table} WHERE FALSE;")
        return [col.name for col in (self._cursor.description or [])]

    def _deduplicate_before_upsert(
            self,
            data: List[Tuple[Any, ...]],
            columns: List[str],
            key: List[str],
    ) -> List[Tuple[Any, ...]]:
        col_idx = {c: i for i, c in enumerate(columns)}
        idx = [col_idx[c] for c in key]
        seen = {}
        for row in data:
            key = tuple(row[i] for i in idx)
            seen[key] = row
        return list(seen.values())

    def _cast(self, description: Tuple[Column, ...], rows: List[Tuple[Any, ...]], cast: Type[_RowT]) -> List[_RowT]:
        if cast is tuple:
            return rows
        elif issubclass(cast, tuple):
            return [cast(*row) for row in rows]
        elif issubclass(cast, dict):
            return [cast(**{k.name: v for k, v in zip(description, row)}) for row in rows]
        else:
            raise ValueError(f"Unrecognized cast type - `{cast}`.")

    def __exit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> Optional[bool]:
        if self._connection is not None:
            if (exc_type is None) and (exc_val is None) and (exc_tb is None):
                self._connection.commit()
            else:
                self._connection.rollback()
        self.close()
