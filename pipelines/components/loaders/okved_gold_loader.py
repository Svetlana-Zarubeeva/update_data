from typing import List, Dict, Tuple
from pipelines.components.loaders.loader import Loader

from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import OKVED_IT_CODES_TABLE


class OkvedGoldLoader(Loader):
    """Безопасно обновляет таблицу в PostgreSQL."""
    
    def __init__(self, postgres_connector: PostgresConnector):
        self.pg = postgres_connector

    def load(self, data: Tuple[List[Dict], bool]) -> None:
        transformed_data, success = data
        if not success:
            return

        with self.pg.with_defaults(schema="public", table=OKVED_IT_CODES_TABLE):
            temp_table = self.pg.create_temp_table_copy(
                schema="public",
                table=OKVED_IT_CODES_TABLE,
                temp_table=f"{OKVED_IT_CODES_TABLE}_tmp"
            )
            
            self.pg.insert(
                data=transformed_data,
                schema="public",
                table=temp_table
            )
            
            self.pg.swap_temp_table_copy(
                schema="public",
                table=OKVED_IT_CODES_TABLE,
                temp_table=temp_table
            )