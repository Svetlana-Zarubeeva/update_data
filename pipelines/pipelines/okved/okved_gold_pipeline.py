from pipelines.pipeline import Pipeline
from pipelines.components.connectors.okved_connector import OkvedConnector
from pipelines.components.extractors.okved_gold_extractor import OkvedGoldExtractor
from pipelines.components.transformers.okved_gold_transformer import OkvedGoldTransformer
from pipelines.components.loaders.okved_gold_loader import OkvedGoldLoader
from pipelines.components.metrics.okved_gold_metrics import OkvedGoldMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector

def main() -> Pipeline:
    """Автоматизированное обновление справочника IT-кодов ОКВЭД/ОКПД2 (разделы 62 и 63) из официальных источников."""
    
    connector = OkvedConnector()
    pg_connector = PostgresConnector()

    extractor = OkvedGoldExtractor(connector)
    transformer = OkvedGoldTransformer()
    loader = OkvedGoldLoader(pg_connector)
    metrics = OkvedGoldMetrics(pg_connector)
    
    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()