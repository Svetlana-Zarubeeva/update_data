from typing import Generator, Dict, Any
import datetime

from pipelines.components.transformers.transformer import Transformer


class ManagementTransformer(Transformer):
    """Преобразует информацию о руководстве в структурированный формат для Gold-слоя."""
    
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
        Преобразует информацию о руководстве в структурированный формат.
        """
        for record in data:
            management = {
                "inn": self._safe_str(record["inn"]),
                "name": self._safe_str(record["name"]),
                "post": self._safe_str(record["post"]),
                "start_date": self._safe_date(record["start_date"])
            }

            yield management