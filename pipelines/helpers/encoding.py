"""
Модуль для определения кодировки файла.
"""

from pathlib import Path
import chardet


def get_encoding(path: Path) -> str:
    """
    Определение кодировки файла
    :param path: путь до файла
    """
    with open(path, 'rb') as f:
        raw_data = b''.join([f.readline() for _ in range(256)])
    return chardet.detect(raw_data)['encoding']
