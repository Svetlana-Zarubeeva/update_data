from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.mongo_connector import MongoConnector
from settings import CHECKO_BRONZE_DATABASE, CHECKO_BRONZE_COLLECTION


class CheckoSilverExtractor(Extractor):
    """Извлекает данные из Bronze-слоя Checko для обработки в Silver-слое."""
    
    def __init__(self, mongo_connector: MongoConnector):
        self._mongo = mongo_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает все документы из коллекции checko_bronze.raw_data.
        """
        self._mongo.connect()
        
        collection = self._mongo.db(CHECKO_BRONZE_DATABASE)[CHECKO_BRONZE_COLLECTION]
        cursor = collection.find({})
        
        for doc in cursor:
            # Извлекаем реальный ИНН из data.data.ИНН
            real_inn = None
            
            # Основной путь: doc["data"]["data"]["ИНН"]
            try:
                real_inn = doc["data"]["data"]["ИНН"]
            except (KeyError, TypeError):
                # Если основной путь не сработал, пробуем альтернативные
                try:
                    # Альтернатива 1: doc["data"]["ИНН"]
                    real_inn = doc["data"]["ИНН"]
                except (KeyError, TypeError):
                    # Альтернатива 2: doc["ИНН"]
                    real_inn = doc.get("ИНН")
            
            # Валидация и очистка ИНН
            if isinstance(real_inn, str):
                # Удаляем все нецифровые символы
                cleaned_inn = ''.join(filter(str.isdigit, real_inn))
                # Проверяем длину (10 или 12 цифр для юрлиц)
                if len(cleaned_inn) in [10, 12]:
                    real_inn = cleaned_inn
                else:
                    real_inn = None
            else:
                real_inn = None
            
            yield {
                "inn": real_inn,
                "ogrn": doc.get("ogrn"),
                "data": doc.get("data", {}),
                "created_at": doc.get("created_at")
            }