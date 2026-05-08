from typing import Any, Dict
import logging
from datetime import datetime

from pipelines.components.metrics.metrics import Metrics
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import LEGAL_ENTITIES_TABLE, ADDRESSES_TABLE, CONTACT_INFO_TABLE, FINANCE_TABLE, MANAGEMENT_TABLE, FOUNDERS_TABLE


class GoldMetrics(Metrics):
    """Сбор и сохранение метрик выполнения пайплайна Gold"""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector
        self._start_time = datetime.utcnow()

    def log_pre_run_metrics(self, extracted_data=None):
        logging.info("📊 Starting Gold pipeline")

    def log_post_run_metrics(self, transformed_data=None):
        self._pg.connect()
        
        # Таблицы Gold-слоя
        tables = {
            "legal_entities": LEGAL_ENTITIES_TABLE,
            "addresses": ADDRESSES_TABLE,
            "contact_info": CONTACT_INFO_TABLE,
            "finance": FINANCE_TABLE,
            "management": MANAGEMENT_TABLE,
            "founders": FOUNDERS_TABLE,
        }

        counts = {}
        for key, table_name in tables.items():
            with self._pg.with_defaults(schema="public", table=table_name):
                result = self._pg.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                counts[f"{key}_count"] = result[0][0] if result else 0

        with self._pg.with_defaults(schema="public", table=LEGAL_ENTITIES_TABLE):
            result = self._pg.execute(
                f'SELECT COUNT(*) FROM "{LEGAL_ENTITIES_TABLE}" WHERE created_at >= %s',
                (self._start_time.isoformat(),)
            )
            new_records = result[0][0] if result else 0

            result = self._pg.execute(
                f'SELECT COUNT(*) FROM "{LEGAL_ENTITIES_TABLE}" WHERE updated_at >= %s AND updated_at != created_at',
                (self._start_time.isoformat(),)
            )
            updated_records = result[0][0] if result else 0

        metrics_record = {
            "pipeline_name": "gold",
            "total_records": counts["legal_entities_count"],
            "new_records": new_records,
            "updated_records": updated_records,
            "legal_entities_count": counts["legal_entities_count"],
            "addresses_count": counts["addresses_count"],
            "contact_info_count": counts["contact_info_count"],
            "finance_count": counts["finance_count"],
            "management_count": counts["management_count"],
            "founders_count": counts["founders_count"],
        }

        with self._pg.with_defaults(schema="public", table="pipeline_metrics"):
            self._pg.insert([metrics_record])

        logging.info(
            f"📈 Gold metrics: "
            f"legal_entities={counts['legal_entities_count']}, "
            f"addresses={counts['addresses_count']}, "
            f"contact_info={counts['contact_info_count']}, "
            f"finance={counts['finance_count']}, "
            f"management={counts['management_count']}, "
            f"founders={counts['founders_count']}"
        )