# pipelines/components/extractors/addresses_extractor.py
from typing import Generator, Dict, Any
import re

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_OFDATA_TABLE, SILVER_DADATA_TABLE


class AddressesExtractor(Extractor):
    """Извлекает адреса юридических лиц из Silver-слоя."""

    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def _extract_district(self, address_full: str) -> str:
        """
        Извлекает название района из полного адреса.
        Примеры: "Азовский р-н", "Аксайский район", "г. Ростов-на-Дону, Октябрьский р-н"
        """
        if not address_full:
            return ""

        # Поиск шаблонов вида "XXX р-н" или "XXX район"
        match = re.search(r'([А-Яа-яёЁ\s\-]+)(?:\s+р[\-\s]*н| район)', address_full)
        if match:
            district_name = match.group(1).strip()
            # Убираем "обл", если есть
            if " обл" in district_name:
                district_name = district_name.split(" обл")[-1].strip()
            return district_name + " район"
        return ""

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает адреса из таблиц silver_ofdata_companies и silver_dadata_companies.
        """
        self._pg.connect()

        query = """
        SELECT 
            o.inn,
            COALESCE(d.address_full, o.address) as address_full,
            d.postal_code,
            d.region,
            d.city,
            d.street,
            d.house,
            d.flat,
            d.latitude,
            d.longitude
        FROM silver.silver_ofdata_companies o
        LEFT JOIN silver.silver_dadata_companies d ON o.inn = d.inn
        """

        with self._pg.with_defaults(schema="silver", table="silver_ofdata_companies"):
            cursor = self._pg.execute(query)

            for row in cursor:
                address_full = row[1] or ""
                yield {
                    "inn": row[0],
                    "address_full": address_full,
                    "postal_code": row[2],
                    "region": row[3],
                    "city": row[4],
                    "street": row[5],
                    "house": row[6],
                    "flat": row[7],
                    "latitude": row[8],
                    "longitude": row[9],
                    "district": self._extract_district(address_full)
                }