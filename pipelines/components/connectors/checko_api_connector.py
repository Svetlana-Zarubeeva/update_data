import requests
import time
import random
from typing import Optional, Dict, Any

from pipelines.components.connectors.connector import Connector
from settings import CHECKO_REQUEST_DELAY_MIN, CHECKO_REQUEST_DELAY_MAX, CHECKO_API_URL


class CheckoApiConnector(Connector):
    """Коннектор для работы с официальным API checko.ru."""

    def __init__(self, api_key: str):
        super().__init__()
        self._session = None
        self._api_key = api_key
        if not self._api_key:
            raise ValueError("API key must be provided")
        
        # Задержки между запросами
        self._delay_min = CHECKO_REQUEST_DELAY_MIN or 1
        self._delay_max = CHECKO_REQUEST_DELAY_MAX or 2
        self._max_retries = 3

    def connect(self) -> None:
        """Создает сессию requests."""
        if self._session:
            return
            
        self._session = requests.Session()

    def close(self) -> None:
        """Закрывает сессию."""
        if self._session:
            self._session.close()
            self._session = None

    def get_company_info(self, inn: str = None, ogrn: str = None) -> Optional[Dict[str, Any]]:
        """
        Получает полный JSON ответ о компании из API checko.ru.
        """
        if not self._session:
            self.connect()
            
        if not inn and not ogrn:
            raise ValueError("Either inn or ogrn must be provided")
            
        params = {
            'key': self._api_key
        }
        if inn:
            params['inn'] = inn
        if ogrn:
            params['ogrn'] = ogrn
            
        url = f"{CHECKO_API_URL}/company"
            
        for attempt in range(self._max_retries):
            try:
                delay = random.uniform(self._delay_min, self._delay_max)
                time.sleep(delay)
                
                response = self._session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 60
                    print(f"⚠️ API rate limit exceeded for company {inn or ogrn}. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 404:
                    print(f"❌ Company not found (404) for INN: {inn}, OGRN: {ogrn}")
                    return None
                elif response.status_code == 403:
                    print("❌ Invalid API key or access denied")
                    return None
                else:
                    print(f"❌ Company API error {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching company info (attempt {attempt + 1}): {str(e)}")
                if attempt < self._max_retries - 1:
                    time.sleep((attempt + 1) * 10)
                else:
                    return None
                    
        return None