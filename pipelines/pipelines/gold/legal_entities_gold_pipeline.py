import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.legal_entities_extractor import LegalEntitiesExtractor
from pipelines.components.transformers.legal_entities_transformer import LegalEntitiesTransformer
from pipelines.components.loaders.legal_entities_loader import LegalEntitiesLoader
from pipelines.components.metrics.legal_entities_metrics import LegalEntitiesMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн формирования основной витрины юридических лиц (Legal Entities) в слое Gold.

        Цель:
            Объединение данных из временных таблиц Gold-слоя (Ofdata и Dadata) 
            в единую таблицу public.legal_entities.
            Используется FULL OUTER JOIN для сохранения всех уникальных компаний 
            из обоих источников, даже если данные есть только в одном из них.

        Extract: 
            - Чтение данных из gold_temp.ofdata_gold_entities и gold_temp.dadata_gold_entities
            - FULL OUTER JOIN по INN для объединения записей
            - Приоритет данных Ofdata при наличии дубликатов (через COALESCE)
        
        Transform: 
            - Приведение типов данных (строки, даты)
            - Замена NULL значений на дефолтные (например, "UNKNOWN" для статуса)
            - Стандартизация названий полей
        
        Load: 
            - Вставка новых записей или обновление существующих по ключу ИНН (UPSERT)
            - Обновление временной метки updated_at при изменении данных
        
        Metrics: 
            - Подсчет общего количества компаний в витрине
            - Подсчет новых добавленных компаний
            - Подсчет обновленных компаний
            - Сохранение метрик в public.pipeline_metrics
    """

    logging.info("--- Starting legal entities gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = LegalEntitiesExtractor(pg_conn)
    transformer = LegalEntitiesTransformer()
    loader = LegalEntitiesLoader(pg_conn)
    metrics = LegalEntitiesMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Legal entities gold pipeline completed successfully ---")