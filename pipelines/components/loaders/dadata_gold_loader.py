from typing import List, Dict, Any

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import DADATA_GOLD_TABLE


class DadataGoldLoader(Loader):
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def load(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        try:
            # Используем контекстный менеджер для установки схемы
            with self._pg.with_defaults(schema="public", table=DADATA_GOLD_TABLE):
                for item in data:
                    query = f"""
                        INSERT INTO {DADATA_GOLD_TABLE} 
                        (inn, ogrn, kpp, short_name, company_name, status, registration_date, okved_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (inn) DO UPDATE SET
                            ogrn = EXCLUDED.ogrn,
                            kpp = EXCLUDED.kpp,
                            short_name = EXCLUDED.short_name,
                            company_name = EXCLUDED.company_name,
                            status = EXCLUDED.status,
                            registration_date = EXCLUDED.registration_date,
                            okved_code = EXCLUDED.okved_code,
                            updated_at = CURRENT_TIMESTAMP
                    """
                    self._pg.execute(query, *item.values())
        except Exception as e:
            raise e