import datetime
from typing import Generator, Dict, Any, List, Optional

from pipelines.components.transformers.transformer import Transformer


class GoldTransformer(Transformer):
    """Преобразует объединенные данные в структурированный формат для Gold-слоя."""
    
    def _extract_management(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Извлекает данные о руководстве."""
        if record.get("management_name") or record.get("management_post"):
            return {
                "name": record.get("management_name"),
                "post": record.get("management_post"),
                "start_date": record.get("management_start_date")
            }
        return None
    
    def _extract_founders(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлекает данные об учредителях из ofdata."""
        founders = []
        ofdata_founders = record.get("founders")
        
        if ofdata_founders and isinstance(ofdata_founders, dict):
            # Обрабатываем физических лиц (ФЛ)
            fl_founders = ofdata_founders.get('ФЛ', [])
            if isinstance(fl_founders, list):
                for founder in fl_founders:
                    if isinstance(founder, dict):
                        founders.append({
                            "inn": founder.get("ИНН"),
                            "full_name": founder.get("ФИО"),
                            "ogrn": None,
                            "kpp": None,
                            "is_inaccurate": founder.get("Недост", False),
                            "reason": founder.get("НедостОпис")
                        })
            
            # Обрабатываем российские организации (РФ)
            rf_founders = ofdata_founders.get('РФ', [])
            if isinstance(rf_founders, list):
                for founder in rf_founders:
                    if isinstance(founder, dict):
                        founders.append({
                            "inn": founder.get("ИНН"),
                            "full_name": founder.get("НаимЮЛПолн"),
                            "ogrn": founder.get("ОГРН"),
                            "kpp": founder.get("КПП"),
                            "is_inaccurate": founder.get("Недост", False),
                            "reason": founder.get("НедостОпис")
                        })
                    
        elif ofdata_founders and isinstance(ofdata_founders, list):
            for founder in ofdata_founders:
                if isinstance(founder, dict):
                    founders.append({
                        "inn": founder.get("inn"),
                        "full_name": founder.get("fio", {}).get("name") if founder.get("fio") else founder.get("name"),
                        "ogrn": founder.get("ogrn"),
                        "kpp": founder.get("kpp"),
                        "is_inaccurate": founder.get("invalidity") is not None,
                        "reason": None
                    })
        
        return founders
    
    def _determine_okved_id(self, record: Dict[str, Any]) -> Optional[str]:
        """Определяет ID ОКВЭД на основе IT-справочника."""
        okved_code = record.get("okved_main") or record.get("okved_code")
        if okved_code:
            return okved_code
        return None

    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует объединенные данные в структурированный формат для Gold-слоя.
        """
        for record in data:
            # Основная информация о юрлице
            legal_entity = {
                "inn": record["inn"],
                "ogrn": record["ogrn"],
                "kpp": record["kpp"],
                "short_name": record.get("dadata_short_name") or record.get("ofdata_short_name") or "",
                "full_name": record.get("dadata_company_name") or record.get("ofdata_full_name") or "",
                "registration_date": record.get("registration_date") or record.get("reg_date"),
                "status": record.get("dadata_status") or record.get("ofdata_status") or "UNKNOWN",
                "okved_id": self._determine_okved_id(record)
            }
            
            # Адрес
            address = {
                "address_full": record.get("address_full") or record.get("ofdata_address") or "",
                "postal_code": record.get("postal_code"),
                "region": record.get("region") or "",
                "city": record.get("city") or "",
                "street": record.get("street"),
                "house": record.get("house"),
                "flat": record.get("flat"),
                "latitude": record.get("latitude"),
                "longitude": record.get("longitude")
            }
            
            # Контактная информация
            contact_info = {
                "phones": record.get("phones") or None,
                "emails": record.get("emails") or None,
                "websites": record.get("websites") or None
            }
            
            # Финансы
            finance = {
                "employee_count": record.get("employee_count"),
                "revenue": record.get("revenue"),
                "income": record.get("income"),
                "expense": record.get("expense"),
                "tax_system": record.get("tax_system")
            }
            
            # Руководство
            management = self._extract_management(record)
            if management:
                if isinstance(management["start_date"], datetime.datetime):
                    management["start_date"] = management["start_date"].date()
            
            # Учредители
            founders = self._extract_founders(record)
            
            transformed = {
                "legal_entity": legal_entity,
                "address": address,
                "contact_info": contact_info,
                "finance": finance,
                "management": management,
                "founders": founders
            }

            yield transformed