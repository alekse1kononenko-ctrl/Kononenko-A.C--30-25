"""Два предметных примера и ошибочный ввод проверяются через переводчик."""

from pathlib import Path
import tomllib
import unittest

from src.errors import TranslationError
from src.translator import translate

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def load_example(name):
    """Перевести реальный файл примера и прочитать полученный TOML."""
    source = (EXAMPLES / name).read_text(encoding="utf-8")
    return tomllib.loads(translate(source))


class ExampleTests(unittest.TestCase):
    """Проверить рассчитанные параметры разных предметных областей."""

    def test_webserver(self):
        """Проверить вычисления и вложенные группы в конфигурации сервера."""
        result = load_example("webserver.conf")
        self.assertEqual(result["timeout"], 10.0)
        self.assertEqual(result["retry"], 3.5)
        self.assertEqual(result["budget"], 7.5)
        self.assertEqual(result["share"], 2.5)
        self.assertEqual(result["capacity"], 16.0)
        self.assertEqual(result["groups"], [["api", "admin"], ["static"], []])

    def test_greenhouse(self):
        """Проверить вложенные выражения и массивы расписания полива."""
        result = load_example("greenhouse.conf")
        self.assertEqual(result["average"], 21.0)
        self.assertEqual(result["delta"], 6.0)
        self.assertEqual(result["adjusted"], 17.5)
        self.assertEqual(result["interval"], 30.0)
        self.assertEqual(result["area"], 9.0)
        self.assertEqual(result["schedule"], [30.0, [12.0, 30.0], []])

    def test_invalid_example(self):
        """Ошибочный демонстрационный пример действительно не принимается."""
        source = (EXAMPLES / "invalid.conf").read_text(encoding="utf-8")
        with self.assertRaisesRegex(TranslationError, "Синтаксическая"):
            translate(source)
