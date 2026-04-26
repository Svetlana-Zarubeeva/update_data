"""
Модуль распаковки архивов
"""

import subprocess
import zipfile
import logging
from pathlib import Path
from typing import Optional, List
from py7zr import py7zr


def unzip_zip(path: Path, to_directory: Optional[Path] = None, each_file: bool = False) -> List[Path]:
    """
    Распаковка zip архива с помощью библиотеки python

    :param path: Путь к архиву
    :param to_directory: Директория, в которую нужно распаковать архив
    :param each_file: Распаковка каждого файла отдельно, файлы которые не может распаковать - пропускает
    """
    if to_directory is None:
        to_directory = path.parent

    try:
        with zipfile.ZipFile(path, 'r') as zip_ref:
            files = [zip_file.filename for zip_file in zip_ref.infolist()]
            if each_file:
                files_to_delete = []
                for file in files:
                    try:
                        zip_ref.extract(file, to_directory)
                    except zipfile.BadZipfile:
                        files_to_delete.append(file)

                for file in files_to_delete:
                    files.remove(file)
            else:
                zip_ref.extractall(to_directory)

            return [to_directory / Path(file) for file in files]
    except Exception as ex:
        logging.error("Something went wrong with archives: `%s`. Error: `%s`.", path, str(ex), exc_info=ex)
        raise ex


def unzip_tar(path: Path, to_directory: Optional[Path] = None) -> List[Path]:
    """
    Распаковка tar архива с помощью tar команды linux.

    :param path: Путь к архиву
    :param to_directory: Директория, в которую нужно распаковать архив
    """
    if to_directory is None:
        to_directory = path.parent

    try:
        list_process = subprocess.run(['tar', '-tf', str(path)], capture_output=True, text=True, check=True)
        file_list_str = list_process.stdout

        subprocess.run(['tar', '-C', str(to_directory), '-xvf', str(path)], check=True, capture_output=True)

        unpacked_paths = []
        for file_path in file_list_str.strip().split("\n"):
            full_path = to_directory / file_path
            if full_path.is_file():
                unpacked_paths.append(full_path)

    except subprocess.CalledProcessError as cpe:
        if ("gzip: stdin: not in gzip format" in cpe.stderr.strip()) and (path.suffix == ".taz"):
            path = path.rename(path.with_suffix(".tar"))
            return unzip_tar(path, to_directory)
        raise RuntimeError(f"Unzipping `{str(path)}` tar failed with error: `{cpe.stderr.strip()}`.")

    return unpacked_paths


def unzip_7zip(path: Path, to_directory: Optional[Path] = None) -> List[Path]:
    """
    Распаковка 7-Zip архива с помощью библиотеки python

    :param path: Путь к архиву
    :param to_directory: Директория, в которую нужно распаковать архив
    """
    if to_directory is None:
        to_directory = path.parent

    with py7zr.SevenZipFile(path, mode='r') as archive:
        archive.extractall(path=to_directory)
        file_names = archive.getnames()

    return [to_directory / file_name for file_name in file_names]
