import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.management_extractor import ManagementExtractor
from pipelines.components.transformers.management_transformer import ManagementTransformer
from pipelines.components.loaders.management_loader import ManagementLoader
from pipelines.components.metrics.management_metrics import ManagementMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн загрузки информации о руководстве (Management) в слой Gold.

        Цель:
            Извлечение данных о руководителях юридических лиц из Silver-слоя,
            их нормализация и сохранение в таблицу public.management.
            Данные связываются с основной таблицей legal_entities по ИНН.

        Extract: 
            - Чтение данных из silver.silver_ofdata_companies и silver.silver_dadata_companies
            - LEFT JOIN по INN для получения ФИО, должности и даты начала полномочий
        
        Transform: 
            - Приведение типов данных (строки, даты)
            - Замена NULL значений на пустые строки или дефолтные значения
            - Формирование словаря с ключами: inn, name, post, start_date
        
        Load: 
            - Поиск ID юридического лица в таблице legal_entities по ИНН
            - Удаление старых записей о руководстве для данного юрлица (полная замена)
            - Вставка актуальной записи о руководителе
        
        Metrics: 
            - Подсчет общего количества записей в таблице management
            - Подсчет новых и обновленных записей
            - Сохранение метрик в public.pipeline_metrics
    """

    logging.info("--- Starting management gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = ManagementExtractor(pg_conn)
    transformer = ManagementTransformer()
    loader = ManagementLoader(pg_conn)
    metrics = ManagementMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Management gold pipeline completed successfully ---")