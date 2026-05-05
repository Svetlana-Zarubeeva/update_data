from pipelines.pipeline import Pipeline
from pipelines.components.extractors.ofdata_gold_extractor import GoldExtractor
from pipelines.components.transformers.ofdata_gold_transformer import GoldTransformer
from pipelines.components.loaders.ofdata_gold_loader import GoldLoader
from pipelines.components.metrics.ofdata_gold_metrics import GoldMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн загрузки данных из слоя Silver в слой Gold (нормализованные данные) системы.

        Цель:
            Преобразование сырых данных о юридических лицах из Silver-слоя в нормализованную,
            реляционную структуру Gold-слоя, обеспечивающую ссылочную целостность и удобство
            для аналитики и поиска.

        Extract: Извлечение всех записей из таблицы silver.silver_ofdata_companies (PostgreSQL).
        Transform: 
            - Парсинг адреса на составные части (индекс, регион, город, улица, дом)
            - Нормализация директоров и учредителей в отдельные списки
            - Формирование структуры под целевые таблицы Gold-слоя
        Load: 
            - Вставка нормализованных данных в связанные таблицы:
                ofdata_legal_entities, ofdata_addresses, ofdata_directors, ofdata_founders
            - Обеспечение целостности через внешние ключи (legal_entity_id)
            - Обработка данных пакетами для эффективности
        Metrics: 
            - Подсчёт общего количества, новых и обновлённых записей в Gold-слое
            - Сохранение метрик выполнения в таблицу pipeline_metrics
    """
    
    pg_conn = PostgresConnector()

    extractor = GoldExtractor(pg_conn)
    transformer = GoldTransformer()
    loader = GoldLoader(pg_conn)
    metrics = GoldMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()