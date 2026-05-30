from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_DADATA_TABLE


class DadataGoldExtractor(Extractor):
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        self._pg.connect()
        query = f"""
            SELECT 
                d.inn,
                d.ogrn,
                d.kpp,
                d.short_name,
                d.company_name,
                d.status,
                d.registration_date,
                COALESCE(itc.okved_code, NULL) AS okved_code
            FROM silver.{SILVER_DADATA_TABLE} d
            LEFT JOIN public.okved_it_codes itc 
                ON d.okved_main = itc.okved_code
        """
        with self._pg.with_defaults(schema="silver", table=SILVER_DADATA_TABLE):
            cursor = self._pg.execute(query)
            for row in cursor:
                yield {
                    "inn": row[0],
                    "ogrn": row[1],
                    "kpp": row[2],
                    "short_name": row[3],
                    "company_name": row[4],
                    "status": row[5],
                    "registration_date": row[6],
                    "okved_code": row[7]
                }