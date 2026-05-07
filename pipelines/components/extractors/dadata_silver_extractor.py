from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.mongo_connector import MongoConnector
from settings import DADATA_BRONZE_DATABASE, DADATA_BRONZE_COLLECTION


class DadataSilverExtractor(Extractor):
    """Извлекает данные из Bronze-слоя DaData для обработки в Silver-слое."""
    
    def __init__(self, mongo_connector: MongoConnector):
        self._mongo = mongo_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает все документы из коллекции contact_info_bronze.data.
        """
        self._mongo.connect()
        
        collection = self._mongo.db(DADATA_BRONZE_DATABASE)[DADATA_BRONZE_COLLECTION]
        cursor = collection.find({})
        
        for doc in cursor:
            yield {
                "inn": doc.get("inn"),
                "ogrn": doc.get("ogrn"),
                "data": doc.get("data", {}),
                "created_at": doc.get("created_at")
            }