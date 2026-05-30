import asyncio
import logging
import time
from datetime import datetime, date
from typing import Any, Dict, AsyncGenerator, Optional

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.checko_api_connector import CheckoApiConnector
from pipelines.components.connectors.postgres_connector import PostgresConnector


class CheckoBronzeExtractor(Extractor):
    """Извлекает полные JSON данные организаций из checko.ru по компаниям из базы данных."""

    def __init__(
        self,
        postgres_connector: PostgresConnector
    ):
        self._postgres_connector = postgres_connector
        self._current_api_key = None
        self._api_keys = []
        self._keys_exhausted = False

    def _reset_daily_limits(self):
        """Принудительно сбрасывает used_today для всех ключей при каждом запуске пайплайна."""
        try:
            self._postgres_connector.connect()
            
            # Принудительный сброс ВСЕХ ключей без проверки даты
            reset_query = """
                UPDATE api_keys 
                SET used_today = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE service_name = 'checko'
                  AND is_active = true
            """
            result = self._postgres_connector.execute(reset_query)
            
            if result:
                logging.info("✅ Reset all daily limits for checko keys (forced reset)")
            else:
                logging.info("ℹ️ No keys to reset")
                    
        except Exception as e:
            logging.error(f"❌ Error resetting daily limits: {str(e)}")
        finally:
            self._postgres_connector.close()

    def _fetch_api_keys(self) -> list[Dict[str, Any]]:
        """Получает ВСЕ активные API-ключи для сервиса checko из PostgreSQL."""
        # Принудительно сбрасываем лимиты при каждом запуске
        self._reset_daily_limits()
        
        query = """
            SELECT 
                api_key,
                daily_limit,
                used_today,
                last_used_at
            FROM api_keys 
            WHERE service_name = 'checko' 
              AND is_active = true
            ORDER BY used_today ASC, last_used_at ASC NULLS FIRST
        """
        
        api_keys = []
        try:
            self._postgres_connector.connect()
            for row in self._postgres_connector.ss_execute(query, cast=dict):
                api_keys.append({
                    "api_key": row.get("api_key"),
                    "daily_limit": row.get("daily_limit"),
                    "used_today": row.get("used_today"),
                    "last_used_at": row.get("last_used_at")
                })
        finally:
            self._postgres_connector.close()
            
        logging.info(f"✅ Fetched {len(api_keys)} active API keys for checko")
        return api_keys

    def _get_next_api_key(self) -> Optional[str]:
        """Возвращает следующий доступный API ключ или None, если все исчерпаны."""
        if self._keys_exhausted:
            return None
            
        if not self._api_keys:
            self._api_keys = self._fetch_api_keys()
            
        if not self._api_keys:
            logging.error("❌ No active API keys available for checko service")
            self._keys_exhausted = True
            return None
            
        # Берем первый доступный ключ (лимиты уже сброшены)
        best_key = self._api_keys[0]["api_key"]
        self._current_api_key = best_key
        self._api_keys.pop(0)
        return best_key

    def _update_api_key_usage(self, api_key: str):
        """Обновляет счетчик использования API ключа."""
        if not api_key:
            return
            
        update_query = """
            UPDATE api_keys 
            SET used_today = used_today + 1,
                last_used_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE api_key = %s AND service_name = 'checko'
        """
        
        try:
            self._postgres_connector.connect()
            self._postgres_connector.execute(update_query, api_key)
            logging.info(f"✅ Updated usage for API key: {api_key[:10]}...")
        except Exception as e:
            logging.error(f"❌ Error updating API key usage: {str(e)}")
        finally:
            self._postgres_connector.close()

    def _mark_all_keys_exhausted(self):
        """Отмечает все ключи как исчерпавшие лимит на сегодня."""
        mark_query = """
            UPDATE api_keys 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE service_name = 'checko' AND is_active = true
        """
        
        try:
            self._postgres_connector.connect()
            self._postgres_connector.execute(mark_query)
            logging.info("✅ Marked all checko keys as processed")
        except Exception as e:
            logging.error(f"❌ Error marking keys as exhausted: {str(e)}")
        finally:
            self._postgres_connector.close()

    def _fetch_companies(self) -> list[Dict[str, Any]]:
        """Получает список компаний с ИНН и ОГРН из PostgreSQL."""
        query = f"""
            SELECT DISTINCT 
                le.inn,
                le.ogrn,
                le.short_name,
                a.address_full as address
            FROM legal_entities le
            LEFT JOIN addresses a ON le.id = a.legal_entity_id
            WHERE le.inn IS NOT NULL AND le.inn != ''
            ORDER BY le.inn
        """
        
        companies = []
        try:
            self._postgres_connector.connect()
            for row in self._postgres_connector.ss_execute(query, cast=dict):
                companies.append({
                    "inn": row.get("inn"),
                    "ogrn": row.get("ogrn"),
                    "short_name": row.get("short_name"),
                    "address": row.get("address")
                })
        finally:
            self._postgres_connector.close()
            
        logging.info(f"✅ Fetched {len(companies)} companies from PostgreSQL")
        return companies

    async def _extract_async(self) -> AsyncGenerator[Dict[str, Any], None]:
        companies = self._fetch_companies()
        if not companies:
            logging.warning("⚠️ No companies found in PostgreSQL table")
            return

        logging.info(f"🔍 Starting data extraction for {len(companies)} companies")

        companies_processed = 0
        
        try:
            for company in companies:
                inn = company.get("inn")
                ogrn = company.get("ogrn")
                short_name = company.get("short_name")
                address = company.get("address")
                
                if not inn:
                    continue
                
                # Получаем НОВЫЙ API ключ для КАЖДОЙ компании
                current_key = self._get_next_api_key()
                if not current_key:
                    # Все ключи исчерпаны - создаем пустую запись и продолжаем
                    yield {
                        "data": {},
                        "metadata": {
                            "inn": inn,
                            "ogrn": ogrn,
                            "short_name": short_name,
                            "downloaded_at": time.time(),
                            "status": "api_limit_exhausted"
                        }
                    }
                    continue
                
                # Создаем новый коннектор для каждого запроса
                current_connector = CheckoApiConnector(current_key)
                try:
                    current_connector.connect()
                    
                    # Получаем полный JSON ответ о компании
                    company_json = current_connector.get_company_info(inn=inn, ogrn=ogrn)
                    
                    # Обновляем использование API ключа
                    self._update_api_key_usage(current_key)
                    companies_processed += 1
                    
                    if not company_json:
                        # Создаем запись для не найденной компании
                        yield {
                            "data": {},
                            "metadata": {
                                "inn": inn,
                                "ogrn": ogrn,
                                "short_name": short_name,
                                "downloaded_at": time.time(),
                                "status": "not_found"
                            }
                        }
                        continue
                    
                    # Возвращаем полный JSON ответ без обработки
                    yield {
                        "data": company_json,
                        "metadata": {
                            "inn": inn,
                            "ogrn": ogrn,
                            "short_name": short_name,
                            "downloaded_at": time.time(),
                            "status": "found"
                        }
                    }
                    
                finally:
                    current_connector.close()
                    
        finally:
            # Отмечаем, что все ключи были обработаны
            self._mark_all_keys_exhausted()
            
        logging.info(f"✅ Data extraction completed successfully for {companies_processed} companies")

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