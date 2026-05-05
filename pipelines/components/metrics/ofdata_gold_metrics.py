from typing import Any, Dict
import logging
from datetime import datetime

from pipelines.components.metrics.metrics import Metrics
from settings import GOLD_LEGAL_ENTITIES_TABLE


class GoldMetrics(Metrics):
    """Считает и сохраняет метрики выполнения пайплайна"""
    
    def __init__(self, pg_connector):
        self._pg = pg_connector
        self._start_time = datetime.utcnow()

    def log_pre_run_metrics(self, extracted_data=None):
        logging.info("📊 Starting Gold pipeline")

    def log_post_run_metrics(self, transformed_data=None):
        self._pg.connect()
        
        with self._pg.with_defaults(schema="public", table=GOLD_LEGAL_ENTITIES_TABLE):
            total = self._pg.execute("SELECT COUNT(*) FROM ofdata_legal_entities")[0][0]
            new = self._pg.execute(
                "SELECT COUNT(*) FROM ofdata_legal_entities WHERE created_at >= %s",
                (self._start_time.isoformat(),)
            )[0][0]
            updated = self._pg.execute(
                "SELECT COUNT(*) FROM ofdata_legal_entities WHERE updated_at >= %s AND updated_at != created_at",
                (self._start_time.isoformat(),)
            )[0][0]

        metrics_record = {
            "pipeline_name": "ofdata_gold",
            "total_records": total,
            "new_records": new,
            "updated_records": updated,
        }

        with self._pg.with_defaults(schema="public", table="pipeline_metrics"):
            self._pg.insert([metrics_record])

        logging.info(f"📈 Gold metrics: total={total}, new={new}, updated={updated}")