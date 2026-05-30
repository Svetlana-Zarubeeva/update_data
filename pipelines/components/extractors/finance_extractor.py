from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import (
    SILVER_OFDATA_TABLE,
    SILVER_DADATA_TABLE
)


class FinanceExtractor(Extractor):
    """Извлекает финансовую информацию юридических лиц из Silver-слоя."""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает финансовую информацию из таблиц silver_ofdata_companies и silver_dadata_companies.
        """
        self._pg.connect()
        
        query = """
        SELECT 
            o.inn,
            d.employee_count,
            d.revenue,
            d.income,
            d.expense,
            d.tax_system
        FROM silver.silver_ofdata_companies o
        LEFT JOIN silver.silver_dadata_companies d ON o.inn = d.inn
        """
        
        with self._pg.with_defaults(schema="silver", table="silver_ofdata_companies"):
            cursor = self._pg.execute(query)
            
            for row in cursor:
                yield {
                    "inn": row[0],
                    "employee_count": row[1],
                    "revenue": row[2],
                    "income": row[3],
                    "expense": row[4],
                    "tax_system": row[5]
                }