from typing import Any, Dict, Generator
import logging

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.mongo_connector import MongoConnector
from settings import OFDATA_BRONZE_DATABASE, OFDATA_BRONZE_COLLECTION


class SilverExtractor(Extractor):
    """Извлечение данных из MongoDB."""
    
    def __init__(self, mongo_connector: MongoConnector):
        self._mongo = mongo_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        logging.info("🔍 Starting extraction from MongoDB: ofdata_bronze.raw_data")
        
        with self._mongo.with_defaults(
            database=OFDATA_BRONZE_DATABASE,
            collection=OFDATA_BRONZE_COLLECTION
        ) as mongo:
            cursor = mongo.select(
                query={"inn": {"$exists": True}},
                fields=["_id", "data", "inn", "okved", "region", "downloaded_at"]
            )
            
            for doc in cursor:
                yield {
                    "raw_doc": doc,
                    "data": doc.get("data", {}),
                    "inn": doc.get("inn"),
                    "okved": doc.get("okved"),
                    "region": doc.get("region"),
                    "downloaded_at": doc.get("downloaded_at")
                }