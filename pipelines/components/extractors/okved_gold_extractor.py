import json
import zipfile
from pathlib import Path
import logging
import tempfile
from typing import List, Dict, Tuple

from pipelines.components.extractors.extractor import Extractor
from pipelines.components.connectors.okved_connector import OkvedConnector


class OkvedGoldExtractor(Extractor):
    """
    Распаковывает ZIP и извлекает IT-релевантные коды ОКВЭД (разделы 62 и 63).
    """

    def __init__(self, connector: OkvedConnector):
        self.connector = connector

    def extract(self) -> Tuple[List[Dict[str, str]], bool]:
        logging.info("🚀 Запуск экстрактора ОКВЭД...")
        archive_path = self.connector.download_okved_archive()
        okveds = self._parse_json_from_zip(archive_path)
        return okveds, True

    def _parse_json_from_zip(self, archive_path: str) -> List[Dict[str, str]]:
        it_codes = []
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                # Ищем единственный .json файл
                json_files = [f for f in zf.namelist() if f.endswith('.json')]
                if not json_files:
                    raise ValueError("В архиве не найдено JSON-файлов")
                json_file = json_files[0]
                logging.info(f"📄 Чтение JSON: {json_file}")

                with zf.open(json_file) as f:
                    data = json.load(f)

                # Предполагается, что данные — список словарей с ключами "code", "name"
                for item in data:
                    code = item.get("code", "").strip()
                    name = item.get("name", "").strip()
                    if code.startswith(("62", "63")):
                        it_codes.append({"code": code, "name": name})

        except Exception as e:
            logging.error(f"Ошибка при работе с ZIP-архивом: {e}")
            raise

        logging.info(f"✅ Найдено IT-кодов: {len(it_codes)}")
        return it_codes