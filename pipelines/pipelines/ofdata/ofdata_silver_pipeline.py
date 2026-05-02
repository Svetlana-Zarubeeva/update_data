from pipelines.pipeline import Pipeline
from pipelines.components.extractors.ofdata_silver_extractor import SilverExtractor
from pipelines.components.transformers.ofdata_silver_transformer import SilverTransformer
from pipelines.components.loaders.ofdata_silver_loader import SilverLoader
from pipelines.components.metrics.ofdata_silver_metrics import SilverMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector
from pipelines.components.connectors.mongo_connector import MongoConnector


def main():
    mongo_conn = MongoConnector()
    pg_conn = PostgresConnector()

    extractor = SilverExtractor(mongo_conn)
    transformer = SilverTransformer()
    loader = SilverLoader(pg_conn)
    metrics = SilverMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()