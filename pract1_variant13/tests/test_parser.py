"""Проверки подстановки переменных и ошибок разбора."""

import unittest
from src.parser import parse_command


class ParserTests(unittest.TestCase):
    """Проверяет правила чтения командной строки."""

    def test_environment(self):
        """Значение берется из переданного окружения."""
        self.assertEqual(
            parse_command('ls "$HOME"', {"HOME": "/a b"}),
            ["ls", "/a b"],
        )

    def test_single_quotes_and_escaping(self):
        """Одинарные кавычки и экранирование сохраняют доллар."""
        self.assertEqual(
            parse_command(r"ls '$HOME' \$HOME", {"HOME": "/x"}),
            ["ls", "$HOME", "$HOME"],
        )

    def test_braces_and_unknown(self):
        """Раскрывает скобочную запись и пустую переменную."""
        self.assertEqual(
            parse_command('cd "${HOME}" "$UNKNOWN"', {"HOME": "/"}),
            ["cd", "/", ""],
        )

    def test_splitting(self):
        """Без кавычек пробел разделяет значение на аргументы."""
        self.assertEqual(
            parse_command("ls $ITEMS", {"ITEMS": "one two"}),
            ["ls", "one", "two"],
        )

    def test_malformed(self):
        """Незакрытые кавычки и переменные дают ошибку."""
        for line in ['ls "abc', "ls ${HOME", "ls \\", "ls ${1}"]:
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_command(line)
