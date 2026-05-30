import json
from typing import Generator, Dict, Any

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_SCHEMA, SILVER_CHECKO_TABLE


class CheckoSilverLoader(Loader):
    """Сохраняет данные в таблицу Silver-слоя Checko."""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def _prepare_json_field(self, value):
        """Преобразует значение в JSON-строку для полей JSONB."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return value

    def load(self, data: Generator[Dict[str, Any], None, None]) -> None:
        data_list = list(data)
        if not data_list:
            return
            
        # Подготовка данных для JSONB полей
        prepared_data = []
        for record in data_list:
            prepared_record = {}
            for key, value in record.items():
                if key in ['phones', 'emails', 'websites', 'okveds']:
                    prepared_record[key] = self._prepare_json_field(value)
                else:
                    prepared_record[key] = value
            prepared_data.append(prepared_record)
            
        with self._pg.with_defaults(schema=SILVER_SCHEMA, table=SILVER_CHECKO_TABLE):
            self._pg.insert(
                data=prepared_data,
                schema=SILVER_SCHEMA,
                table=SILVER_CHECKO_TABLE,
                upsert_on=["inn"],
                upsert_update_columns="*"
            )