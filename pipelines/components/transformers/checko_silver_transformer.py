import datetime
from typing import Generator, Dict, Any, List, Optional

from pipelines.components.transformers.transformer import Transformer


class CheckoSilverTransformer(Transformer):
    """Преобразует данные из Bronze-слоя Checko в структурированный формат для Silver-слоя."""
    
    def _extract_address(self, address_data: Dict) -> Dict[str, Any]:
        """Извлекает адресные данные."""
        if not address_data:
            return {}
            
        # Обработка структуры Checko
        if isinstance(address_data, dict) and "ЮрАдрес" in address_data:
            address_info = address_data["ЮрАдрес"]
            if not isinstance(address_info, dict):
                return {}
            address_full = address_info.get("АдресРФ")
            data_section = address_info
        else:
            address_full = address_data.get("АдресРФ") or address_data.get("value")
            data_section = address_data
            
        return {
            "address_full": address_full,
            "postal_code": data_section.get("Индекс") or data_section.get("postal_code"),
            "region": data_section.get("Регион", {}).get("Наим") if isinstance(data_section.get("Регион"), dict) else data_section.get("Регион"),
            "city": data_section.get("НасПункт") or data_section.get("city"),
            "street": data_section.get("Улица") or data_section.get("street"),
            "house": data_section.get("Дом") or data_section.get("house"),
            "flat": data_section.get("Кварт") or data_section.get("flat"),
            "latitude": None,
            "longitude": None
        }
    
    def _extract_phones(self, contacts_data: Dict) -> List[Dict[str, Any]]:
        """Извлекает телефонные номера."""
        phones = []
        if contacts_data and isinstance(contacts_data, dict):
            tel_list = contacts_data.get("Тел", [])
            if isinstance(tel_list, list):
                for phone in tel_list:
                    if isinstance(phone, str) and phone.strip():
                        phones.append({"number": phone.strip(), "type": "main"})
        return phones
    
    def _extract_emails(self, contacts_data: Dict) -> List[str]:
        """Извлекает email-адреса."""
        emails = []
        if contacts_data and isinstance(contacts_data, dict):
            email_list = contacts_data.get("Емэйл", [])
            if isinstance(email_list, list):
                for email in email_list:
                    if isinstance(email, str) and email.strip():
                        emails.append(email.strip())
        return emails
    
    def _extract_websites(self, contacts_data: Dict) -> List[str]:
        """Извлекает веб-сайты."""
        websites = []
        if contacts_data and isinstance(contacts_data, dict):
            site = contacts_data.get("Сайт")
            if isinstance(site, str) and site.strip():
                websites.append(site.strip())
        return websites
    
    def _extract_okveds(self, okved_data: Dict, okved_dop: List) -> List[Dict[str, Any]]:
        """Извлекает коды ОКВЭД."""
        okveds = []
        
        # Основной ОКВЭД
        if okved_data and isinstance(okved_data, dict):
            code = okved_data.get("Код")
            name = okved_data.get("Наим")
            if isinstance(code, str) and code.strip():
                okveds.append({
                    "code": code.strip(),
                    "name": name if isinstance(name, str) else None,
                    "main": True
                })
        elif isinstance(okved_data, str) and okved_data.strip():
            okveds.append({
                "code": okved_data.strip(),
                "name": None,
                "main": True
            })
        
        # Дополнительные ОКВЭД
        if okved_dop and isinstance(okved_dop, list):
            for okved in okved_dop:
                if isinstance(okved, dict):
                    code = okved.get("Код")
                    name = okved.get("Наим")
                    if isinstance(code, str) and code.strip():
                        okveds.append({
                            "code": code.strip(),
                            "name": name if isinstance(name, str) else None,
                            "main": False
                        })
        
        return okveds

    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует сырые данные из Bronze-слоя в структурированный формат для Silver-слоя.
        """
        for record in data:
            # Пропускаем записи без корректного ИНН
            inn = record.get("inn")
            if not inn or not isinstance(inn, str) or len(inn) not in [10, 12]:
                continue
                
            checko_data = record.get("data", {})
            if not checko_data or not isinstance(checko_data, dict):
                continue
                
            # Обработка структуры Checko
            if "data" in checko_data and isinstance(checko_data["data"], dict):
                data_section = checko_data["data"]
            else:
                data_section = checko_data
            
            if not data_section:
                continue
            
            # Безопасное получение state
            status_data = data_section.get("Статус") or {}
            if not isinstance(status_data, dict):
                status_data = {"Наим": str(status_data) if status_data else "UNKNOWN"}
            
            # Безопасное получение management
            management_list = data_section.get("Руковод") or []
            management_data = {}
            if management_list and isinstance(management_list, list):
                for manager in management_list:
                    if isinstance(manager, dict) and not manager.get("Недост", False):
                        management_data = manager
                        break
            
            # Безопасное получение name
            company_name = data_section.get("НаимПолн") or data_section.get("НаимСокр") or ""
            short_name = data_section.get("НаимСокр") or ""

            # Основная информация
            transformed = {
                "inn": inn,
                "ogrn": record.get("ogrn") or data_section.get("ОГРН"),
                "company_name": company_name,
                "short_name": short_name,
                "kpp": data_section.get("КПП"),
                "status": status_data.get("Наим", "UNKNOWN"),
                "registration_date": self._convert_date(data_section.get("ДатаРег")),
                "actuality_date": self._convert_date(data_section.get("ДатаОГРН")),
                
                # Адрес
                **self._extract_address(data_section.get("ЮрАдрес", {}) or data_section),
                
                # Контактная информация
                "phones": self._extract_phones(data_section.get("Контакты", {}) or {}),
                "emails": self._extract_emails(data_section.get("Контакты", {}) or {}),
                "websites": self._extract_websites(data_section.get("Контакты", {}) or {}),
                
                # Финансы
                "employee_count": data_section.get("СЧР"),
                "revenue": None,
                "income": None,
                "expense": None,
                "tax_system": None,
                
                # Руководство
                "management_name": management_data.get("ФИО") if management_data else None,
                "management_post": management_data.get("НаимДолжн") if management_data else None,
                "management_start_date": self._convert_date(management_data.get("ДатаЗаписи")) if management_data else None,
                
                # ОКВЭД
                "okved_main": data_section.get("ОКВЭД", {}).get("Код") if isinstance(data_section.get("ОКВЭД"), dict) else data_section.get("ОКВЭД"),
                "okveds": self._extract_okveds(data_section.get("ОКВЭД"), data_section.get("ОКВЭДДоп", [])),
                
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            }
            
            # Удаляем None значения, но оставляем пустые строки и списки
            transformed = {k: v for k, v in transformed.items() if v is not None}
            yield transformed
    
    def _convert_date(self, date_value) -> Optional[datetime.datetime]:
        """Преобразует дату из формата Checko в datetime."""
        if date_value is None:
            return None
            
        if isinstance(date_value, str):
            try:
                return datetime.datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                return None
                
        return None