from typing import Any, Dict, Generator, List, Tuple
import logging

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import founder_type_records


class GoldLoader(Loader):
    """Загружает нормализованные данные в таблицы Gold слоя батчами по 500 записей"""
    
    def __init__(self, postgres_connector: PostgresConnector):
        self._pg = postgres_connector
        self._loaded_count = 0

    def load(self, data: Generator[Dict[str, Any], None, None]) -> None:
        logging.info("💾 Starting load to Gold layer")

        batch = {"addresses": [], "legal_entities": [], "directors": [], "founders": []}
        batch_size = 500

        for item in data:
            batch["addresses"].append(item["address"])
            batch["legal_entities"].append(item["legal_entity"])
            batch["directors"].extend(item["directors"])
            batch["founders"].extend(item["founders"])

            if len(batch["legal_entities"]) >= batch_size:
                self._process_batch(batch)
                batch = {"addresses": [], "legal_entities": [], "directors": [], "founders": []}

        if batch["legal_entities"]:
            self._process_batch(batch)

        logging.info(f"✅ Loaded {self._loaded_count} legal entities into Gold layer")

    def _get_legal_entity_ids_by_inn(self, inns: List[str]) -> Dict[str, int]:
        """Получает id юрлиц по списку ИНН."""
        if not inns:
            return {}
        placeholders = ','.join(['%s'] * len(inns))
        query = f"SELECT inn, id FROM public.ofdata_legal_entities WHERE inn IN ({placeholders})"
        self._pg._cursor.execute(query, tuple(inns))
        return {row[0]: row[1] for row in self._pg._cursor.fetchall()}

    def _process_batch(self, batch: Dict[str, List[Dict[str, Any]]]) -> None:
        self._pg.connect()
        
        try:
            # Загрузка справочника типов учредителей
            self._pg.insert(
                data=founder_type_records,
                schema="public",
                table="ofdata_founder_types",
                upsert_on=["type_code"],
                upsert_update_columns=["type_name"]
            )

            # Подготовка данных юрлиц и сбор ИНН
            legal_entity_records = []
            inns = []
            for entity in batch["legal_entities"]:
                clean_entity = {k: v for k, v in entity.items() if k != 'address_id'}
                legal_entity_records.append(clean_entity)
                inns.append(entity["inn"])

            # Вставка юридических лиц
            self._pg.insert(
                data=legal_entity_records,
                schema="public",
                table="ofdata_legal_entities",
                upsert_on=["inn"],
                upsert_update_columns="*"
            )

            # Получение id юрлиц по их ИНН
            inn_to_id_map = self._get_legal_entity_ids_by_inn(inns)

            # Подготовка данных адресов с legal_entity_id
            address_records = []
            for i, addr in enumerate(batch["addresses"]):
                legal_entity_inn = batch["legal_entities"][i]["inn"]
                legal_entity_id = inn_to_id_map.get(legal_entity_inn)
                if legal_entity_id is None:
                    logging.warning(f"⚠️  Legal entity with INN {legal_entity_inn} not found after insert")
                    continue
                addr_record = {
                    "legal_entity_id": legal_entity_id,
                    "index": addr["index"],
                    "region": addr["region"],
                    "city": addr["city"],
                    "street": addr["street"],
                    "house": addr["house"],
                    "full_address": addr["full_address"]
                }
                address_records.append(addr_record)

            # Вставка адресов
            if address_records:
                self._pg.insert(
                    data=address_records,
                    schema="public",
                    table="ofdata_addresses"
                )

            # Подготовка и вставка директоров
            director_records = []
            for director in batch["directors"]:
                legal_entity_inn = director.get("legal_entity_inn")
                if not legal_entity_inn:
                    logging.warning(f"⚠️ Director record missing legal_entity_inn: {director}")
                    continue
                legal_entity_id = inn_to_id_map.get(legal_entity_inn)
                if legal_entity_id is None:
                    logging.warning(f"⚠️ Legal entity ID not found for INN {legal_entity_inn} in director data")
                    continue
                director_record = {
                    "legal_entity_id": legal_entity_id,
                    "inn": director.get("inn"),
                    "full_name": director["full_name"],
                    "position": director["position"],
                    "is_disqualified": director.get("is_disqualified", False),
                    "is_inaccurate": director.get("is_inaccurate", False),
                    "reason": director.get("reason")
                }
                director_records.append(director_record)

            if director_records:
                self._pg.insert(
                    data=director_records,
                    schema="public",
                    table="ofdata_directors"
                )

            # Подготовка и вставка учредителей
            founder_records = []
            self._pg._cursor.execute("SELECT type_code, id FROM public.ofdata_founder_types")
            founder_type_map = {row[0]: row[1] for row in self._pg._cursor.fetchall()}

            for founder in batch["founders"]:
                legal_entity_inn = founder.get("legal_entity_inn")
                if not legal_entity_inn:
                    logging.warning(f"⚠️ Founder record missing legal_entity_inn: {founder}")
                    continue
                legal_entity_id = inn_to_id_map.get(legal_entity_inn)
                if legal_entity_id is None:
                    logging.warning(f"⚠️ Legal entity ID not found for INN {legal_entity_inn} in founder data")
                    continue

                founder_type_code = founder.get("founder_type_code")
                founder_type_id = founder_type_map.get(founder_type_code)
                if founder_type_id is None:
                    logging.warning(f"⚠️ Founder type code '{founder_type_code}' not found in ofdata_founder_types")
                    continue

                founder_record = {
                    "legal_entity_id": legal_entity_id,
                    "founder_type_id": founder_type_id,
                    "inn": founder.get("inn"),
                    "full_name": founder["full_name"],
                    "ogrn": founder.get("ogrn"),
                    "kpp": founder.get("kpp"),
                    "is_inaccurate": founder.get("is_inaccurate", False),
                    "reason": founder.get("reason")
                }
                founder_records.append(founder_record)

            if founder_records:
                self._pg.insert(
                    data=founder_records,
                    schema="public",
                    table="ofdata_founders"
                )

            self._loaded_count += len(legal_entity_records)
            logging.info(f"✅ Inserted batch of {len(legal_entity_records)} legal entities")

        except Exception as e:
            logging.error(f"❌ Error inserting batch: {e}")
            raise