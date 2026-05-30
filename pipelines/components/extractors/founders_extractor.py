from typing import Generator, Dict, Any

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector
from settings import SILVER_OFDATA_TABLE


class FoundersExtractor(Extractor):
    """Извлекает информацию об учредителях из Silver-слоя."""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает информацию об учредителях из таблицы silver_ofdata_companies.
        """
        self._pg.connect()
        
        query = """
        SELECT 
            inn,
            founders
        FROM silver.silver_ofdata_companies
        WHERE founders IS NOT NULL
        """
        
        with self._pg.with_defaults(schema="silver", table="silver_ofdata_companies"):
            cursor = self._pg.execute(query)
            
            for row in cursor:
                inn = row[0]
                founders = row[1]
                
                # Обрабатываем учредителей
                if founders and isinstance(founders, dict):
                    # Обрабатываем физических лиц (ФЛ)
                    fl_founders = founders.get('ФЛ', [])
                    if isinstance(fl_founders, list):
                        for founder in fl_founders:
                            if isinstance(founder, dict):
                                yield {
                                    "inn": inn,
                                    "inn_founder": founder.get("ИНН"),
                                    "full_name": founder.get("ФИО"),
                                    "ogrn": None,
                                    "kpp": None,
                                    "is_inaccurate": founder.get("Недост", False),
                                    "reason": founder.get("НедостОпис")
                                }
                    
                    # Обрабатываем российские организации (РФ)
                    rf_founders = founders.get('РФ', [])
                    if isinstance(rf_founders, list):
                        for founder in rf_founders:
                            if isinstance(founder, dict):
                                yield {
                                    "inn": inn,
                                    "inn_founder": founder.get("ИНН"),
                                    "full_name": founder.get("НаимЮЛПолн"),
                                    "ogrn": founder.get("ОГРН"),
                                    "kpp": founder.get("КПП"),
                                    "is_inaccurate": founder.get("Недост", False),
                                    "reason": founder.get("НедостОпис")
                                }
                
                elif founders and isinstance(founders, list):
                    for founder in founders:
                        if isinstance(founder, dict):
                            yield {
                                "inn": inn,
                                "inn_founder": founder.get("inn"),
                                "full_name": founder.get("fio", {}).get("name") if founder.get("fio") else founder.get("name"),
                                "ogrn": founder.get("ogrn"),
                                "kpp": founder.get("kpp"),
                                "is_inaccurate": founder.get("invalidity") is not None,
                                "reason": None
                            }