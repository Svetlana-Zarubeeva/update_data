import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.checko_silver_extractor import CheckoSilverExtractor
from pipelines.components.transformers.checko_silver_transformer import CheckoSilverTransformer
from pipelines.components.loaders.checko_silver_loader import CheckoSilverLoader
from pipelines.components.metrics.checko_silver_metrics import CheckoSilverMetrics
from pipelines.components.connectors.mongo_connector import MongoConnector
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн преобразования данных из Bronze-слоя Checko в структурированный Silver-слой системы.

        Цель:
            Преобразование сырых JSON-ответов от Checko API, хранящихся в MongoDB Bronze-слоя,
            в нормализованную реляционную структуру Silver-слоя. Это обеспечивает удобство
            для последующей аналитики, поиска и интеграции с другими компонентами системы.

        Extract: 
            - Извлечение всех документов из коллекции checko_bronze.raw_data (MongoDB)
            - Получение только обновлённых или новых записей с момента последнего запуска
            - Подготовка данных для дальнейшей трансформации
        Transform: 
            - Парсинг адреса на составные части (индекс, регион, город, улица, дом, квартира)
            - Извлечение контактной информации (телефоны, email, сайты)
            - Обработка финансовых показателей (численность сотрудников)
            - Нормализация данных о руководстве и учредителях
            - Безопасная обработка null-значений и преобразование дат
        Load: 
            - Сохранение преобразованных данных в таблицу silver_checko_companies (PostgreSQL)
            - Выполнение upsert операций по полю ИНН для обеспечения идемпотентности
            - Обновление существующих записей или создание новых при необходимости
        Metrics: 
            - Подсчёт общего количества, новых и обновлённых записей в Silver-слое
            - Сохранение метрик выполнения в таблицу silver_pipeline_metrics
    """

    logging.info("--- Starting checko silver pipeline ---")

    mongo_conn = MongoConnector()
    pg_conn = PostgresConnector()

    extractor = CheckoSilverExtractor(mongo_conn)
    transformer = CheckoSilverTransformer()
    loader = CheckoSilverLoader(pg_conn)
    metrics = CheckoSilverMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Checko silver pipeline completed successfully ---")