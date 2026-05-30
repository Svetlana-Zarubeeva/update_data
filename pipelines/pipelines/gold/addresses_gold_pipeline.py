import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.addresses_extractor import AddressesExtractor
from pipelines.components.transformers.addresses_transformer import AddressesTransformer
from pipelines.components.loaders.addresses_loader import AddressesLoader
from pipelines.components.metrics.addresses_metrics import AddressesMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн загрузки адресной информации (Addresses) в слой Gold.

        Цель:
            Извлечение, нормализация и сохранение адресов юридических лиц 
            из Silver-слоя в таблицу public.addresses.
            Данные связываются с основной таблицей legal_entities по ИНН.
            Особое внимание уделяется очистке строковых представлений адресов 
            и выделению района из полного адреса.

        Extract: 
            - Чтение данных из silver.silver_ofdata_companies и silver.silver_dadata_companies
            - LEFT JOIN по INN для получения детализированного адреса из Dadata
            - Парсинг полного адреса для выделения названия района (если оно не указано явно)
        
        Transform: 
            - Нормализация полного адреса: приведение к нижнему регистру, замена сокращений 
              (ул., д., кв.) на полные слова, удаление дубликатов и лишних пробелов
            - Приведение типов данных (float для координат, string для текстовых полей)
            - Стандартизация структуры записи
        
        Load: 
            - Поиск ID юридического лица в таблице legal_entities по ИНН
            - Удаление старых адресных записей для данного юрлица (полная замена актуальными данными)
            - Вставка нового адреса с геокоординатами
        
        Metrics: 
            - Подсчет общего количества адресов в системе
            - Подсчет новых и обновленных записей
            - Сохранение метрик в public.pipeline_metrics
    """

    logging.info("--- Starting addresses gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = AddressesExtractor(pg_conn)
    transformer = AddressesTransformer()
    loader = AddressesLoader(pg_conn)
    metrics = AddressesMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Addresses gold pipeline completed successfully ---")