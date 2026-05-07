from typing import Generator, Dict, Any

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_SCHEMA, SILVER_DADATA_TABLE


class DadataSilverLoader(Loader):
    """Сохраняет данные в таблицу Silver-слоя."""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def load(self, data: Generator[Dict[str, Any], None, None]) -> None:
        data_list = list(data)
        if not data_list:
            return
            
        with self._pg.with_defaults(schema=SILVER_SCHEMA, table=SILVER_DADATA_TABLE):
            self._pg.insert(
                data=data_list,
                schema=SILVER_SCHEMA,
                table=SILVER_DADATA_TABLE,
                upsert_on=["inn"],
                upsert_update_columns="*"
            )