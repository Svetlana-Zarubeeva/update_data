from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import OFDATA_GOLD_TABLE, DADATA_GOLD_TABLE


class LegalEntitiesExtractor(Extractor):
    """Извлекает основные данные юридических лиц из промежуточных Gold-таблиц."""

    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает данные о юридических лицах из таблиц gold_temp.ofdata_gold_entities и gold_temp.dadata_gold_entities.
        """
        self._pg.connect()

        query = f"""
        SELECT 
            COALESCE(o.inn, d.inn) as inn,
            COALESCE(o.ogrn, d.ogrn) as ogrn,
            COALESCE(o.kpp, d.kpp) as kpp,
            COALESCE(o.short_name, d.short_name) as short_name,
            COALESCE(o.full_name, d.company_name) as full_name,
            COALESCE(o.reg_date, d.registration_date::date) as registration_date,
            COALESCE(o.status, d.status) as status,
            COALESCE(o.okved_code, d.okved_code) as okved_code
        FROM {OFDATA_GOLD_TABLE} o
        FULL OUTER JOIN {DADATA_GOLD_TABLE} d ON o.inn = d.inn
        WHERE o.inn IS NOT NULL OR d.inn IS NOT NULL
        """

        # Указываем схему для выполнения запроса
        with self._pg.with_defaults(schema="gold_temp", table=OFDATA_GOLD_TABLE):
            cursor = self._pg.execute(query)

            for row in cursor:
                yield {
                    "inn": row[0],
                    "ogrn": row[1],
                    "kpp": row[2],
                    "short_name": row[3],
                    "full_name": row[4],
                    "registration_date": row[5],
                    "status": row[6],
                    "okved_code": row[7]
                }