import requests
from abc import ABC
from tqdm import tqdm
import os
import logging

from pipelines.components.connectors.connector import Connector
from settings import OKVED_DOWNLOAD_URL, storage_path


class OkvedConnector(Connector, ABC):
    """
    Скачивает ZIP-архив с JSON-файлом ОКВЭД.
    """
    def __init__(self):
        self.url = OKVED_DOWNLOAD_URL
        self.local_path = os.path.join(storage_path, "okved_2.json.zip")

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def download_okved_archive(self) -> str:
        """Скачивает ZIP-архив и возвращает путь к нему."""
        logging.info(f"📥 Скачивание архива ОКВЭД с {self.url}")
        
        response = requests.get(self.url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(self.local_path, "wb") as f, tqdm(
            total=total_size, unit='B', unit_scale=True, desc="OKVED Archive"
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
                
        logging.info(f"✅ Архив сохранён: {self.local_path}")
        return self.local_path