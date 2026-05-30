import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.ofdata_gold_extractor import OfdataGoldExtractor
from pipelines.components.transformers.ofdata_gold_transformer import OfdataGoldTransformer
from pipelines.components.loaders.ofdata_gold_loader import OfdataGoldLoader
from pipelines.components.metrics.ofdata_gold_metrics import OfdataGoldMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн загрузки данных из слоя Silver в слой Gold (витрина данных).

        Цель:
            Формирование финальной витрины данных о юридических лицах для аналитики.
            Данные берутся из нормализованной таблицы Silver, обогащаются кодами ОКВЭД
            и загружаются в таблицу Gold с поддержкой актуальности (upsert).

        Extract: Чтение данных из таблицы silver.silver_ofdata_companies.
                 Выполняется LEFT JOIN с таблицей справочника OKVED IT кодов
                 для получения человеко-читаемого или стандартизированного кода деятельности.
        
        Transform: 
            - Приведение типов данных (строки, даты)
            - Замена NULL значений на дефолтные (например, "UNKNOWN" для статуса)
            - Подготовка плоской структуры для загрузки
        
        Load: 
            - Вставка новых записей или обновление существующих по ключу ИНН (UPSERT)
            - Обновление временных меток (created_at/updated_at)
        
        Metrics: 
            - Подсчет общего количества записей в витрине
            - Подсчет новых добавленных записей
            - Подсчет обновленных записей
            - Сохранение метрик в таблицу public.pipeline_metrics
    """
    
    logging.info("--- Starting legal entities gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = OfdataGoldExtractor(pg_conn)
    transformer = OfdataGoldTransformer()
    loader = OfdataGoldLoader(pg_conn)
    metrics = OfdataGoldMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Legal entities gold pipeline completed successfully ---")