from typing import Any, Dict, Generator, List
import logging

from pipelines.components.loaders.loader import Loader
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_SCHEMA, SILVER_OFDATA_TABLE


class SilverLoader(Loader):
    """Загрузка преобразованных данных в PostgreSQL"""
    
    def __init__(self, postgres_connector: PostgresConnector):
        self._pg = postgres_connector
        self._loaded_count = 0

    def load(self, data: Generator[Dict[str, Any], None, None]) -> None:
        logging.info(f"💾 Starting load to PostgreSQL: {SILVER_SCHEMA}.{SILVER_OFDATA_TABLE}")

        with self._pg.with_defaults(schema=SILVER_SCHEMA, table=SILVER_OFDATA_TABLE):
            batch = []
            batch_size = 500

            for item in data:
                batch.append(item)
                if len(batch) >= batch_size:
                    self._process_batch(batch)
                    batch = []

            if batch:
                self._process_batch(batch)

        logging.info(f"✅ Loaded {self._loaded_count} records into {SILVER_SCHEMA}.{SILVER_OFDATA_TABLE}")

    def _process_batch(self, batch: List[Dict[str, Any]]) -> None:
        try:
            self._pg.insert(
                data=batch,
                schema=SILVER_SCHEMA,
                table=SILVER_OFDATA_TABLE,
                upsert_on=["inn"],
                upsert_update_columns="*"
            )
            self._loaded_count += len(batch)Загрузка преобразованных данных в PostgreSQL
            logging.info(f"✅ Inserted batch of {len(batch)} records")

        except Exception as e:
            logging.error(f"❌ Error inserting batch: {e}")
            raise