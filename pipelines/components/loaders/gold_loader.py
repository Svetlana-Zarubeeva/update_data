from typing import List, Dict, Any, Optional
import json

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import (
    LEGAL_ENTITIES_TABLE,
    ADDRESSES_TABLE,
    CONTACT_INFO_TABLE,
    FINANCE_TABLE,
    MANAGEMENT_TABLE,
    FOUNDERS_TABLE,
    GOLD_FOUNDER_TYPES_TABLE
)


class GoldLoader(Loader):
    """Сохраняет данные в нормализованные таблицы Gold-слоя."""

    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def _get_founder_type_id(self, founder_data):
        """Определяет тип учредителя на основе данных."""
        try:
            if founder_data.get("ogrn"):
                return 2  # Российская организация
            else:
                return 1  # Физическое лицо
        except Exception:
            return 1

    def _initialize_founder_types(self):
        """Инициализирует таблицу типов учредителей, не нарушая целостность данных."""

        required_types = [
            (1, 'ФЛ', 'Физическое лицо'),
            (2, 'РосОрг', 'Российская организация'),
            (3, 'ИнОрг', 'Иностранная организация'),
            (4, 'ПИФ', 'Паевой инвестиционный фонд'),
            (5, 'РФ', 'Субъект РФ')
        ]
        
        for id_val, code, name in required_types:
            self._pg.execute(
                f"""INSERT INTO {GOLD_FOUNDER_TYPES_TABLE} (id, type_code, type_name) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING""",
                id_val, code, name
            )

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

    def _prepare_json_field(self, value):
        if value is None or value == {} or value == []:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return value

    def _process_company(self, item):
        """Обрабатывает одну компанию полностью"""
        try:
            legal_entity = item["legal_entity"]

            # --- Основная сущность ---
            query = f"""
                INSERT INTO {LEGAL_ENTITIES_TABLE} (inn, ogrn, kpp, short_name, full_name, 
                                          registration_date, status, okved_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (inn) DO UPDATE SET
                    ogrn = EXCLUDED.ogrn,
                    kpp = EXCLUDED.kpp,
                    short_name = EXCLUDED.short_name,
                    full_name = EXCLUDED.full_name,
                    registration_date = EXCLUDED.registration_date,
                    status = EXCLUDED.status,
                    okved_id = EXCLUDED.okved_id,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """

            params = (
                self._safe_str(legal_entity["inn"]),
                self._safe_str(legal_entity["ogrn"]),
                self._safe_str(legal_entity["kpp"]),
                self._safe_str(legal_entity["short_name"]),
                self._safe_str(legal_entity["full_name"]),
                legal_entity["registration_date"],
                self._safe_str(legal_entity["status"], "UNKNOWN"),
                self._safe_str(legal_entity["okved_id"])
            )

            result = self._pg.execute(query, *params)
            if result and len(result) > 0:
                legal_entity_id = result[0][0]
            else:
                id_result = self._pg.execute(
                    f"SELECT id FROM {LEGAL_ENTITIES_TABLE} WHERE inn = %s",
                    self._safe_str(legal_entity["inn"])
                )
                if id_result and len(id_result) > 0:
                    legal_entity_id = id_result[0][0]
                else:
                    print(f"⚠️ Could not get ID for INN {legal_entity['inn']}")
                    return False

            # --- Адрес ---
            address = item["address"]
            self._pg.execute(
                f"DELETE FROM {ADDRESSES_TABLE} WHERE legal_entity_id = %s",
                legal_entity_id
            )
            address_query = f"""
                INSERT INTO {ADDRESSES_TABLE} (legal_entity_id, address_full, postal_code, 
                                    region, city, street, house, flat, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            address_params = (
                legal_entity_id,
                self._safe_str(address["address_full"]),
                self._safe_str(address["postal_code"]),
                self._safe_str(address["region"]),
                self._safe_str(address["city"]),
                self._safe_str(address["street"]),
                self._safe_str(address["house"]),
                self._safe_str(address["flat"]),
                self._safe_float(address["latitude"]),
                self._safe_float(address["longitude"])
            )
            self._pg.execute(address_query, *address_params)

            # --- Контактная информация ---
            contact_info = item["contact_info"]
            self._pg.execute(
                f"DELETE FROM {CONTACT_INFO_TABLE} WHERE legal_entity_id = %s",
                legal_entity_id
            )
            contact_query = f"""
                INSERT INTO {CONTACT_INFO_TABLE} (legal_entity_id, phones, emails, websites)
                VALUES (%s, %s, %s, %s)
            """
            contact_params = (
                legal_entity_id,
                self._prepare_json_field(contact_info["phones"]),
                self._prepare_json_field(contact_info["emails"]),
                self._prepare_json_field(contact_info["websites"])
            )
            self._pg.execute(contact_query, *contact_params)

            # --- Финансы ---
            finance = item["finance"]
            self._pg.execute(
                f"DELETE FROM {FINANCE_TABLE} WHERE legal_entity_id = %s",
                legal_entity_id
            )
            finance_query = f"""
                INSERT INTO {FINANCE_TABLE} (legal_entity_id, employee_count, revenue, income, expense, tax_system)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            finance_params = (
                legal_entity_id,
                finance["employee_count"],
                finance["revenue"],
                finance["income"],
                finance["expense"],
                self._safe_str(finance["tax_system"])
            )
            self._pg.execute(finance_query, *finance_params)

            # --- Руководство ---
            management = item["management"]
            self._pg.execute(
                f"DELETE FROM {MANAGEMENT_TABLE} WHERE legal_entity_id = %s",
                legal_entity_id
            )
            if management and (management["name"] or management["post"]):
                management_query = f"""
                    INSERT INTO {MANAGEMENT_TABLE} (legal_entity_id, name, post, start_date)
                    VALUES (%s, %s, %s, %s)
                """
                management_params = (
                    legal_entity_id,
                    self._safe_str(management["name"]),
                    self._safe_str(management["post"]),
                    management["start_date"]
                )
                self._pg.execute(management_query, *management_params)

            # --- Учредители ---
            founders = item["founders"]
            self._pg.execute(
                f"DELETE FROM {FOUNDERS_TABLE} WHERE legal_entity_id = %s",
                legal_entity_id
            )
            for founder in founders:
                founder_type_id = self._get_founder_type_id(founder)
                founder_query = f"""
                    INSERT INTO {FOUNDERS_TABLE} (legal_entity_id, founder_type_id, inn, full_name, 
                                        is_inaccurate, reason)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                founder_params = (
                    legal_entity_id,
                    founder_type_id,
                    self._safe_str(founder["inn"]),
                    self._safe_str(founder["full_name"]),
                    bool(founder["is_inaccurate"]) if founder["is_inaccurate"] is not None else False,
                    self._safe_str(founder["reason"])
                )
                self._pg.execute(founder_query, *founder_params)

            return True

        except Exception as e:
            return False

    def load(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        try:
            with self._pg:
                self._initialize_founder_types()
                
                processed_count = 0
                error_count = 0

                for item in data:
                    success = self._process_company(item)
                    if success:
                        processed_count += 1
                    else:
                        error_count += 1
                        
        except Exception as e:
            raise e