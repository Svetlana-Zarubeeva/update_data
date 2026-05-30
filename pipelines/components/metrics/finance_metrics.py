from typing import Any, Dict
import logging
from datetime import datetime

from pipelines.components.metrics.metrics import Metrics
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import FINANCE_TABLE


class FinanceMetrics(Metrics):
    """Сбор и сохранение метрик выполнения пайплайна Finance Gold"""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector
        self._start_time = datetime.utcnow()

    def log_pre_run_metrics(self, extracted_data=None):
        logging.info("📊 Starting Finance Gold pipeline")

    def log_post_run_metrics(self, transformed_data=None):
        self._pg.connect()
        
        # Подсчет записей
        with self._pg.with_defaults(schema="public", table=FINANCE_TABLE):
            result = self._pg.execute(f'SELECT COUNT(*) FROM "{FINANCE_TABLE}"')
            total_records = result[0][0] if result else 0

            result = self._pg.execute(
                f'SELECT COUNT(*) FROM "{FINANCE_TABLE}" WHERE created_at >= %s',
                (self._start_time.isoformat(),)
            )
            new_records = result[0][0] if result else 0

            result = self._pg.execute(
                f'SELECT COUNT(*) FROM "{FINANCE_TABLE}" WHERE updated_at >= %s AND updated_at != created_at',
                (self._start_time.isoformat(),)
            )
            updated_records = result[0][0] if result else 0

        metrics_record = {
            "pipeline_name": "finance_gold",
            "total_records": total_records,
            "new_records": new_records,
            "updated_records": updated_records,
        }

        with self._pg.with_defaults(schema="public", table="pipeline_metrics"):
            self._pg.insert([metrics_record])

        logging.info(
            f"📈 Finance Gold metrics: "
            f"total={total_records}, new={new_records}, updated={updated_records}"
        )