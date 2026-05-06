import logging
from datetime import datetime

from pipelines.components.metrics.metrics import Metrics
from pipelines.components.connectors.mongo_connector import MongoConnector
from settings import DADATA_BRONZE_DATABASE, DADATA_BRONZE_COLLECTION


class DadataBronzeMetrics(Metrics):
    def __init__(self, mongo_connector: MongoConnector):
        self._mongo = mongo_connector
        self._start_time = datetime.utcnow()

    def log_pre_run_metrics(self, extracted_data=None):
        """Вызывается до запуска пайплайна."""
        logging.info("📊 Starting dadata bronze pipeline")

    def log_post_run_metrics(self, transformed_data=None):
        """Вызывается после завершения пайплайна. Считает метрики по итоговым данным в MongoDB."""
        self._mongo.connect()
        
        db = self._mongo.db(DADATA_BRONZE_DATABASE)
        collection = db[DADATA_BRONZE_COLLECTION]
        
        total_all_time = collection.count_documents({})
        
        successful_requests = collection.count_documents({
            "created_at": {"$gte": self._start_time.isoformat()}
        })
        
        total_requested = 0
        if transformed_data is not None:
            total_requested = sum(1 for _ in transformed_data)
        
        failed_requests = total_requested - successful_requests

        message = (
            f"📈 DaData Bronze Metrics: "
            f"requested={total_requested}, "
            f"success={successful_requests}, "
            f"failed={failed_requests}"
        )
        logging.info(message)

        metrics_collection = db["pipeline_metrics"]
        metrics_collection.insert_one({
            "pipeline_name": "dadata_bronze",
            "total_requested": total_requested,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "created_at": datetime.utcnow().isoformat()
        })