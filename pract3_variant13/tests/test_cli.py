"""Проверки стандартных потоков и настоящего запуска отдельного процесса."""

import io
from pathlib import Path
import subprocess
import sys
import tomllib
import unittest
from unittest.mock import Mock

from src.main import EXIT_ERROR, EXIT_SUCCESS, run

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARGUMENT_ERROR = 2


def invoke(source=b"", *arguments):
    """Запустить CLI отдельным процессом с байтовыми стандартными потоками."""
    return subprocess.run(
        [sys.executable, "-m", "src.main", *arguments], input=source,
        capture_output=True, cwd=PROJECT_ROOT, check=False,
    )


class CliTests(unittest.TestCase):
    """Проверить коды завершения, кодировку и отсутствие частичного вывода."""

    def test_standard_streams(self):
        """Успешный процесс пишет корректный TOML и не пишет диагностику."""
        result = invoke("name: [[Привет]]; x: $+ 1 2$;".encode())
        self.assertEqual(result.returncode, EXIT_SUCCESS)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(tomllib.loads(result.stdout.decode()),
                         {"name": "Привет", "x": 3.0})

    def test_no_partial_output(self):
        """Ошибка в конце документа оставляет stdout полностью пустым."""
        result = invoke(b"a: 1.0;\nx: $/ 1 0$;")
        self.assertEqual(result.returncode, EXIT_ERROR)
        self.assertEqual(result.stdout, b"")
        self.assertIn("Деление на ноль", result.stderr.decode())

    def test_syntax_error(self):
        """Синтаксическая ошибка выводится только в stderr с координатами."""
        result = invoke(b"a: 1.0;\nx: @;")
        self.assertEqual(result.returncode, EXIT_ERROR)
        self.assertEqual(result.stdout, b"")
        self.assertIn("Строка 2, столбец 4", result.stderr.decode())

    def test_invalid_utf8(self):
        """Неверный UTF-8 дает контролируемую ошибку без трассировки."""
        result = invoke(b"\xff")
        self.assertEqual(result.returncode, EXIT_ERROR)
        self.assertEqual(result.stdout, b"")
        self.assertIn("Ошибка ввода/вывода", result.stderr.decode())
        self.assertNotIn(b"Traceback", result.stderr)

    def test_string_line_endings(self):
        """CRLF внутри строки сохраняется при передаче через CLI."""
        result = invoke(b"x: [[a\r\nb]];\r\n")
        self.assertEqual(result.returncode, EXIT_SUCCESS)
        self.assertEqual(tomllib.loads(result.stdout.decode()),
                         {"x": "a\r\nb"})

    def test_empty_input(self):
        """Пустой stdin успешно дает пустой stdout."""
        result = invoke()
        self.assertEqual(result.returncode, EXIT_SUCCESS)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def test_help_and_version(self):
        """Справка и версия не требуют ввода конфигурации."""
        for argument in ("--help", "--version"):
            with self.subTest(argument=argument):
                result = invoke(b"", argument)
                self.assertEqual(result.returncode, EXIT_SUCCESS)
                self.assertTrue(result.stdout)
                self.assertEqual(result.stderr, b"")

    def test_unknown_argument(self):
        """Вариант 13 не принимает входной файл аргументом CLI."""
        result = invoke(b"", "--input", "file.conf")
        self.assertEqual(result.returncode, ARGUMENT_ERROR)
        self.assertEqual(result.stdout, b"")
        self.assertTrue(result.stderr)

    def test_io_error(self):
        """Сбой чтения потока превращается в сообщение и код ошибки."""
        source = Mock()
        source.read.side_effect = OSError("read error")
        output, errors = io.StringIO(), io.StringIO()
        code = run(source, output, errors)
        self.assertEqual(code, EXIT_ERROR)
        self.assertFalse(output.getvalue())
        self.assertIn("Ошибка ввода/вывода", errors.getvalue())
