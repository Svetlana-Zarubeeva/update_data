from typing import Any, Dict, Generator
import datetime
import logging
from pipelines.components.transformers.transformer import Transformer


class OfdataBronzeTransformer(Transformer):
    """Преобразует сырые данные в унифицированную структуру для хранения в MongoDB."""

    def transform(self, data: Generator[Dict[str, Any], None, None]) -> Generator[Dict[str, Any], None, None]:
        now_iso = datetime.datetime.utcnow().isoformat()
        processed_count = 0

        for item in data:
            try:
                if not isinstance(item, dict):
                    logging.warning(f"⚠️ Skipping non-dict item: {type(item)}")
                    continue

                company_data = item.get("data", {})
                metadata = item.get("metadata", {})

                if not isinstance(company_data, dict):
                    logging.warning(f"⚠️ 'data' is not a dict: {type(company_data)}")
                    company_data = {}

                if not company_data:
                    continue
                
                inn = company_data.get("ИНН") or company_data.get("inn") or company_data.get("INN")
                
                if not inn:
                    inn = f"NO_INN_{uuid.uuid4()}"
                
                transformed_item = {
                    "data": company_data,
                    "inn": inn,
                    "okved": metadata.get("okved"),
                    "region": metadata.get("region"),
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }

                processed_count += 1
                yield transformed_item

            except Exception as e:
                logging.error(f"❌ Error transforming record: {str(e)}")
                continue