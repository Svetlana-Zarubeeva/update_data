from typing import Any, Dict, Generator
import logging
from pymongo.errors import OperationFailure
from pymongo import UpdateOne

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.mongo_connector import MongoConnector
from settings import CHECKO_BRONZE_DATABASE, CHECKO_BRONZE_COLLECTION


class CheckoBronzeLoader(Loader):
    """Загружает данные в коллекцию MongoDB (checko_bronze.raw_data)."""

    def __init__(self, mongo_connector: MongoConnector, metrics):
        self._mongo_connector = mongo_connector
        self._metrics = metrics
        self._loaded_count = 0

    def load(self, data: Generator[Dict[str, Any], None, None]) -> None:
        logging.info(f"💾 Starting data load to MongoDB collection: {CHECKO_BRONZE_COLLECTION}")
        batch = []
        batch_size = 500

        with self._mongo_connector.with_defaults(
            database=CHECKO_BRONZE_DATABASE,
            collection=CHECKO_BRONZE_COLLECTION
        ) as mongo:
            # Создаем индекс по ИНН для ускорения поиска
            mongo.create_index_if_not_exists("inn", unique=False)

            for item in data:
                batch.append(item)
                if len(batch) >= batch_size:
                    self._process_batch(mongo, batch)
                    batch = []

            if batch:
                self._process_batch(mongo, batch)

        self._metrics.set_loaded_count(self._loaded_count)
        logging.info("✅ Data load completed successfully")

    def _process_batch(self, mongo: MongoConnector, batch: list) -> None:
        try:
            operations = []
            
            for document in batch:
                inn = document.get("inn")
                if inn:
                    operations.append(
                        UpdateOne(
                            {"inn": inn},
                            {"$set": document},
                            upsert=True
                        )
                    )
                else:
                    mongo.insert([document], ordered=False)
                    self._loaded_count += 1
            
            if operations:
                result = mongo._client[mongo._default_database][mongo._default_collection].bulk_write(operations, ordered=False)
                self._loaded_count += result.upserted_count + result.modified_count
                    
            logging.info(f"✅ Processed batch of {len(batch)} records")
            
        except OperationFailure as e:
            if "BSONObjectTooLarge" in str(e):
                logging.warning("⚠️ Document too large, processing individually...")
                for item in batch:
                    try:
                        inn = item.get("inn")
                        if inn:
                            mongo.insert([item], upsert_key=["inn"], ordered=False)
                        else:
                            mongo.insert([item], ordered=False)
                        self._loaded_count += 1
                    except Exception as ie:
                        logging.error(f"❌ Error inserting single doc: {ie}")
            else:
                logging.error(f"❌ Error inserting batch: {e}")