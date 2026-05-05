from typing import Any, Dict, Generator, List, Optional
import datetime
import json
import re
import logging

from pipelines.components.transformers.transformer import Transformer


def parse_address(address_str: str) -> Dict[str, str]:
    """Разбивает адрес на составные части в соответствии с требованиями таблицы."""
    if not address_str:
        return {
            "index": "", 
            "region": "", 
            "city": "", 
            "street": "", 
            "house": "", 
            "full_address": ""
        }
    
    parts = [p.strip() for p in address_str.split(",") if p.strip()]
    
    region_parts = []
    for part in parts:
        if re.match(r'^\d{6}$', part) or any(x in part.lower() for x in ["область", "край", "республика"]):
            region_parts.append(part)
        else:
            break
    
    region = ", ".join(region_parts)
    remaining_parts = parts[len(region_parts):]
    
    city = ""
    for i, part in enumerate(remaining_parts):
        if any(x in part.lower() for x in ["г.", "город", "пос.", "с."]):
            city = part
            remaining_parts = remaining_parts[i+1:]
            break
    
    street_house = ", ".join(remaining_parts)
    house = ""
    house_keywords = ["д.", "дом", "кв.", "квартира", "стр.", "строение", "км", "ком."]
    for keyword in house_keywords:
        if keyword in street_house.lower():
            last_idx = street_house.lower().rfind(keyword)
            if last_idx != -1:
                house = street_house[last_idx:].strip()
                street = street_house[:last_idx].strip().rstrip(",")
                break
    else:
        street = street_house

    index = region.split(",")[0] if region and "," in region else ""

    return {
        "index": index,
        "region": region,
        "city": city,
        "street": street,
        "house": house,
        "full_address": address_str
    }


class GoldTransformer(Transformer):
    """Преобразует сырые данные в нормализованную структуру для Gold слоя"""
    
    def transform(self, data: Generator[Dict[str, Any], None, None]) -> Generator[Dict[str, Any], None, None]:
        now_iso = datetime.datetime.utcnow().isoformat()
        processed_count = 0

        for item in data:
            try:
                # Адрес
                address_data = parse_address(item.get("address", ""))

                # Директора
                directors_raw = item.get("directors", [])
                if isinstance(directors_raw, str):
                    directors_raw = json.loads(directors_raw) if directors_raw else []

                directors = []
                for d in directors_raw:
                    directors.append({
                        "legal_entity_inn": item["inn"],
                        "inn": d.get("ИНН"),
                        "full_name": d.get("ФИО"),
                        "position": d.get("НаимДолжн") or d.get("ВидДолжн") or "",
                        "is_disqualified": d.get("ДисквЛицо", False),
                        "is_inaccurate": d.get("Недост", False),
                        "reason": d.get("НедостОпис")
                    })

                # Учредители
                founders_raw = item.get("founders", {})
                if isinstance(founders_raw, str):
                    founders_raw = json.loads(founders_raw) if founders_raw else {}

                founders = []
                for founder_type_code, flist in founders_raw.items():
                    if not isinstance(flist, list):
                        continue
                    for f in flist:
                        founders.append({
                            "legal_entity_inn": item["inn"],
                            "founder_type_code": founder_type_code,
                            "inn": f.get("ИНН"),
                            "full_name": f.get("ФИО") or f.get("НаимПолн") or "",
                            "ogrn": f.get("ОГРН"),
                            "kpp": f.get("КПП"),
                            "is_inaccurate": f.get("Недост", False),
                            "reason": f.get("НедостОпис")
                        })

                # Юридическое лицо
                legal_entity = {
                    "inn": item["inn"],
                    "ogrn": item.get("ogrn"),
                    "kpp": item.get("kpp"),
                    "short_name": item.get("short_name", ""),
                    "full_name": item.get("full_name", ""),
                    "reg_date": item.get("reg_date"),
                    "status": item.get("status", ""),
                    "region_code": item.get("region_code", ""),
                    "address_id": None,
                    "okved_code": item.get("okved_code", ""),
                    "okved_description": item.get("okved_description", ""),
                    "created_at": now_iso,
                    "updated_at": now_iso
                }

                processed_count += 1
                yield {
                    "legal_entity": legal_entity,
                    "address": address_data,
                    "directors": directors,
                    "founders": founders
                }

            except Exception as e:
                logging.error(f"❌ Error transforming record INN={item.get('inn')}: {e}")
                continue

        logging.info(f"📊 Transformation completed: {processed_count} records processed")