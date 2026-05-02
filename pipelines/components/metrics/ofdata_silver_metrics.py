from typing import Any, Dict
import logging
from datetime import datetime

from pipelines.components.metrics.metrics import Metrics
from settings import SILVER_SCHEMA, SILVER_OFDATA_TABLE


class SilverMetrics(Metrics):
    """Сбор и сохранение метрик выполнения пайплайна"""
    
    def __init__(self, pg_connector):
        self._pg = pg_connector
        self._start_time = datetime.utcnow()

    def log_pre_run_metrics(self, extracted_data=None):
        logging.info("📊 Starting Silver pipeline")

    def log_post_run_metrics(self, transformed_data=None):
        self._pg.connect()
        
        companies_table = f'"{SILVER_SCHEMA}"."{SILVER_OFDATA_TABLE}"'

        with self._pg.with_defaults(schema=SILVER_SCHEMA, table=SILVER_OFDATA_TABLE):
            result = self._pg.execute(f"SELECT COUNT(*) FROM {companies_table}")
            total = result[0][0] if result else 0
            
            result = self._pg.execute(
                f"SELECT COUNT(*) FROM {companies_table} WHERE created_at >= %s",
                (self._start_time.isoformat(),)
            )
            created = result[0][0] if result else 0
            
            result = self._pg.execute(
                f"SELECT COUNT(*) FROM {companies_table} WHERE updated_at >= %s AND updated_at != created_at",
                (self._start_time.isoformat(),)
            )
            updated = result[0][0] if result else 0

        metrics_record = {
            "pipeline_name": "ofdata_silver",
            "total_records": total,
            "new_records": created,
            "updated_records": updated,
        }

        with self._pg.with_defaults(schema=SILVER_SCHEMA, table="silver_pipeline_metrics"):
            self._pg.insert([metrics_record])

        logging.info(f"📈 Silver metrics: total={total}, new={created}, updated={updated}")