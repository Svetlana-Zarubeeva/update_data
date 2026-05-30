import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.dadata_gold_extractor import DadataGoldExtractor
from pipelines.components.transformers.dadata_gold_transformer import DadataGoldTransformer
from pipelines.components.loaders.dadata_gold_loader import DadataGoldLoader
from pipelines.components.metrics.dadata_gold_metrics import DadataGoldMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн загрузки данных из источника Dadata в промежуточный слой Gold (Dadata Gold).

        Цель:
            Извлечение сырых данных о юридических лицах, полученных от сервиса Dadata,
            их первичная нормализация и сохранение в таблицу public.dadata_gold_entities.
            Эти данные впоследствии будут объединены с данными Ofdata в основной витрине Legal Entities.

        Extract: 
            - Чтение данных из таблицы silver.silver_dadata_companies
            - LEFT JOIN с таблицей справочника OKVED IT кодов (public.okved_it_codes)
              для стандартизации кода основного вида деятельности
        
        Transform: 
            - Приведение типов данных (строки, даты)
            - Замена NULL значений на дефолтные (например, "UNKNOWN" для статуса)
            - Переименование полей под стандарт витрины (например, okved_main -> okved_code)
        
        Load: 
            - Вставка новых записей или обновление существующих по ключу ИНН (UPSERT)
            - Обновление временной метки updated_at при изменении данных
        
        Metrics: 
            - Подсчет общего количества записей в таблице dadata_gold_entities
            - Подсчет новых добавленных записей
            - Подсчет обновленных записей
            - Сохранение метрик в public.pipeline_metrics
    """
    
    logging.info("--- Starting dadata gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = DadataGoldExtractor(pg_conn)
    transformer = DadataGoldTransformer()
    loader = DadataGoldLoader(pg_conn)
    metrics = DadataGoldMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Dadata gold pipeline completed successfully ---")