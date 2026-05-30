from typing import Generator, Dict, Any, Optional
import json

from pipelines.components.transformers.transformer import Transformer


class ContactGoldTransformer(Transformer):
    """Преобразует контактные данные в структурированный формат для Gold-слоя."""
    
    def _prepare_json_field(self, value):
        """Подготавливает значение для сохранения в JSONB поле."""
        if value is None or value == {} or value == []:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, str):
            # Если строка похожа на JSON, попробуем распарсить и сохранить как JSON
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                return json.dumps([value], ensure_ascii=False)
        return json.dumps(value, ensure_ascii=False)

    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует контактные данные в структурированный формат для Gold-слоя.
        """
        for record in data:
            contact_info = {
                "legal_entity_id": record["legal_entity_id"],
                "phones": self._prepare_json_field(record.get("phones")),
                "emails": self._prepare_json_field(record.get("emails")),
                "websites": self._prepare_json_field(record.get("websites"))
            }
            
            yield contact_info