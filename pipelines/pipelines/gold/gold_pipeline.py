import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.gold_extractor import GoldExtractor
from pipelines.components.transformers.gold_transformer import GoldTransformer
from pipelines.components.loaders.gold_loader import GoldLoader
from pipelines.components.metrics.gold_metrics import GoldMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн объединения и нормализации данных из Silver-слоя в Gold-слой системы.

        Цель:
            Объединить данные о юридических лицах, полученные из двух источников (OFData и DaData),
            преобразовать их в единую нормализованную структуру и загрузить в реляционные таблицы Gold-слоя.
            Обеспечить целостность данных, устранить дублирование и предоставить удобную схему для аналитики.

        Extract: Извлечение объединённых записей из таблиц silver_ofdata_companies и silver_dadata_companies
                 с помощью LEFT JOIN по ИНН.
        Transform: Нормализация данных — приоритизация полей DaData над OFData, обработка учредителей
                   в разных форматах, извлечение руководства, определение актуального ОКВЭД.
        Load: Загрузка структурированных данных в нормализованные таблицы Gold-слоя:
              legal_entities, addresses, contact_info, finance, management, founders.
        Metrics: Сбор и сохранение метрик выполнения — количество записей в каждой таблице,
                 число новых и обновлённых записей.
    """

    logging.info("--- Starting gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = GoldExtractor(pg_conn)
    transformer = GoldTransformer()
    loader = GoldLoader(pg_conn)
    metrics = GoldMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Gold pipeline completed successfully ---")