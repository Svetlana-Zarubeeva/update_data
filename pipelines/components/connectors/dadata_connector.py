import logging
import requests
import time
import random
from typing import Optional, Dict, Any

from pipelines.components.connectors.connector import Connector
from settings import DADATA_API_KEY, DADATA_SECRET_KEY, DADATA_API_URL


class DadataConnector(Connector):
    def __init__(self, timeout: int = 20, max_retries: int = 3):
        super().__init__()
        self.timeout = timeout
        self.max_retries = max_retries
        self._is_connected = False
        self._last_request_time = 0

    def _respect_rate_limit(self):
        """Добавляет случайную задержку между запросами для избежания блокировки."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        min_delay = 0.5
        if elapsed < min_delay:
            delay = min_delay + random.uniform(0.1, 0.5)
            time.sleep(delay)
        self._last_request_time = time.time()

    def connect(self) -> None:
        if not self._is_connected:
            self._is_connected = True
            self.logger.info("🔌 Connected to DaData API")

    def close(self) -> None:
        if self._is_connected:
            self._is_connected = False
            self.logger.info("🔌 Disconnected from DaData API")

    def fetch_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        if not self._is_connected:
            self.connect()

        headers = {
            "Authorization": f"Token {DADATA_API_KEY}",
            "Content-Type": "application/json",
        }
        if DADATA_SECRET_KEY:
            headers["X-Secret"] = DADATA_SECRET_KEY

        for attempt in range(self.max_retries + 1):
            self._respect_rate_limit()

            try:
                response = requests.post(
                    DADATA_API_URL,
                    json={"query": inn},
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    self.logger.error(f"❌ Unexpected Content-Type: {content_type}. Response: {response.text[:200]}...")
                    return None
                    
                data = response.json()
                suggestions = data.get("suggestions", [])
                
                if not suggestions:
                    self.logger.warning(f"⚠️ No data found in DaData for INN={inn}")
                    return None

                return suggestions[0]

            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning(f"⏳ Timeout for INN={inn}, retry {attempt + 1}/{self.max_retries} in {wait_time:.1f}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"❌ Failed after {self.max_retries} retries for INN={inn} (timeout={self.timeout}s)")
                    return None
                    
            except requests.exceptions.JSONDecodeError:
                self.logger.error(f"❌ Invalid JSON response from DaData API for INN={inn}. Response: {response.text[:200]}...")
                return None
                
            except Exception as e:
                self.logger.error(f"❌ Error fetching from DaData API for INN={inn}: {e}")
                return None