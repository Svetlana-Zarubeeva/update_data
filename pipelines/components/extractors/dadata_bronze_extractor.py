import hashlib
import json
from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from pipelines.components.connectors.mongo_connector import MongoConnector
from pipelines.components.connectors.dadata_connector import DadataConnector
from settings import GOLD_LEGAL_ENTITIES_TABLE, DADATA_BRONZE_DATABASE, DADATA_BRONZE_COLLECTION


class DadataBronzeExtractor(Extractor):
    """Извлекает данные об организациях из Gold-слоя и дополняет их информацией из DaData API."""

    def __init__(
        self,
        pg_connector: PostgresConnector,
        mongo_connector: MongoConnector,
        dadata_connector: DadataConnector
    ):
        self._pg = pg_connector
        self._mongo = mongo_connector
        self._dadata = dadata_connector

    def _get_data_hash(self, data: Dict) -> str:
        """Создаёт хеш от данных для сравнения."""
        clean_data = {k: v for k, v in data.items() if k not in ["hid", "source"]}
        serialized = json.dumps(clean_data, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.md5(serialized.encode('utf-8')).hexdigest()

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает данные организаций из Gold и дополняет их информацией из DaData.
        Возвращает документы для загрузки в Bronze (включая обновления).
        """
        self._dadata.connect()

        self._mongo.connect()

        with self._pg.with_defaults(schema="public", table=GOLD_LEGAL_ENTITIES_TABLE):
            cursor = self._pg.execute(f"SELECT inn, ogrn FROM {GOLD_LEGAL_ENTITIES_TABLE}")
            gold_records = [(row[0] or "", row[1] or "") for row in cursor]

        collection = self._mongo.db(DADATA_BRONZE_DATABASE)[DADATA_BRONZE_COLLECTION]
        bronze_docs = collection.find({}, {"inn": 1, "data_hash": 1})
        bronze_map = {doc["inn"]: doc.get("data_hash") for doc in bronze_docs if doc.get("inn")}

        for inn, ogrn in gold_records:
            if not ogrn or not inn:
                continue

            dadata_record = self._dadata.fetch_by_inn(inn)
            if dadata_record is None:
                continue

            new_hash = self._get_data_hash(dadata_record)

            existing_hash = bronze_map.get(inn)
            if existing_hash != new_hash:
                yield {
                    "inn": inn,
                    "ogrn": ogrn,
                    "data": dadata_record,
                    "data_hash": new_hash
                }