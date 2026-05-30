import datetime
import logging
import uuid
from typing import Any, Dict, Generator

from pipelines.components.transformers.transformer import Transformer


class CheckoBronzeTransformer(Transformer):
    """Преобразует сырые данные из checko.ru в унифицированную структуру для хранения в MongoDB."""

    def transform(self, data: Generator[Dict[str, Any], None, None]) -> Generator[Dict[str, Any], None, None]:
        now_iso = datetime.datetime.utcnow().isoformat()
        processed_count = 0

        for item in data:
            try:
                if not isinstance(item, dict):
                    logging.warning(f"⚠️ Skipping non-dict item: {type(item)}")
                    continue

                raw_data = item.get("data", {})
                metadata = item.get("metadata", {})

                if not isinstance(raw_data, dict):
                    logging.warning(f"⚠️ 'data' is not a dict: {type(raw_data)}")
                    raw_data = {}

                if not raw_data:
                    continue
                
                inn = raw_data.get("inn")
                
                if not inn:
                    inn = f"NO_INN_{uuid.uuid4()}"
                
                transformed_item = {
                    "data": raw_data,
                    "inn": inn,
                    "ogrn": raw_data.get("ogrn"),
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