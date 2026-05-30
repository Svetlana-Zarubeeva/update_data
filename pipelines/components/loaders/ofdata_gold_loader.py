from typing import List, Dict, Any

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import OFDATA_GOLD_TABLE


class OfdataGoldLoader(Loader):
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def load(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        try:
            with self._pg:
                for item in data:
                    query = f"""
                        INSERT INTO {OFDATA_GOLD_TABLE} 
                        (inn, ogrn, kpp, short_name, full_name, reg_date, status, okved_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (inn) DO UPDATE SET
                            ogrn = EXCLUDED.ogrn,
                            kpp = EXCLUDED.kpp,
                            short_name = EXCLUDED.short_name,
                            full_name = EXCLUDED.full_name,
                            reg_date = EXCLUDED.reg_date,
                            status = EXCLUDED.status,
                            okved_code = EXCLUDED.okved_code,
                            updated_at = CURRENT_TIMESTAMP
                    """
                    self._pg.execute(query, *item.values())
        except Exception as e:
            raise e