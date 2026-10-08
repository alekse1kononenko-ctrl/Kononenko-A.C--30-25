"""Проверки удаления только в памяти текущей сессии."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from src.shell import Shell
from src.vfs import VirtualFileSystem


class RemoveTests(unittest.TestCase):
    """Проверяет исчезновение файла и сохранность источника VFS."""

    def setUp(self):
        """Создает архив с двумя файлами и каталогом."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "vfs.zip"
        with ZipFile(self.path, "w") as archive:
            archive.writestr("tmp/a.txt", "A")
            archive.writestr("tmp/b.txt", "B")
        self.output = []
        self.shell = Shell(
            "test", VirtualFileSystem.load(self.path), self.output.append,
        )

    def test_remove_and_archive_unchanged(self):
        """Удаление меняет VFS; байты архива не меняются."""
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertTrue(self.shell.execute("rm /tmp/a.txt"))
        self.assertNotIn("/tmp/a.txt", self.shell.vfs.files)
        self.assertFalse(self.shell.execute("cat /tmp/a.txt"))
        after = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertEqual(before, after)
        restored = VirtualFileSystem.load(self.path)
        self.assertEqual(restored.read_file("/tmp/a.txt"), b"A")

    def test_multiple_relative_files(self):
        """Можно удалить несколько файлов относительно cwd."""
        self.assertTrue(self.shell.execute("cd /tmp"))
        self.assertTrue(self.shell.execute("rm a.txt b.txt"))
        self.assertEqual(self.shell.vfs.list_path("/tmp"), [])

    def test_remove_errors(self):
        """rm отклоняет каталог, отсутствующий файл и неверный вызов."""
        for line in ["rm", "rm /tmp", "rm /missing", "rm -r /tmp"]:
            with self.subTest(line=line):
                self.assertFalse(self.shell.execute(line))
        self.assertEqual(len(self.shell.vfs.files), 2)
