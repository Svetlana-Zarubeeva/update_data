import logging

from pipelines.pipeline import Pipeline
from pipelines.runner import Runner
from pipelines.components.connectors.mongo_connector import MongoConnector
from pipelines.components.connectors.postgres_connector import PostgresConnector
from pipelines.components.extractors.checko_bronze_extractor import CheckoBronzeExtractor
from pipelines.components.transformers.checko_bronze_transformer import CheckoBronzeTransformer
from pipelines.components.loaders.checko_bronze_loader import CheckoBronzeLoader
from pipelines.components.metrics.checko_bronze_metrics import CheckoBronzeMetrics


def main():
    """
        Пайплайн загрузки контактных данных из checko.ru в слой Bronze (сырые данные) системы.

        Цель:
            Сбор контактных данных организаций по ИНН из таблицы legal_entities,
            нормализация полученных данных, сохранение в MongoDB и фиксация метрик выполнения.

        Extract: Получение данных из checko.ru по каждому ИНН с использованием API ключей из таблицы.
        Transform: Нормализация и добавление служебных полей.
        Load: Сохранение в MongoDB с upsert'ом по ИНН.
        Metrics: Фиксация результатов выполнения.
    """

    logging.info(f"--- Starting checko bronze pipeline ---")

    mongo_connector = MongoConnector()
    postgres_connector = PostgresConnector()

    metrics = CheckoBronzeMetrics(mongo_connector)

    extractor = CheckoBronzeExtractor(
        postgres_connector=postgres_connector
    )
    transformer = CheckoBronzeTransformer()
    loader = CheckoBronzeLoader(mongo_connector, metrics)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Checko bronze pipeline completed successfully ---")


if __name__ == "__main__":
    main()