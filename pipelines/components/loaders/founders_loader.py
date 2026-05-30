from typing import List, Dict, Any
import psycopg2

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import LEGAL_ENTITIES_TABLE, FOUNDERS_TABLE, GOLD_FOUNDER_TYPES_TABLE, DATABASE_TO_CONF, Database


class FoundersLoader(Loader):
    """Сохраняет информацию об учредителях в таблицу founders Gold-слоя."""

    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def _safe_str(self, value, default=""):
        if value is None:
            return default
        return str(value)

    def _initialize_founder_types(self, cursor):
        """Инициализирует таблицу типов учредителей."""
        required_types = [
            (1, 'ФЛ', 'Физическое лицо'),
            (2, 'РосОрг', 'Российская организация'),
            (3, 'ИнОрг', 'Иностранная организация'),
            (4, 'ПИФ', 'Паевой инвестиционный фонд'),
            (5, 'РФ', 'Субъект РФ')
        ]
        
        for id_val, code, name in required_types:
            cursor.execute(
                f"""INSERT INTO {GOLD_FOUNDER_TYPES_TABLE} (id, type_code, type_name) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING""",
                (id_val, code, name)
            )

    def load(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        # Создаем прямое соединение с PostgreSQL
        connection = psycopg2.connect(**DATABASE_TO_CONF[Database("data")])
        cursor = connection.cursor()
        
        try:
            self._initialize_founder_types(cursor)
                
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
                inn_founder = self._safe_str(item["inn_founder"])
                full_name = self._safe_str(item["full_name"])
                ogrn = self._safe_str(item["ogrn"])
                kpp = self._safe_str(item["kpp"])
                is_inaccurate = item["is_inaccurate"]
                reason = self._safe_str(item["reason"])
                founder_type_id = item["founder_type_id"]
                
                # Вставляем информацию об учредителе
                query = f"""
                    INSERT INTO {FOUNDERS_TABLE} (legal_entity_id, founder_type_id, inn, full_name, 
                                        is_inaccurate, reason)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    legal_entity_id, founder_type_id, inn_founder, full_name, is_inaccurate, reason
                )
                cursor.execute(query, params)
                processed_count += 1
                
            connection.commit()
                    
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()