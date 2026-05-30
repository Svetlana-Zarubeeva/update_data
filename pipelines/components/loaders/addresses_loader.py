from typing import List, Dict, Any

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import LEGAL_ENTITIES_TABLE, ADDRESSES_TABLE


class AddressesLoader(Loader):
    """Сохраняет адреса юридических лиц в таблицу addresses Gold-слоя."""

    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def _safe_str(self, value, default=""):
        if value is None:
            return default
        return str(value)
    
    def _safe_float(self, value):
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def load(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        with self._pg:
            processed_count = 0
            
            for item in data:
                inn = self._safe_str(item["inn"])
                
                query = f"SELECT id FROM {LEGAL_ENTITIES_TABLE} WHERE inn = %s"
                result = self._pg.execute(query, inn)
                
                if not result:
                    continue
                    
                legal_entity_id = result[0][0]
                address_full = self._safe_str(item["address_full"])
                postal_code = self._safe_str(item["postal_code"])
                region = self._safe_str(item["region"])
                district = self._safe_str(item["district"])  # Новое поле
                city = self._safe_str(item["city"])
                street = self._safe_str(item["street"])
                house = self._safe_str(item["house"])
                flat = self._safe_str(item["flat"])
                latitude = self._safe_float(item["latitude"])
                longitude = self._safe_float(item["longitude"])
                
                delete_query = f"DELETE FROM {ADDRESSES_TABLE} WHERE legal_entity_id = %s"
                self._pg.execute(delete_query, legal_entity_id)
                
                insert_query = f"""
                    INSERT INTO {ADDRESSES_TABLE} (
                        legal_entity_id, address_full, postal_code, region, district,
                        city, street, house, flat, latitude, longitude
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    legal_entity_id, address_full, postal_code, region, district,
                    city, street, house, flat, latitude, longitude
                )
                self._pg.execute(insert_query, *params)
                processed_count += 1