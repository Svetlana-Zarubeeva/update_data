from typing import List, Dict, Any
import psycopg2

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import LEGAL_ENTITIES_TABLE, FINANCE_TABLE, DATABASE_TO_CONF, Database


class FinanceLoader(Loader):
    """Сохраняет финансовую информацию в таблицу finance Gold-слоя."""

    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def _safe_int(self, value):
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value):
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_str(self, value, default=""):
        if value is None:
            return default
        return str(value)

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
                employee_count = self._safe_int(item["employee_count"])
                revenue = self._safe_float(item["revenue"])
                income = self._safe_float(item["income"])
                expense = self._safe_float(item["expense"])
                tax_system = self._safe_str(item["tax_system"])
                
                # Удаляем существующие финансовые данные
                delete_query = f"DELETE FROM {FINANCE_TABLE} WHERE legal_entity_id = %s"
                cursor.execute(delete_query, (legal_entity_id,))
                
                # Вставляем новые финансовые данные
                insert_query = f"""
                    INSERT INTO {FINANCE_TABLE} (legal_entity_id, employee_count, revenue, income, expense, tax_system)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    legal_entity_id, employee_count, revenue, income, expense, tax_system
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