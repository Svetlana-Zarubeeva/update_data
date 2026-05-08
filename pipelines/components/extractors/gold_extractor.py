from typing import Generator, Dict, Any, Optional

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.postgres_connector import PostgresConnector


class GoldExtractor(Extractor):
    """Извлекает данные из Silver-слоя для обработки в Gold-слое."""
    
    def __init__(self, pg_connector: PostgresConnector):
        self._pg = pg_connector

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """
        Извлекает объединенные данные из silver_ofdata_companies и silver_dadata_companies.
        Возвращает генератор записей для дальнейшей обработки.
        """
        self._pg.connect()
        
        # SQL-запрос для объединения данных из двух источников
        query = """
        SELECT 
            -- Из ofdata
            o.inn,
            o.ogrn,
            o.kpp,
            o.short_name as ofdata_short_name,
            o.full_name as ofdata_full_name,
            o.reg_date,
            o.status as ofdata_status,
            o.region_code,
            o.okved_code,
            o.okved_description,
            o.directors,
            o.founders,
            
            -- Из dadata
            d.company_name as dadata_company_name,
            d.short_name as dadata_short_name,
            d.status as dadata_status,
            d.registration_date,
            d.actuality_date,
            d.address_full,
            d.postal_code,
            d.region,
            d.city,
            d.street,
            d.house,
            d.flat,
            d.latitude,
            d.longitude,
            d.phones,
            d.emails,
            d.websites,
            d.employee_count,
            d.revenue,
            d.income,
            d.expense,
            d.tax_system,
            d.management_name,
            d.management_post,
            d.management_start_date,
            d.okved_main,
            d.okveds
            
        FROM silver.silver_ofdata_companies o
        LEFT JOIN silver.silver_dadata_companies d ON o.inn = d.inn
        """
        
        with self._pg.with_defaults(schema="silver", table="silver_ofdata_companies"):
            cursor = self._pg.execute(query)
            
            for row in cursor:
                yield {
                    "inn": row[0],
                    "ogrn": row[1],
                    "kpp": row[2],
                    "ofdata_short_name": row[3],
                    "ofdata_full_name": row[4],
                    "reg_date": row[5],
                    "ofdata_status": row[6],
                    "region_code": row[7],
                    "okved_code": row[8],
                    "okved_description": row[9],
                    "directors": row[10],
                    "founders": row[11],
                    
                    "dadata_company_name": row[12],
                    "dadata_short_name": row[13],
                    "dadata_status": row[14],
                    "registration_date": row[15],
                    "actuality_date": row[16],
                    "address_full": row[17],
                    "postal_code": row[18],
                    "region": row[19],
                    "city": row[20],
                    "street": row[21],
                    "house": row[22],
                    "flat": row[23],
                    "latitude": row[24],
                    "longitude": row[25],
                    "phones": row[26],
                    "emails": row[27],
                    "websites": row[28],
                    "employee_count": row[29],
                    "revenue": row[30],
                    "income": row[31],
                    "expense": row[32],
                    "tax_system": row[33],
                    "management_name": row[34],
                    "management_post": row[35],
                    "management_start_date": row[36],
                    "okved_main": row[37],
                    "okveds": row[38]
                }