import rarfile
import docx
from pathlib import Path
import logging
import tempfile
import shutil
from typing import List, Dict, Tuple

from pipelines.components.connectors.rosstat_okved_connector import RosstatOkvedConnector
from pipelines.components.extractors.extractor import Extractor


class OkvedGoldExtractor(Extractor):
    """
    Распаковывает архив и извлекает IT-релевантные коды ОКВЭД/ОКПД2 (разделы 62 и 63).
    """

    def __init__(self, connector: RosstatOkvedConnector):
        self.connector = connector

    def extract(self) -> Tuple[List[Dict[str, str]], bool]:
        logging.info("🚀 Запуск экстрактора ОКВЭД/ОКПД2...")

        archive_path = self.connector.download_okved_archive()

        okveds = self._parse_docx_from_rar(archive_path)

        return okveds, True


    def _parse_docx_from_rar(self, archive_path: str) -> List[Dict[str, str]]:
        it_codes = []
        
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                logging.info(f"Распаковка архива во временную папку: {tmp_dir}")
                with rarfile.RarFile(archive_path, "r") as rf:
                    rf.extractall(path=tmp_dir)

                docx_paths = list(Path(tmp_dir).rglob("*.docx"))
                logging.info(f"Найдено .docx файлов: {len(docx_paths)}")

                for docx_path in docx_paths:
                    logging.info(f"📄 Обработка: {docx_path.name}")
                    try:
                        if docx_path.stat().st_size < 1024:
                            logging.warning(f"Файл {docx_path.name} слишком мал — пропускаем")
                            continue

                        doc = docx.Document(docx_path)
                        
                        for table in doc.tables:
                            for row in table.rows:
                                if len(row.cells) > 0:
                                    code_cell = row.cells[0].text.strip()
                                    if self._is_valid_okpd_code(code_cell):
                                        if code_cell.startswith("62") or code_cell.startswith("63"):
                                            if len(row.cells) > 1:
                                                description = row.cells[1].text.strip()
                                                description = description.split("Эта группировка")[0].strip()
                                                it_codes.append({"code": code_cell, "name": description})
                                            
                    except Exception as e:
                        logging.error(f"Ошибка при парсинге {docx_path.name}: {e}")

        except rarfile.NotRarFile:
            raise ValueError("Файл не является RAR-архивом")
        except Exception as e:
            logging.error(f"Ошибка при работе с архивом: {e}")
            raise

        logging.info(f"✅ Найдено IT-кодов: {len(it_codes)}")
        return it_codes

    def _is_valid_okpd_code(self, s: str) -> bool:
        """Проверяет, соответствует ли строка формату кода ОКПД2/ОКВЭД и не является ли она заголовком раздела."""
        if not s or not s[0].isdigit():
            return False
        if s.endswith(".") or ".." in s:
            return False
        parts = s.split(".")
        all_digits = all(part.isdigit() for part in parts)
        has_enough_parts = len(parts) >= 2
        return all_digits and has_enough_parts