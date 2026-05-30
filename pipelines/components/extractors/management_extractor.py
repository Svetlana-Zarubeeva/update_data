from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import (
    SILVER_OFDATA_TABLE,
    SILVER_DADATA_TABLE
)


class ManagementExtractor(Extractor):
    """Извлекает информацию о руководстве юридических лиц из Silver-слоя."""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает информацию о руководстве из таблиц silver_ofdata_companies и silver_dadata_companies.
        """
        self._pg.connect()
        
        query = """
        SELECT 
            o.inn,
            d.management_name,
            d.management_post,
            d.management_start_date
        FROM silver.silver_ofdata_companies o
        LEFT JOIN silver.silver_dadata_companies d ON o.inn = d.inn
        """
        
        with self._pg.with_defaults(schema="silver", table="silver_ofdata_companies"):
            cursor = self._pg.execute(query)
            
            for row in cursor:
                yield {
                    "inn": row[0],
                    "name": row[1],
                    "post": row[2],
                    "start_date": row[3]
                }