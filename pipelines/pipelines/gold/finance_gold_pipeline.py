import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.finance_extractor import FinanceExtractor
from pipelines.components.transformers.finance_transformer import FinanceTransformer
from pipelines.components.loaders.finance_loader import FinanceLoader
from pipelines.components.metrics.finance_metrics import FinanceMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн загрузки финансовой отчетности (Finance) в слой Gold.

        Цель:
            Извлечение финансовых показателей и данных о численности сотрудников 
            из Silver-слоя, их нормализация и сохранение в таблицу public.finance.
            Данные связываются с основной таблицей legal_entities по ИНН.

        Extract: 
            - Чтение данных из silver.silver_ofdata_companies и silver.silver_dadata_companies
            - LEFT JOIN по INN для получения финансовых метрик (выручка, доходы, расходы) 
              и системы налогообложения из источника Dadata
        
        Transform: 
            - Приведение типов данных (целые числа для штата, float для денег)
            - Обработка некорректных числовых значений (замена на NULL)
            - Стандартизация строковых полей
        
        Load: 
            - Поиск ID юридического лица в таблице legal_entities по ИНН
            - Удаление старых финансовых записей для данного юрлица (полная замена актуальными данными)
            - Вставка новых финансовых показателей
        
        Metrics: 
            - Подсчет общего количества финансовых записей
            - Подсчет новых и обновленных записей
            - Сохранение метрик в public.pipeline_metrics
    """

    logging.info("--- Starting finance gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = FinanceExtractor(pg_conn)
    transformer = FinanceTransformer()
    loader = FinanceLoader(pg_conn)
    metrics = FinanceMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Finance gold pipeline completed successfully ---")