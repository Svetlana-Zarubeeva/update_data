from typing import Generator, Dict, Any, Optional

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_SCHEMA, SILVER_CHECKO_TABLE


class ContactGoldExtractor(Extractor):
    """Извлекает контактные данные из Silver-слоя Checko для обработки в Gold-слое."""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает контактные данные из таблицы silver_checko_companies и связывает с legal_entities.
        """
        # Получаем все компании из legal_entities
        self._pg.connect()
        legal_entities_query = "SELECT id, inn FROM legal_entities"
        legal_entities_map = {}
        with self._pg.with_defaults(schema="public", table="legal_entities"):
            cursor = self._pg.execute(legal_entities_query)
            for row in cursor:
                # Убедитесь, что INN в правильном формате
                inn_clean = str(row[1]).strip() if row[1] else None
                if inn_clean:
                    legal_entities_map[inn_clean] = row[0]
                
        # Получаем контактные данные из silver_checko_companies
        with self._pg.with_defaults(schema=SILVER_SCHEMA, table=SILVER_CHECKO_TABLE):
            query = f"""
                SELECT 
                    inn,
                    phones,
                    emails, 
                    websites
                FROM {SILVER_SCHEMA}.{SILVER_CHECKO_TABLE}
                WHERE phones IS NOT NULL 
                   OR emails IS NOT NULL 
                   OR websites IS NOT NULL
            """
            cursor = self._pg.execute(query)
            
            processed_count = 0
            for row in cursor:
                inn = row[0]
                if not inn:
                    continue
                    
                inn_str = str(inn).strip()
                if inn_str not in legal_entities_map:
                    continue
                
                legal_entity_id = legal_entities_map[inn_str]
                phones = row[1]
                emails = row[2]
                websites = row[3]
                
                # Проверяем, есть ли хотя бы одна контактная информация
                if phones is None and emails is None and websites is None:
                    continue
                
                processed_count += 1
                yield {
                    "legal_entity_id": legal_entity_id,
                    "inn": inn_str,
                    "phones": phones,
                    "emails": emails,
                    "websites": websites
                }