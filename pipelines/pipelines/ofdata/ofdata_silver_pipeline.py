from pipelines.pipeline import Pipeline
from pipelines.components.extractors.ofdata_silver_extractor import SilverExtractor
from pipelines.components.transformers.ofdata_silver_transformer import SilverTransformer
from pipelines.components.loaders.ofdata_silver_loader import SilverLoader
from pipelines.components.metrics.ofdata_silver_metrics import SilverMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector
from pipelines.components.connectors.mongo_connector import MongoConnector


def main():
    """
        Пайплайн загрузки данных из MongoDB (Bronze-слой) в слой Silver (нормализованные сырые данные).

        Цель:
            Извлечение необработанных данных о юридических лицах из MongoDB,
            их первичная нормализация и сохранение в реляционную таблицу PostgreSQL
            для последующей обработки в Gold-слое.

        Extract: Чтение документов из коллекции MongoDB (bronze.ofdata_companies).
        Transform: 
            - Парсинг JSON-полей (директора, учредители)
            - Приведение форматов дат и строк
            - Удаление или замена некорректных значений
            - Формирование плоской структуры под таблицу Silver
        Load: 
            - Вставка/обновление записей в таблицу silver.silver_ofdata_companies
            - Обработка дубликатов через upsert по ИНН
        Metrics: 
            - Подсчёт общего количества, новых и обновлённых записей
            - Сохранение метрик выполнения в таблицу silver_pipeline_metrics
    """
    
    mongo_conn = MongoConnector()
    pg_conn = PostgresConnector()

    extractor = SilverExtractor(mongo_conn)
    transformer = SilverTransformer()
    loader = SilverLoader(pg_conn)
    metrics = SilverMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()