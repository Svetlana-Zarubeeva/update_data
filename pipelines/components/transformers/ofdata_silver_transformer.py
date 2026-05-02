from typing import Any, Dict, Generator, Optional
import datetime
import json
import logging

from pipelines.components.transformers.transformer import Transformer


class SilverTransformer(Transformer):
    """Преобразование сырых данных в структурированный вид"""
    
    def transform(self, data: Generator[Dict[str, Any], None, None]) -> Generator[Dict[str, Any], None, None]:
        now_iso = datetime.datetime.utcnow().isoformat()
        processed_count = 0

        for item in data:
            try:
                company_data = item.get("data", {})
                
                inn = (
                    item.get("inn") or
                    company_data.get("ИНН") or
                    company_data.get("inn") or
                    company_data.get("INN")
                )
                if not inn:
                    logging.warning(f"⚠️ Skipping record with missing INN")
                    continue

                directors_raw = company_data.get("Руковод", [])
                founders_raw = company_data.get("Учред", {})

                transformed = {
                    "inn": inn,
                    "ogrn": company_data.get("ОГРН"),
                    "kpp": company_data.get("КПП"),
                    "short_name": company_data.get("НаимСокр"),
                    "full_name": company_data.get("НаимПолн"),
                    "reg_date": company_data.get("ДатаРег"),
                    "status": company_data.get("Статус"),
                    "region_code": item.get("region") or company_data.get("РегионКод"),
                    "address": company_data.get("ЮрАдрес"),
                    "okved_code": item.get("okved") or company_data.get("ОКВЭД"),
                    "okved_description": company_data.get("ОКВЭД"),
                    "directors": json.dumps(directors_raw, ensure_ascii=False),
                    "founders": json.dumps(founders_raw, ensure_ascii=False),
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }

                processed_count += 1
                yield transformed

            except Exception as e:
                logging.error(f"❌ Error transforming record: {e}")
                continue

        logging.info(f"📊 Transformation completed: {processed_count} records processed")