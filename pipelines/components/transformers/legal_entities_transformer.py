from typing import Generator, Dict, Any
import datetime

from pipelines.components.transformers.transformer import Transformer


class LegalEntitiesTransformer(Transformer):
    """Преобразует данные юридических лиц в структурированный формат для Gold-слоя."""
    
    def _safe_str(self, value, default=""):
        if value is None:
            return default
        return str(value)
    
    def _safe_date(self, value):
        if value and isinstance(value, datetime.datetime):
            return value.date()
        return value

    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует данные юридических лиц в структурированный формат.
        """
        for record in data:
            legal_entity = {
                "inn": self._safe_str(record["inn"]),
                "ogrn": self._safe_str(record["ogrn"]),
                "kpp": self._safe_str(record["kpp"]),
                "short_name": self._safe_str(record["short_name"]),
                "full_name": self._safe_str(record["full_name"]),
                "registration_date": self._safe_date(record["registration_date"]),
                "status": self._safe_str(record["status"], "UNKNOWN"),
                "okved_code": self._safe_str(record["okved_code"])
            }

            yield legal_entity