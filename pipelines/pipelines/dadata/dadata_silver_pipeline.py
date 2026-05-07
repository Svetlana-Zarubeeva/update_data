import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.dadata_silver_extractor import DadataSilverExtractor
from pipelines.components.transformers.dadata_silver_transformer import DadataSilverTransformer
from pipelines.components.loaders.dadata_silver_loader import DadataSilverLoader
from pipelines.components.metrics.dadata_silver_metrics import DadataSilverMetrics
from pipelines.components.connectors.mongo_connector import MongoConnector
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн преобразования данных из Bronze-слоя DaData в структурированный Silver-слой системы.

        Цель:
            Преобразование сырых JSON-ответов от DaData API, хранящихся в MongoDB Bronze-слоя,
            в нормализованную реляционную структуру Silver-слоя. Это обеспечивает удобство
            для последующей аналитики, поиска и интеграции с другими компонентами системы.

        Extract: 
            - Извлечение всех документов из коллекции contact_info_bronze.data (MongoDB)
            - Получение только обновлённых или новых записей с момента последнего запуска
            - Подготовка данных для дальнейшей трансформации
        Transform: 
            - Парсинг адреса на составные части (индекс, регион, город, улица, дом, квартира, координаты)
            - Извлечение контактной информации (телефоны, email, сайты)
            - Обработка финансовых показателей (выручка, доходы, расходы, система налогообложения)
            - Нормализация данных о руководстве и учредителях
            - Безопасная обработка null-значений и преобразование временных меток
        Load: 
            - Сохранение преобразованных данных в таблицу silver_dadata_companies (PostgreSQL)
            - Выполнение upsert операций по полю ИНН для обеспечения идемпотентности
            - Обновление существующих записей или создание новых при необходимости
        Metrics: 
            - Подсчёт общего количества, новых и обновлённых записей в Silver-слое
            - Сохранение метрик выполнения в таблицу silver_pipeline_metrics
    """

    logging.info("--- Starting dadata silver pipeline ---")

    mongo_conn = MongoConnector()
    pg_conn = PostgresConnector()

    extractor = DadataSilverExtractor(mongo_conn)
    transformer = DadataSilverTransformer()
    loader = DadataSilverLoader(pg_conn)
    metrics = DadataSilverMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- DaData silver pipeline completed successfully ---")