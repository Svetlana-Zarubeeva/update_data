from typing import List, Dict, Any
import psycopg2
import datetime

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import LEGAL_ENTITIES_TABLE, MANAGEMENT_TABLE, DATABASE_TO_CONF, Database


class ManagementLoader(Loader):
    """Сохраняет информацию о руководстве в таблицу management Gold-слоя."""

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

        # Создаем прямое соединение с PostgreSQL
        connection = psycopg2.connect(**DATABASE_TO_CONF[Database("data")])
        cursor = connection.cursor()
        
        try:
            processed_count = 0
            
            for item in data:
                inn = self._safe_str(item["inn"])
                
                # Получаем ID для каждого INN по отдельности
                query = f"SELECT id FROM {LEGAL_ENTITIES_TABLE} WHERE inn = %s"
                cursor.execute(query, (inn,))
                result = cursor.fetchone()
                
                if not result:
                    continue
                    
                legal_entity_id = result[0]
                name = self._safe_str(item["name"])
                post = self._safe_str(item["post"])
                start_date = self._safe_date(item["start_date"])
                
                # Удаляем существующие записи о руководстве
                delete_query = f"DELETE FROM {MANAGEMENT_TABLE} WHERE legal_entity_id = %s"
                cursor.execute(delete_query, (legal_entity_id,))
                
                # Вставляем новую запись о руководстве
                insert_query = f"""
                    INSERT INTO {MANAGEMENT_TABLE} (legal_entity_id, name, post, start_date)
                    VALUES (%s, %s, %s, %s)
                """
                params = (
                    legal_entity_id, name, post, start_date
                )
                cursor.execute(insert_query, params)
                processed_count += 1
                
            connection.commit()
                    
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()