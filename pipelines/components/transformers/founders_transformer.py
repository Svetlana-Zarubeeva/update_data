from typing import Generator, Dict, Any

from pipelines.components.transformers.transformer import Transformer


class FoundersTransformer(Transformer):
    """Преобразует информацию об учредителях в структурированный формат для Gold-слоя."""
    
    def _safe_str(self, value, default=""):
        if value is None:
            return default
        return str(value)

    def _get_founder_type_id(self, founder_data):
        """Определяет тип учредителя на основе данных."""
        if founder_data.get("ogrn"):
            return 2  # Российская организация
        return 1  # Физическое лицо

    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует информацию об учредителях в структурированный формат.
        """
        for record in data:
            founder = {
                "inn": self._safe_str(record["inn"]),
                "inn_founder": self._safe_str(record["inn_founder"]),
                "full_name": self._safe_str(record["full_name"]),
                "ogrn": self._safe_str(record["ogrn"]),
                "kpp": self._safe_str(record["kpp"]),
                "is_inaccurate": bool(record["is_inaccurate"]),
                "reason": self._safe_str(record["reason"]),
                "founder_type_id": self._get_founder_type_id(record)
            }

            yield founder