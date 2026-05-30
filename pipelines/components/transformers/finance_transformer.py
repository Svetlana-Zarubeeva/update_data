from typing import Generator, Dict, Any

from pipelines.components.transformers.transformer import Transformer


class FinanceTransformer(Transformer):
    """Преобразует финансовую информацию в структурированный формат для Gold-слоя."""
    
    def _safe_int(self, value):
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value):
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_str(self, value, default=""):
        if value is None:
            return default
        return str(value)

    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует финансовую информацию в структурированный формат.
        """
        for record in data:
            finance = {
                "inn": self._safe_str(record["inn"]),
                "employee_count": self._safe_int(record["employee_count"]),
                "revenue": self._safe_float(record["revenue"]),
                "income": self._safe_float(record["income"]),
                "expense": self._safe_float(record["expense"]),
                "tax_system": self._safe_str(record["tax_system"])
            }

            yield finance