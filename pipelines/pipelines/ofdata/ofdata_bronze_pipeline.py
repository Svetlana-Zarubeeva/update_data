import logging

from pipelines.pipeline import Pipeline
from pipelines.runner import Runner
from pipelines.components.connectors.mongo_connector import MongoConnector
from pipelines.components.connectors.ofdata_api_connector import OfdataApiConnector
from pipelines.components.extractors.ofdata_bronze_extractor import OfdataBronzeExtractor
from pipelines.components.transformers.ofdata_bronze_transformer import OfdataBronzeTransformer
from pipelines.components.loaders.ofdata_bronze_loader import OfdataBronzeLoader
from pipelines.components.metrics.ofdata_bronze_metrics import OfdataBronzeMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн загрузки данных из API Ofdata в слой Bronze (сырые данные) системы.

        Цель:
            Сбор актуальных сведений о юридических лицах по заданным IT-связанным ОКВЭДам,
            нормализация полученных данных, сохранение в MongoDB и фиксация метрик выполнения.

        Extract: Получение данных из внешнего API по каждому IT-ОКВЭДу.
        Transform: Нормализация и добавление служебных полей.
        Load: Сохранение в MongoDB с upsert'ом по ИНН.
        Metrics: Фиксация результатов выполнения.
    """

    logging.info(f"--- Starting ofdata bronze pipeline ---")

    mongo_connector = MongoConnector()
    postgres_connector = PostgresConnector()
    ofdata_api_connector = OfdataApiConnector()

    metrics = OfdataBronzeMetrics(mongo_connector)

    extractor = OfdataBronzeExtractor(
        connector_ofdata=ofdata_api_connector,
        postgres_connector=postgres_connector
    )
    transformer = OfdataBronzeTransformer()
    loader = OfdataBronzeLoader(mongo_connector, metrics)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- ofdata bronze pipeline completed successfully ---")