import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.contact_gold_extractor import ContactGoldExtractor
from pipelines.components.transformers.contact_gold_transformer import ContactGoldTransformer
from pipelines.components.loaders.contact_gold_loader import ContactGoldLoader
from pipelines.components.metrics.contact_gold_metrics import ContactGoldMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн обработки контактных данных из Silver-слоя в Gold-слой системы.

        Цель:
            Извлечь контактные данные (телефоны, email, сайты) из таблицы silver_checko_companies,
            связать их с соответствующими юридическими лицами в Gold-слое и сохранить в таблицу contact_info.

        Extract: Извлечение контактных данных из таблицы silver_checko_companies в PostgreSQL.
        Transform: Нормализация и преобразование контактных данных в единый формат JSONB.
        Load: Сохранение контактной информации в таблицу contact_info Gold-слоя с привязкой к legal_entity_id.
        Metrics: Сбор и сохранение метрик выполнения — количество контактных записей.
    """

    logging.info("--- Starting contact gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = ContactGoldExtractor(pg_conn)
    transformer = ContactGoldTransformer()
    loader = ContactGoldLoader(pg_conn)
    metrics = ContactGoldMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Contact gold pipeline completed successfully ---")