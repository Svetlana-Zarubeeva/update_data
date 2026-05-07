import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.dadata_bronze_extractor import DadataBronzeExtractor
from pipelines.components.transformers.dadata_bronze_transformer import DadataBronzeTransformer
from pipelines.components.loaders.dadata_bronze_loader import DadataBronzeLoader
from pipelines.components.metrics.dadata_bronze_metrics import DadataBronzeMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector
from pipelines.components.connectors.mongo_connector import MongoConnector
from pipelines.components.connectors.dadata_connector import DadataConnector


def main():
    """
        Пайплайн загрузки контактной и расширенной информации об организациях из DaData API в Bronze-слой системы.

        Цель:
            Обогащение данных о юридических лицах, уже присутствующих в Gold-слое, актуальной информацией
            из внешнего источника — DaData API. Это включает контактные данные (email, телефон, сайт),
            географические координаты, финансовые показатели, данные об учредителях и руководителях,
            а также другую информацию из ЕГРЮЛ, недоступную в исходных данных.

        Extract: 
            - Получение списка всех организаций из таблицы ofdata_legal_entities (PostgreSQL)
            - Фильтрация организаций, которые ещё не обработаны или имеют устаревшие данные
            - Запрос полной информации по каждой организации через DaData API по ИНН
        Transform: 
            - Добавление служебного поля `created_at` для отслеживания времени загрузки
            - Подготовка данных к сохранению в формате, пригодном для MongoDB
        Load: 
            - Сохранение полных JSON-ответов от DaData API в коллекцию contact_info_bronze.data (MongoDB)
            - Использование хеширования для последующего определения изменений при повторных запусках
        Metrics: 
            - Подсчёт количества запрошенных, успешно загруженных и неудачных запросов
            - Сохранение метрик выполнения в коллекцию contact_info_bronze.pipeline_metrics
    """

    logging.info("--- Starting dadata bronze pipeline ---")

    pg_conn = PostgresConnector()
    mongo_conn = MongoConnector()
    dadata_conn = DadataConnector()

    extractor = DadataBronzeExtractor(pg_conn, mongo_conn, dadata_conn)
    transformer = DadataBronzeTransformer()
    loader = DadataBronzeLoader(mongo_conn)
    metrics = DadataBronzeMetrics(mongo_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- DaData bronze pipeline completed successfully ---")