"""Виртуальные пути и содержимое ZIP в оперативной памяти."""

import base64
import posixpath
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile


class VirtualFileSystem:
    """Хранит каталоги и файлы без распаковки на диск."""

    def __init__(self):
        """Корень существует даже в пустом архиве."""
        self.directories = {"/"}
        self.files = {}

    @classmethod
    def load(cls, archive_path):
        """Читает ZIP, сохраняет содержимое файлов в формате base64."""
        vfs = cls()
        try:
            with ZipFile(archive_path) as archive:
                for item in archive.infolist():
                    vfs.add_entry(item, archive)
        except FileNotFoundError as error:
            raise ValueError("VFS: файл не найден") from error
        except (BadZipFile, OSError, RuntimeError) as error:
            raise ValueError("VFS: неверный или недоступный ZIP") from error
        return vfs

    def add_entry(self, item, archive):
        """Добавляет один элемент и его родительские каталоги."""
        parts = PurePosixPath(item.filename).parts
        if (item.filename.startswith("/") or ".." in parts
                or "\\" in item.filename):
            raise ValueError("VFS: недопустимый путь в ZIP")
        path = self.resolve(item.filename, "/")
        is_directory = item.is_dir()
        if path in self.files or (not is_directory
                                  and path in self.directories):
            raise ValueError("VFS: конфликт путей в ZIP")
        parent = posixpath.dirname(path)
        while parent != "/":
            if parent in self.files:
                raise ValueError("VFS: файл использован как каталог")
            self.directories.add(parent)
            parent = posixpath.dirname(parent)
        if is_directory:
            self.directories.add(path)
        else:
            data = archive.read(item)
            self.files[path] = base64.b64encode(data).decode("ascii")

    def resolve(self, path, cwd):
        """Нормализует абсолютный или относительный виртуальный путь."""
        if not path:
            raise ValueError("пустой путь")
        joined = path if path.startswith("/") else cwd + "/" + path
        # Один начальный слеш не допускает особого значения // в POSIX.
        return "/" + posixpath.normpath(joined).lstrip("/")

    def require_directory(self, path):
        """Проверяет, что виртуальный путь обозначает каталог."""
        if path in self.files:
            raise ValueError(f"{path}: не является каталогом")
        if path not in self.directories:
            raise ValueError(f"{path}: путь не найден")

    def list_path(self, path):
        """Возвращает файл либо имена непосредственных потомков."""
        if path in self.files:
            return [posixpath.basename(path)]
        self.require_directory(path)
        nodes = self.directories | self.files.keys()
        return sorted(
            posixpath.basename(node) for node in nodes
            if node != "/" and posixpath.dirname(node) == path
        )

    def read_file(self, path):
        """Восстанавливает исходные байты из хранимого base64."""
        if path in self.directories:
            raise ValueError(f"{path}: является каталогом")
        if path not in self.files:
            raise ValueError(f"{path}: файл не найден")
        return base64.b64decode(self.files[path])


    def remove_file(self, path):
        """Удаляет файл из словаря, не открывая исходный ZIP на запись."""
        if path in self.directories:
            raise ValueError(f"{path}: является каталогом")
        if path not in self.files:
            raise ValueError(f"{path}: файл не найден")
        # Изменяется только объект VFS текущей сессии.
        del self.files[path]
