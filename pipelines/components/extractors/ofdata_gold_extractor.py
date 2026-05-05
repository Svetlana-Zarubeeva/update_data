from typing import Any, Dict, Generator
import logging

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_SCHEMA, SILVER_OFDATA_TABLE


class GoldExtractor(Extractor):
    """Извлекает данные из Silver слоя (таблица silver.silver_ofdata_companies)"""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        logging.info("🔍 Starting extraction from Silver layer: silver.silver_ofdata_companies")
        
        table_name = f'"{SILVER_SCHEMA}"."{SILVER_OFDATA_TABLE}"'
        
        with self._pg.with_defaults(schema=SILVER_SCHEMA, table=SILVER_OFDATA_TABLE):
            cursor = self._pg.execute(f"SELECT * FROM {table_name}")
            
            for row in cursor:
                yield {
                    "inn": row[0],
                    "ogrn": row[1],
                    "kpp": row[2],
                    "short_name": row[3],
                    "full_name": row[4],
                    "reg_date": row[5],
                    "status": row[6],
                    "region_code": row[7],
                    "address": row[8],
                    "okved_code": row[9],
                    "okved_description": row[10],
                    "directors": row[11],
                    "founders": row[12],
                    "created_at": row[13],
                    "updated_at": row[14]
                }