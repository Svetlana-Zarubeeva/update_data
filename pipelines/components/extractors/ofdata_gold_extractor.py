from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_OFDATA_TABLE


class OfdataGoldExtractor(Extractor):
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        self._pg.connect()
        query = f"""
            SELECT 
                o.inn,
                o.ogrn,
                o.kpp,
                o.short_name,
                o.full_name,
                o.reg_date,
                o.status,
                COALESCE(itc.okved_code, NULL) AS okved_code
            FROM silver.{SILVER_OFDATA_TABLE} o
            LEFT JOIN public.okved_it_codes itc 
                ON o.okved_code = itc.okved_code
        """
        with self._pg.with_defaults(schema="silver", table=SILVER_OFDATA_TABLE):
            cursor = self._pg.execute(query)
            for row in cursor:
                yield {
                    "inn": row[0],
                    "ogrn": row[1],
                    "kpp": row[2],
                    "short_name": row[3],
                    "full_name": row[4],
                    "reg_date": row[5],
                    "status": row[6],
                    "okved_code": row[7]  # уже строка вида "62.01" или NULL
                }