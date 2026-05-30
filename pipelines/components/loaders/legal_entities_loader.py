from typing import List, Dict, Any
import datetime

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import LEGAL_ENTITIES_TABLE


class LegalEntitiesLoader(Loader):
    """Сохраняет данные юридических лиц в таблицу legal_entities Gold-слоя."""

    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def _safe_str(self, value, default=""):
        if value is None:
            return default
        return str(value)

    def _safe_date(self, value):
        if value and isinstance(value, datetime.datetime):
            return value.date()
        return value

    def load(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        try:
            with self._pg:
                processed_count = 0
                for item in data:
                    inn = self._safe_str(item["inn"])
                    ogrn = self._safe_str(item["ogrn"])
                    kpp = self._safe_str(item["kpp"])
                    short_name = self._safe_str(item["short_name"])
                    full_name = self._safe_str(item["full_name"])
                    registration_date = self._safe_date(item["registration_date"])
                    status = self._safe_str(item["status"], "UNKNOWN")
                    okved_code = self._safe_str(item["okved_code"])

                    query = f"""
                        INSERT INTO {LEGAL_ENTITIES_TABLE} 
                        (inn, ogrn, kpp, short_name, full_name, registration_date, status, okved_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (inn) DO UPDATE SET
                            ogrn = EXCLUDED.ogrn,
                            kpp = EXCLUDED.kpp,
                            short_name = EXCLUDED.short_name,
                            full_name = EXCLUDED.full_name,
                            registration_date = EXCLUDED.registration_date,
                            status = EXCLUDED.status,
                            okved_code = EXCLUDED.okved_code,
                            updated_at = CURRENT_TIMESTAMP
                    """
                    self._pg.execute(query, inn, ogrn, kpp, short_name, full_name, registration_date, status, okved_code)
                    processed_count += 1

        except Exception as e:
            raise e