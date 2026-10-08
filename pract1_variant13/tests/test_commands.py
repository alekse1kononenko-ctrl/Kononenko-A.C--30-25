"""Проверки основных команд на независимой VFS в памяти."""

import base64
import unittest
from src.commands import CLEAR_SEQUENCE
from src.shell import Shell
from src.vfs import VirtualFileSystem


class CommandsTests(unittest.TestCase):
    """Проверяет пути, чтение текста и обработку аргументов."""

    def setUp(self):
        """Создает файлы непосредственно в модели VFS."""
        vfs = VirtualFileSystem()
        vfs.directories.update({"/docs", "/docs/a", "/empty"})
        entries = {"/docs/a/note.txt": b"Note\n", "/f.txt": b"Text"}
        entries["/binary.bin"] = bytes([0, 255])
        for path, data in entries.items():
            vfs.files[path] = base64.b64encode(data).decode("ascii")
        self.output = []
        self.shell = Shell("test", vfs, self.output.append)

    def test_ls_directory_and_file(self):
        """ls поддерживает корень, файл и пустой каталог."""
        self.assertTrue(self.shell.execute("ls"))
        self.assertIn("docs", self.output[-1])
        self.assertTrue(self.shell.execute("ls /f.txt"))
        self.assertEqual(self.output[-1], "f.txt")
        self.assertTrue(self.shell.execute("ls /empty"))
        self.assertEqual(self.output[-1], "")

    def test_cd_paths(self):
        """cd поддерживает абсолютные и относительные пути, . и .."""
        for line, expected in [
            ("cd /docs", "/docs"), ("cd a", "/docs/a"),
            ("cd .", "/docs/a"), ("cd ..", "/docs"), ("cd", "/"),
        ]:
            self.assertTrue(self.shell.execute(line))
            self.assertEqual(self.shell.cwd, expected)

    def test_cat_text_and_binary(self):
        """cat читает несколько файлов и представляет двоичные байты."""
        self.assertTrue(self.shell.execute("cat /f.txt /docs/a/note.txt"))
        self.assertEqual(self.output, ["Text", "Note"])
        self.assertTrue(self.shell.execute("cat /binary.bin"))
        self.assertEqual(self.output[-1], "base64: AP8=")

    def test_uname_and_clear(self):
        """uname возвращает имя системы, clear отправляет ANSI-код."""
        self.assertTrue(self.shell.execute("uname"))
        self.assertEqual(self.output[-1], "UnixEmulator")
        self.assertTrue(self.shell.execute("clear"))
        self.assertEqual(self.output[-1], CLEAR_SEQUENCE)

    def test_command_errors(self):
        """Ошибочные пути и аргументы дают неуспешный результат."""
        for line in [
            "ls /missing", "ls -x", "cd /f.txt", "cd /missing",
            "cd /docs /empty", "cat", "cat /docs", "cat /missing",
            "uname extra", "clear extra",
        ]:
            with self.subTest(line=line):
                self.assertFalse(self.shell.execute(line))
        self.assertEqual(self.shell.cwd, "/")
