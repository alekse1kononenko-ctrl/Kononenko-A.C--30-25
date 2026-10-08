"""ZIP хранится в памяти: словарь файлов и множество каталогов."""

import base64
import posixpath
from zipfile import BadZipFile, ZipFile


def resolve_path(path, cwd="/"):
    """Превращает относительный путь в абсолютный, учитывает . и .."""
    if not path:
        raise ValueError("пустой путь")
    path = posixpath.join(cwd, path)
    return "/" + posixpath.normpath(path).lstrip("/")


def add_entry(vfs, archive, item):
    """Добавляет файл или каталог ZIP вместе с родительскими папками."""
    name = item.filename
    if name.startswith("/") or ".." in name.split("/") or "\\" in name:
        raise ValueError("VFS: недопустимый путь в ZIP")
    path = resolve_path(name)
    if path in vfs["files"]:
        raise ValueError("VFS: конфликт путей в ZIP")
    if not item.is_dir() and path in vfs["directories"]:
        raise ValueError("VFS: конфликт путей в ZIP")
    parent = posixpath.dirname(path)
    while parent != "/":
        if parent in vfs["files"]:
            raise ValueError("VFS: файл использован как каталог")
        vfs["directories"].add(parent)
        parent = posixpath.dirname(parent)
    if item.is_dir():
        vfs["directories"].add(path)
    else:
        data = archive.read(item)
        vfs["files"][path] = base64.b64encode(data).decode("ascii")


def load_vfs(archive_path):
    """Читает ZIP без распаковки; файлы хранятся в формате base64."""
    vfs = {"files": {}, "directories": {"/"}}
    try:
        with ZipFile(archive_path) as archive:
            for item in archive.infolist():
                add_entry(vfs, archive, item)
    except FileNotFoundError as error:
        raise ValueError("VFS: файл не найден") from error
    except (BadZipFile, OSError, RuntimeError, NotImplementedError) as error:
        raise ValueError("VFS: неверный или недоступный ZIP") from error
    return vfs


def check_directory(vfs, path):
    """Сообщает об ошибке, если путь не является каталогом."""
    if path in vfs["files"]:
        raise ValueError(f"{path}: не является каталогом")
    if path not in vfs["directories"]:
        raise ValueError(f"{path}: путь не найден")


def check_file(vfs, path):
    """Сообщает об ошибке, если путь не является файлом."""
    if path in vfs["directories"]:
        raise ValueError(f"{path}: является каталогом")
    if path not in vfs["files"]:
        raise ValueError(f"{path}: файл не найден")


def list_path(vfs, path):
    """Возвращает имя файла или имена внутри указанного каталога."""
    if path in vfs["files"]:
        return [posixpath.basename(path)]
    check_directory(vfs, path)
    names = []
    for node in vfs["directories"] | vfs["files"].keys():
        if node != "/" and posixpath.dirname(node) == path:
            names.append(posixpath.basename(node))
    return sorted(names)


def read_file(vfs, path):
    """Получает исходные байты файла из строки base64 в памяти."""
    check_file(vfs, path)
    return base64.b64decode(vfs["files"][path])


def remove_file(vfs, path):
    """Удаляет запись словаря; исходный ZIP остается неизменным."""
    check_file(vfs, path)
    del vfs["files"][path]
