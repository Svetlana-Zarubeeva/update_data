import datetime
from typing import Generator, Dict, Any, List, Optional

from pipelines.components.transformers.transformer import Transformer


class DadataSilverTransformer(Transformer):
    """Преобразует данные из Bronze-слоя DaData в структурированный формат для Silver-слоя."""
    
    def _extract_address(self, address_data: Dict) -> Dict[str, Any]:
        """Извлекает адресные данные."""
        if not address_data or not isinstance(address_data, dict):
            return {}
            
        data = address_data.get("data", {})
        if not isinstance(data, dict):
            data = {}
            
        return {
            "address_full": address_data.get("value"),
            "postal_code": data.get("postal_code"),
            "region": data.get("region"),
            "city": data.get("city"),
            "street": data.get("street"),
            "house": data.get("house"),
            "flat": data.get("flat"),
            "latitude": data.get("geo_lat"),
            "longitude": data.get("geo_lon")
        }
    
    def _extract_phones(self, phones_data: List) -> List[Dict[str, Any]]:
        """Извлекает телефонные номера."""
        if not phones_data:
            return []
            
        phones = []
        for phone in phones_data:
            if isinstance(phone, dict) and "data" in phone:
                phone_data = phone["data"]
                if isinstance(phone_data, dict):
                    phones.append({
                        "number": phone_data.get("source"),
                        "type": phone_data.get("type"),
                        "provider": phone_data.get("provider")
                    })
        return phones
    
    def _extract_emails(self, emails_data: List) -> List[str]:
        """Извлекает email-адреса."""
        if not emails_data:
            return []
            
        emails = []
        for email in emails_data:
            if isinstance(email, dict) and "data" in email:
                email_data = email["data"]
                if isinstance(email_data, dict):
                    email_source = email_data.get("source")
                    if email_source:
                        emails.append(email_source)
        return emails
    
    def _extract_websites(self, sites_data: List) -> List[str]:
        """Извлекает веб-сайты."""
        return []
    
    def _extract_okveds(self, okveds_data: List) -> List[Dict[str, Any]]:
        """Извлекает коды ОКВЭД."""
        if not okveds_data:
            return []
            
        okveds = []
        for okved in okveds_data:
            if isinstance(okved, dict):
                okveds.append({
                    "code": okved.get("code"),
                    "name": okved.get("name"),
                    "main": okved.get("main", False)
                })
        return okveds

    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует сырые данные из Bronze-слоя в структурированный формат для Silver-слоя.
        """
        for record in data:
            dadata = record.get("data", {})
            if not dadata or not isinstance(dadata, dict):
                continue
                
            data_section = dadata.get("data", {})
            if not data_section or not isinstance(data_section, dict):
                continue
            
            # Безопасное получение finance
            finance_data = data_section.get("finance") or {}
            if not isinstance(finance_data, dict):
                finance_data = {}
            
            # Безопасное получение state
            state_data = data_section.get("state") or {}
            if not isinstance(state_data, dict):
                state_data = {}
            
            # Безопасное получение management
            management_data = data_section.get("management") or {}
            if not isinstance(management_data, dict):
                management_data = {}
            
            # Безопасное получение name
            name_data = data_section.get("name") or {}
            if not isinstance(name_data, dict):
                name_data = {}

            # Основная информация
            transformed = {
                "inn": record.get("inn"),
                "ogrn": record.get("ogrn"),
                "company_name": name_data.get("full_with_opf"),
                "short_name": name_data.get("short_with_opf"),
                "kpp": data_section.get("kpp"),
                "status": state_data.get("status"),
                "registration_date": self._convert_timestamp(state_data.get("registration_date")),
                "actuality_date": self._convert_timestamp(state_data.get("actuality_date")),
                
                # Адрес
                **self._extract_address(data_section.get("address", {})),
                
                # Контактная информация
                "phones": self._extract_phones(data_section.get("phones", [])),
                "emails": self._extract_emails(data_section.get("emails", [])),
                "websites": self._extract_websites(data_section.get("sites", [])),
                
                # Финансы
                "employee_count": data_section.get("employee_count"),
                "revenue": finance_data.get("revenue"),
                "income": finance_data.get("income"),
                "expense": finance_data.get("expense"),
                "tax_system": finance_data.get("tax_system"),
                
                # Руководство
                "management_name": management_data.get("name"),
                "management_post": management_data.get("post"),
                "management_start_date": self._convert_timestamp(management_data.get("start_date")),
                
                # ОКВЭД
                "okved_main": data_section.get("okved"),
                "okveds": self._extract_okveds(data_section.get("okveds", [])),
                
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            }
            
            transformed = {k: v for k, v in transformed.items() if v is not None}
            yield transformed
    
    def _convert_timestamp(self, timestamp) -> Optional[datetime.datetime]:
        """Преобразует timestamp из формата DaData в datetime."""
        if timestamp is None:
            return None
            
        if isinstance(timestamp, dict) and "$numberLong" in timestamp:
            timestamp = int(timestamp["$numberLong"])
        elif isinstance(timestamp, str):
            try:
                timestamp = int(timestamp)
            except ValueError:
                return None
        
        if isinstance(timestamp, int):
            if timestamp > 1e10:
                return datetime.datetime.fromtimestamp(timestamp / 1000)
            else:
                return datetime.datetime.fromtimestamp(timestamp)
                
        return None