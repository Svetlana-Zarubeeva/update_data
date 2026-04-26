import tarfile
import zipfile
from pathlib import Path

import py7zr


class FileFormatValidator:
    @staticmethod
    def is_zip_file(filepath: Path) -> bool:
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.testzip()

            return True
        except zipfile.BadZipFile:
            return False

    @staticmethod
    def is_tar_file(filepath: Path) -> bool:
        try:
            with tarfile.open(filepath, 'r') as tar_ref:
                tar_ref.getmembers()

            return True
        except tarfile.ReadError:
            return False

    @staticmethod
    def is_seven_zip_file(filepath: Path) -> bool:
        try:
            with py7zr.SevenZipFile(filepath, mode='r'):
                return True

        except py7zr.Bad7zFile:
            return False

    @staticmethod
    def is_compress_z_file(filepath: Path) -> bool:
        if str.join("", filepath.suffix) not in ('.z', '.taz', '.taz.old', '.tar.z'):
            return False

        try:
            with open(filepath, 'rb') as f:
                header = f.read(2)
                return header in (b'\x1F\x9D', b'\x1F\x8B')
        except:
            return False
