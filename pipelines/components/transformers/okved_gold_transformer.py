import re
from typing import List, Dict, Tuple
from datetime import datetime

from pipelines.components.transformers.transformer import Transformer


class OkvedGoldTransformer(Transformer):
    """Приводит данные к единому формату и валидирует их."""

    def transform(self, data: Tuple[List[Dict[str, str]], bool]) -> Tuple[List[Dict], bool]:
        raw_okveds, success = data
        if not success:
            return [], False

        transformed = []
        for okved in raw_okveds:
            code = okved["code"].replace(" ", "")
            if not self._validate_okved_code(code):
                continue
                
            section = code.split(".")[0]
            transformed.append({
                "okved_code": code,
                "description": okved["name"].strip(),
                "section": section,
                "created_at": datetime.utcnow()
            })

        return transformed, True

    def _validate_okved_code(self, code: str) -> bool:
        return bool(re.match(r"^\d{2}(\.\d+)*$", code))