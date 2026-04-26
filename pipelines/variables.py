import json
from typing import Any, Optional, Tuple, ClassVar
from psycopg2 import connect
from psycopg2.extensions import connection
from settings import VARIABLES_TABLE_NAME, DATABASE_TO_CONF, Database


class Variables:
    _connection: ClassVar[connection] = None

    def __class_getitem__(cls, key: str) -> Any:
        value = cls._select(key)
        if value is None or (len(value) == 0):
            raise KeyError(key)
        return json.loads(value[0])

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        value = cls._select(key)
        if value is None or (len(value) == 0):
            return default
        return value[0]

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        with cls._get_connection().cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {VARIABLES_TABLE_NAME}(key, value) VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """,
                (key, json.dumps(value)),
            )

    @classmethod
    def _select(cls, key: str) -> Optional[Tuple[Any]]:
        with cls._get_connection().cursor() as cursor:
            cursor.execute(f"SELECT value FROM {VARIABLES_TABLE_NAME} WHERE key=%s LIMIT 1;", (key,))
            result = cursor.fetchone()
            return result

    @classmethod
    def _get_connection(cls) -> connection:
        if cls._connection is None:
            conn = connect(**DATABASE_TO_CONF[Database.data])
            conn.set_session(autocommit=True)
            cls._connection = conn
        return cls._connection
