import datetime
from typing import Generator, Dict, Any

from pipelines.components.transformers.transformer import Transformer


class DadataBronzeTransformer(Transformer):
    def transform(
        self, data: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Преобразует сырые данные от экстрактора в финальный формат для загрузки в MongoDB.
        Добавляет служебное поле created_at.
        """
        now = datetime.datetime.utcnow().isoformat()
        
        for record in data:
            yield {
                "inn": record["inn"],
                "ogrn": record["ogrn"],
                "data": record["data"],
                "created_at": now
            }