from typing import Any, Dict
import logging
from datetime import datetime

from pipelines.components.metrics.metrics import Metrics
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import CONTACT_INFO_TABLE


class ContactGoldMetrics(Metrics):
    """Сбор и сохранение метрик выполнения пайплайна Contact Gold"""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector
        self._start_time = datetime.utcnow()

    def log_pre_run_metrics(self, extracted_data=None):
        logging.info("📊 Starting Contact Gold pipeline")

    def log_post_run_metrics(self, transformed_data=None):
        self._pg.connect()
        
        # Подсчет контактных записей
        with self._pg.with_defaults(schema="public", table=CONTACT_INFO_TABLE):
            result = self._pg.execute(f'SELECT COUNT(*) FROM "{CONTACT_INFO_TABLE}"')
            total_records = result[0][0] if result else 0

            result = self._pg.execute(
                f'SELECT COUNT(*) FROM "{CONTACT_INFO_TABLE}" WHERE created_at >= %s',
                (self._start_time.isoformat(),)
            )
            new_records = result[0][0] if result else 0

            result = self._pg.execute(
                f'SELECT COUNT(*) FROM "{CONTACT_INFO_TABLE}" WHERE updated_at >= %s AND updated_at != created_at',
                (self._start_time.isoformat(),)
            )
            updated_records = result[0][0] if result else 0

        # Используем только поля, которые существуют в таблице pipeline_metrics
        metrics_record = {
            "pipeline_name": "contact_gold",
            "total_records": total_records,
            "new_records": new_records,
            "updated_records": updated_records,
        }

        with self._pg.with_defaults(schema="public", table="pipeline_metrics"):
            self._pg.insert([metrics_record])

        logging.info(
            f"📈 Contact Gold metrics: "
            f"total={total_records}, new={new_records}, updated={updated_records}"
        )