"""Проверки базового диалога."""

import unittest
from src.shell import Shell


class ShellTests(unittest.TestCase):
    """Проверяет ошибки, приглашение и завершение сессии."""

    def setUp(self):
        """Перехватывает вывод, не меняя системную консоль."""
        self.output = []
        self.shell = Shell("demo", write=self.output.append)

    def test_prompt(self):
        """В приглашении присутствует имя VFS."""
        self.assertEqual(self.shell.prompt, "demo:/$ ")

    def test_unknown_and_parser_error(self):
        """Ошибки не прекращают интерактивную сессию."""
        self.assertFalse(self.shell.execute("unknown"))
        self.assertFalse(self.shell.execute('ls "'))
        self.assertTrue(self.shell.running)

    def test_exit(self):
        """Команда exit прекращает работу без аргументов."""
        self.assertFalse(self.shell.execute("exit extra"))
        self.assertTrue(self.shell.execute("exit"))
        self.assertFalse(self.shell.running)

    def test_stubs(self):
        """Заглушки выводят название и разобранные аргументы."""
        self.assertTrue(self.shell.execute("ls a b"))
        self.assertEqual(self.output[-1], "ls: аргументы = ['a', 'b']")
        self.assertTrue(self.shell.execute("cd /home"))
