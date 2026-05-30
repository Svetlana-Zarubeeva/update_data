from typing import Generator, Dict, Any
import datetime

from pipelines.components.transformers.transformer import Transformer


class OfdataGoldTransformer(Transformer):
    def _safe_str(self, value, default=""):
        return str(value) if value is not None else default

    def _safe_date(self, value):
        if value and isinstance(value, datetime.datetime):
            return value.date()
        return value

    def transform(self, data: Generator[Dict[str, Any], None, None]) -> Generator[Dict[str, Any], None, None]:
        for record in data:
            yield {
                "inn": self._safe_str(record["inn"]),
                "ogrn": self._safe_str(record["ogrn"]),
                "kpp": self._safe_str(record["kpp"]),
                "short_name": self._safe_str(record["short_name"]),
                "full_name": self._safe_str(record["full_name"]),
                "reg_date": self._safe_date(record["reg_date"]),
                "status": self._safe_str(record["status"], "UNKNOWN"),
                "okved_code": self._safe_str(record["okved_code"])
            }