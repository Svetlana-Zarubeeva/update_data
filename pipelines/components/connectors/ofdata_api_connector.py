import asyncio
import logging
from typing import Any, Dict, Optional, Tuple, AsyncIterator

import aiohttp
from aiohttp import ClientTimeout

from pipelines.components.connectors.connector import Connector
from settings import (
    OFDATA_API_URL,
    OFDATA_API_TIMEOUT,
    OFDATA_API_MAX_RETRIES,
    OFDATA_API_RETRY_DELAY,
    OFDATA_API_MAX_PAGE_SIZE,
    OFDATA_API_KEY,
)


class OfdataApiConnector(Connector):
    """Асинхронный клиент для взаимодействия с API сервиса ofdata.ru."""

    PAGE_SIZE = OFDATA_API_MAX_PAGE_SIZE

    def __init__(self):
        super().__init__()
        self._session: Optional[aiohttp.ClientSession] = None
        self._is_closed = True
        self._request_timeout = ClientTimeout(total=OFDATA_API_TIMEOUT)

    async def connect(self):
        if self._is_closed:
            self._session = aiohttp.ClientSession(
                timeout=self._request_timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                }
            )
            self._is_closed = False

    async def close(self):
        if not self._is_closed and self._session and not self._session.closed:
            await self._session.close()
        self._is_closed = True

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _make_request_with_retry(
        self,
        endpoint: str,
        params: Dict[str, Any],
        max_retries: int = OFDATA_API_MAX_RETRIES
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        params = {**params, "key": OFDATA_API_KEY}
        url = f"{OFDATA_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        
        total_retries = 0
        while total_retries <= max_retries:
            try:
                async with self._session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json(), False
                    elif response.status in (429, 500, 502, 503, 504):
                        total_retries += 1
                        if total_retries <= max_retries:
                            await asyncio.sleep(OFDATA_API_RETRY_DELAY)
                            continue
                        else:
                            logging.error("Max retries exceeded")
                            return None, True
                    else:
                        logging.error(f"Unexpected status: {response.status}, URL: {url}, params: {params}")
                        return None, True
            except Exception as e:
                total_retries += 1
                if total_retries > max_retries:
                    logging.error(f"Max retries exceeded: {e}")
                    return None, True
                await asyncio.sleep(OFDATA_API_RETRY_DELAY)
        return None, True

    async def search_companies(
        self,
        okved: str,
        region: str,
        page: int = 1,
        page_size: int = OFDATA_API_MAX_PAGE_SIZE
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        params = {
            "by": "okved",
            "obj": "org",
            "query": okved,         # <-- значение кода ОКВЭД передаётся в query при by=okved
            "region": region,
            "limit": page_size,
            "page": page,
        }
        return await self._make_request_with_retry("v2/search", params)