import asyncio
import logging
import time
from typing import Any, Dict, AsyncGenerator

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.ofdata_api_connector import OfdataApiConnector
from settings import OFDATA_REGION


class OfdataBronzeExtractor(Extractor):
    """Извлекает данные из API по списку актуальных ОКВЭД-кодов, связанных с IT-сферой."""

    def __init__(
        self,
        connector_ofdata: OfdataApiConnector,
        postgres_connector
    ):
        self._connector_ofdata = connector_ofdata
        self._region = OFDATA_REGION
        self._postgres_connector = postgres_connector

    def _fetch_okved_codes(self) -> list[str]:
        query = "SELECT DISTINCT okved_code FROM okved_it_codes WHERE okved_code IS NOT NULL;"
        self._postgres_connector.connect()
        with self._postgres_connector._connection.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]

    async def _extract_async(self) -> AsyncGenerator[Dict[str, Any], None]:
        okved_codes = self._fetch_okved_codes()
        logging.info(f"🔍 Starting data extraction for OKVED codes: {okved_codes}")
        logging.info(f"📍 Region filter: {self._region}")

        async with self._connector_ofdata as connector:
            for okved in okved_codes:
                logging.info(f"🔄 Processing OKVED code: {okved}")
                companies_data, is_error = await connector.search_companies(
                    okved=okved, region=self._region, page=1
                )
                if is_error or not isinstance(companies_data, dict):
                    logging.error(f"❌ Invalid response format for OKVED {okved}: {type(companies_data)}")
                    continue

                data_block = companies_data.get("data", {})
                if not isinstance(data_block, dict):
                    logging.warning(f"⚠️ 'data' is not a dict for OKVED {okved}")
                    continue

                total_count = data_block.get("ЗапВсего", 0)
                records = data_block.get("Записи", [])

                if not isinstance(records, list):
                    logging.warning(f"⚠️ 'Записи' is not a list for OKVED {okved}")
                    records = []

                logging.info(f"📊 Total companies found for OKVED {okved}: {total_count}")

                for company in records:
                    yield {
                        "data": company,
                        "metadata": {
                            "okved": okved,
                            "region": self._region,
                            "downloaded_at": time.time()
                        }
                    }

                page = 2
                while (page - 1) * connector.PAGE_SIZE < total_count:
                    logging.info(f"➡️ Fetching page {page} for OKVED {okved}...")
                    next_data, is_error = await connector.search_companies(
                        okved=okved, region=self._region, page=page
                    )
                    if is_error or not isinstance(next_data, dict):
                        break

                    next_block = next_data.get("data", {})
                    next_records = next_block.get("Записи", [])
                    if not isinstance(next_records, list):
                        break

                    for company in next_records:
                        yield {
                            "data": company,
                            "metadata": {
                                "okved": okved,
                                "region": self._region,
                                "downloaded_at": time.time()
                            }
                        }

                    if len(next_records) < connector.PAGE_SIZE:
                        break
                    page += 1

        logging.info("✅ Data extraction completed successfully")

    def extract(self):
        async def run():
            async for item in self._extract_async():
                yield item

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async_gen = run()

        try:
            while True:
                try:
                    item = loop.run_until_complete(async_gen.__anext__())
                    yield item
                except StopAsyncIteration:
                    break
        finally:
            loop.run_until_complete(async_gen.aclose())