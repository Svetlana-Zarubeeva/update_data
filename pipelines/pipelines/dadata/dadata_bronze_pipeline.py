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