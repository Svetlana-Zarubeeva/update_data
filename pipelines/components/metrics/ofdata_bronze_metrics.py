from typing import Any, Dict
import logging
from datetime import datetime
from pymongo import MongoClient

from pipelines.components.metrics.metrics import Metrics
from settings import OFDATA_BRONZE_DATABASE, OFDATA_BRONZE_COLLECTION


class OfdataBronzeMetrics(Metrics):
    """Сбор и запись метрик выполнения пайплайна."""

    def __init__(self, mongo_connector: MongoClient):
        self._mongo_connector = mongo_connector
        self._loaded_count = 0
        self._start_time = datetime.utcnow()

    def set_loaded_count(self, count: int) -> None:
        self._loaded_count = count

    def log_pre_run_metrics(self, extracted_data=None) -> None:
        logging.info(f"📊 Starting ofdata bronze pipeline")

    def log_post_run_metrics(self, transformed_data=None) -> None:
        end_time = datetime.utcnow()
        
        with self._mongo_connector.with_defaults(
            database=OFDATA_BRONZE_DATABASE,
            collection=OFDATA_BRONZE_COLLECTION
        ) as mongo:
            total_records = mongo.count()
            created_records = mongo.count({"created_at": {"$gte": self._start_time.isoformat()}})
            updated_records = mongo.count({"updated_at": {"$gte": self._start_time.isoformat()}})

        metrics_doc = {
            "loaded_records": self._loaded_count,
            "total_records_in_db": total_records,
            "created_records": created_records,
            "updated_records": updated_records,
        }

        with self._mongo_connector.with_defaults(
            database=OFDATA_BRONZE_DATABASE,
            collection="pipeline_metrics"
        ) as mongo:
            mongo.insert([metrics_doc])

        logging.info(f"📈 Pipeline metrics recorded: loaded={self._loaded_count}, created={created_records}, updated={updated_records}")
        logging.info(f"✅ Total records in DB: {total_records}")