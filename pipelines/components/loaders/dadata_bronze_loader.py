from typing import Generator, Dict, Any

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.mongo_connector import MongoConnector
from settings import DADATA_BRONZE_DATABASE, DADATA_BRONZE_COLLECTION


class DadataBronzeLoader(Loader):
    """Сохраняет данные в MongoDB Bronze-слоя."""
    
    def __init__(self, mongo_connector: MongoConnector):
        self._mongo = mongo_connector

    def load(self, data: Generator[Dict[str, Any], None, None]) -> None:
        data_list = list(data)
        if not data_list:
            return

        self._mongo.connect()
            
        bronze_db = self._mongo.db(DADATA_BRONZE_DATABASE)
        collection = bronze_db[DADATA_BRONZE_COLLECTION]

        collection.insert_many(data_list)