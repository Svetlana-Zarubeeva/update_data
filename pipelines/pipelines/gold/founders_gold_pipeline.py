import logging

from pipelines.pipeline import Pipeline
from pipelines.components.extractors.founders_extractor import FoundersExtractor
from pipelines.components.transformers.founders_transformer import FoundersTransformer
from pipelines.components.loaders.founders_loader import FoundersLoader
from pipelines.components.metrics.founders_metrics import FoundersMetrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


def main():
    """
        Пайплайн загрузки информации об учредителях (Founders) в слой Gold.

        Цель:
            Извлечение данных об учредителях из Silver-слоя, их классификация 
            (физические/юридические лица) и сохранение в таблицу public.founders.
            Данные связываются с основной таблицей legal_entities по ИНН компании.

        Extract: 
            - Чтение JSON-поля founders из silver.silver_ofdata_companies
            - Парсинг вложенной структуры для разделения на физических лиц (ФЛ) 
              и российские организации (РФ)
            - Извлечение ключевых атрибутов: ИНН, ФИО/Наименование, ОГРН, КПП
        
        Transform: 
            - Определение типа учредителя (founder_type_id) на основе наличия ОГРН
            - Приведение типов данных и обработка NULL значений
            - Формирование плоской структуры записи
        
        Load: 
            - Инициализация справочника типов учредителей (public.gold_founder_types)
            - Поиск ID юридического лица в таблице legal_entities по ИНН
            - Вставка записи об учредителе с привязкой к legal_entity_id
        
        Metrics: 
            - Подсчет общего количества учредителей в системе
            - Подсчет новых добавленных записей
            - Сохранение метрик в public.pipeline_metrics
    """

    logging.info("--- Starting founders gold pipeline ---")

    pg_conn = PostgresConnector()

    extractor = FoundersExtractor(pg_conn)
    transformer = FoundersTransformer()
    loader = FoundersLoader(pg_conn)
    metrics = FoundersMetrics(pg_conn)

    pipeline = Pipeline(extractor, transformer, loader, metrics)
    pipeline.run()

    logging.info("--- Founders gold pipeline completed successfully ---")