from typing import List, Dict, Any, Optional

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import CONTACT_INFO_TABLE


class ContactGoldLoader(Loader):
    """Сохраняет контактные данные в таблицу contact_info Gold-слоя."""

    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def load(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        try:
            with self._pg:
                processed_count = 0
                
                for item in data:
                    legal_entity_id = item["legal_entity_id"]
                    
                    # Удаляем существующие контактные данные
                    self._pg.execute(
                        f"DELETE FROM {CONTACT_INFO_TABLE} WHERE legal_entity_id = %s",
                        legal_entity_id
                    )
                    
                    # Вставляем новые контактные данные
                    contact_query = f"""
                        INSERT INTO {CONTACT_INFO_TABLE} (legal_entity_id, phones, emails, websites)
                        VALUES (%s, %s, %s, %s)
                    """
                    contact_params = (
                        legal_entity_id,
                        item["phones"],
                        item["emails"],
                        item["websites"]
                    )
                    self._pg.execute(contact_query, *contact_params)
                    processed_count += 1
                                            
        except Exception as e:
            raise e