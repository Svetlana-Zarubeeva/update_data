from typing import Any, Dict
import logging
from datetime import datetime

from pipelines.components.metrics.metrics import Metrics
from settings import CHECKO_BRONZE_DATABASE, CHECKO_BRONZE_COLLECTION


class CheckoBronzeMetrics(Metrics):
    """Сбор и запись метрик выполнения пайплайна checko.ru."""

    def __init__(self, mongo_connector):
        self._mongo_connector = mongo_connector
        self._loaded_count = 0
        self._start_time = datetime.utcnow()

    def set_loaded_count(self, count: int) -> None:
        self._loaded_count = count

    def log_pre_run_metrics(self, extracted_data=None) -> None:
        logging.info(f"📊 Starting checko bronze pipeline")

    def log_post_run_metrics(self, transformed_data=None) -> None:
        end_time = datetime.utcnow()
        
        with self._mongo_connector.with_defaults(
            database=CHECKO_BRONZE_DATABASE,
            collection=CHECKO_BRONZE_COLLECTION
        ) as mongo:
            total_records = mongo.count()
            created_records = mongo.count({"created_at": {"$gte": self._start_time.isoformat()}})
            updated_records = mongo.count({"updated_at": {"$gte": self._start_time.isoformat()}})
            found_records = mongo.count({"data.status": "found"})
            not_found_records = mongo.count({"data.status": "not_found"})

        metrics_doc = {
            "pipeline_name": "checko_bronze",
            "loaded_records": self._loaded_count,
            "total_records_in_db": total_records,
            "created_records": created_records,
            "updated_records": updated_records,
            "found_records": found_records,
            "not_found_records": not_found_records,
            "execution_time_seconds": (end_time - self._start_time).total_seconds(),
            "timestamp": datetime.utcnow().isoformat()
        }

        with self._mongo_connector.with_defaults(
            database=CHECKO_BRONZE_DATABASE,
            collection="pipeline_metrics"
        ) as mongo:
            mongo.insert([metrics_doc])

        logging.info(f"📈 Pipeline metrics recorded: loaded={self._loaded_count}, found={found_records}, not_found={not_found_records}")
        logging.info(f"✅ Total records in DB: {total_records}")