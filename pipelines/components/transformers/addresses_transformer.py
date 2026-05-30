from typing import Generator, Dict, Any
import re
import string

from pipelines.components.transformers.transformer import Transformer


class AddressesTransformer(Transformer):
    """Преобразует адреса в структурированный формат для Gold-слоя."""
    
    def _normalize_address(self, address: str) -> str:
        """Нормализует строку адреса к единому формату."""
        if not address:
            return ""
        
        # Убираем лишние пробелы
        address = re.sub(r'\s+', ' ', address).strip()
        
        # Приводим к нижнему регистру
        address = address.lower()
        
        # Заменяем сокращения на полные названия
        replacements = [
            (r'\bг\.?\b', 'город '),
            (r'\bул\.?\b', 'улица '),
            (r'\bпер\.?\b', 'переулок '),
            (r'\bпр\.?\b', 'проспект '),
            (r'\bш\.?\b', 'шоссе '),
            (r'\bпл\.?\b', 'площадь '),
            (r'\bд\.?\b', 'дом '),
            (r'\bкв\.?\b', 'квартира '),
            (r'\bофис\.?\b', 'офис '),
            (r'\bпомещ\.?\b', 'помещение '),
            (r'\bкорп\.?\b', 'корпус '),
            (r'\bстроение\.?\b', 'строение '),
            (r'\bдом\.?\b', 'дом '),
            (r'\bр-н\.?\b', 'район '),
            (r'\bобл\.?\b', 'область '),
            (r'\bс\.?\b', 'село '),
            (r'\bп\.?\b', 'поселок '),
            (r'\bст-ца\.?\b', 'станица '),
            (r'\bпос\.?\b', 'поселок '),
            (r'\bг\.?\b', 'город '),
            (r'\bпгт\.?\b', 'поселок городского типа '),
            (r'\bмкр\.?\b', 'микрорайон '),
            (r'\bул\.?\b', 'улица '),
        ]
        
        for pattern, replacement in replacements:
            address = re.sub(pattern, replacement, address)
        
        # Удаляем лишние пробелы после замены
        address = re.sub(r'\s+', ' ', address).strip()
        
        # Убираем дублирующиеся слова (например, "город город")
        address = re.sub(r'\b(\w+)\s+\1\b', r'\1', address)
        
        # Убираем лишние запятые
        address = re.sub(r',\s*,', ',', address)
        address = re.sub(r'^,\s*|,\s*$', '', address)
        
        # Добавляем пробел после запятых, если их нет
        address = re.sub(r',(\S)', r', \1', address)
        
        # Убираем лишние пробелы перед знаками препинания
        address = re.sub(r'\s+([,.;:])', r'\1', address)
        
        # Приводим к стандартному формату: регион, район, город, улица, дом, квартира
        # (если это возможно)
        
        # Возвращаем нормализованный адрес
        return address.title()

    def _safe_str(self, value, default=""):
        if value is None:
            return default
        return str(value)
    
    def _safe_float(self, value):
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует данные адресов в структурированный формат.
        """
        for record in data:
            # Нормализуем полный адрес
            normalized_address = self._normalize_address(record["address_full"])
            
            address = {
                "inn": self._safe_str(record["inn"]),
                "address_full": normalized_address,
                "postal_code": self._safe_str(record["postal_code"]),
                "region": self._safe_str(record["region"]),
                "district": self._safe_str(record.get("district", "")),  # Новое поле
                "city": self._safe_str(record["city"]),
                "street": self._safe_str(record["street"]),
                "house": self._safe_str(record["house"]),
                "flat": self._safe_str(record["flat"]),
                "latitude": self._safe_float(record["latitude"]),
                "longitude": self._safe_float(record["longitude"])
            }

            yield address