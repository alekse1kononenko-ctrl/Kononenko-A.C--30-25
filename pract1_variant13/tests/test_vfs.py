"""Проверки загрузки ZIP без извлечения и изменений на диске."""

import base64
import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from src.vfs import VirtualFileSystem


class VfsTests(unittest.TestCase):
    """Проверяет память, двоичные данные, пути и ошибки архива."""

    def setUp(self):
        """Создает временный ZIP и фиксирует исходный хеш."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "vfs.zip"
        with ZipFile(self.path, "w") as archive:
            archive.writestr("a/b/c/file.txt", "text")
            archive.writestr("binary.bin", bytes([0, 255, 128]))
            archive.writestr("empty/", "")
        self.before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.vfs = VirtualFileSystem.load(self.path)

    def test_three_levels(self):
        """Родительские каталоги создаются даже без ZIP-записей."""
        self.assertIn("/a/b/c", self.vfs.directories)
        self.assertEqual(self.vfs.list_path("/a/b/c"), ["file.txt"])

    def test_binary_base64(self):
        """Двоичные байты обратимо представлены строкой base64."""
        encoded = self.vfs.files["/binary.bin"]
        self.assertEqual(base64.b64decode(encoded), bytes([0, 255, 128]))

    def test_no_disk_modification(self):
        """После загрузки на диске остается только неизмененный ZIP."""
        after = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertEqual(after, self.before)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [self.path])

    def test_path_normalization(self):
        """Проверяет относительный путь и переход к родителю."""
        self.assertEqual(self.vfs.resolve("../c", "/a/b"), "/a/c")
        self.assertEqual(self.vfs.resolve("../../..", "/a"), "/")
        self.assertEqual(self.vfs.resolve("//a", "/"), "/a")

    def test_loading_errors(self):
        """Отсутствующий файл и обычный текст не принимаются как VFS."""
        with self.assertRaisesRegex(ValueError, "не найден"):
            VirtualFileSystem.load(self.path.with_name("missing.zip"))
        invalid = self.path.with_name("invalid.zip")
        invalid.write_text("invalid", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ZIP"):
            VirtualFileSystem.load(invalid)

    def test_invalid_archive_paths(self):
        """Архив с выходом за корень или конфликтом путей отклоняется."""
        for entries in [["../bad"], ["a", "a/file.txt"]]:
            with self.subTest(entries=entries):
                invalid = self.path.with_name("unsafe.zip")
                with ZipFile(invalid, "w") as archive:
                    for name in entries:
                        archive.writestr(name, "x")
                with self.assertRaises(ValueError):
                    VirtualFileSystem.load(invalid)
