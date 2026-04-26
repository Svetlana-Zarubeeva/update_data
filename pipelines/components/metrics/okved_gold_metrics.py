from typing import Tuple, List, Dict
from datetime import datetime

from pipelines.components.metrics.metrics import Metrics
from pipelines.components.connectors.postgres_connector import PostgresConnector


class OkvedGoldMetrics(Metrics):
    """Логирует метрики выполнения пайплайна."""
    
    def __init__(self, postgres_connector: PostgresConnector):
        self.pg = postgres_connector
        self.pre_metrics = {}

    def log_pre_run_metrics(self, extracted_data: Tuple[List[Dict], bool]) -> None:
        raw_data, _ = extracted_data
        self.pre_metrics["downloaded_count"] = len(raw_data)

    def log_post_run_metrics(self, transformed_data: Tuple[List[Dict], bool]) -> None:
        with self.pg.with_defaults(schema="public", table="okved_it_codes"):
            result = self.pg.execute("SELECT COUNT(*) FROM public.okved_it_codes")
            written_count = result[0][0] if result else 0

        metric_record = {
            "pipeline_name": "okved_gold",
            "downloaded_count": self.pre_metrics.get("downloaded_count", 0),
            "written_count": written_count,
        }

        with self.pg.with_defaults(schema="public", table="okved_pipeline_metrics"):
            self.pg.insert([metric_record])