"""Проверки семантики с независимым чтением результата через tomllib."""

import math
import tomllib
import unittest

from src.errors import TranslationError
from src.evaluator import MAX_NESTING
from src.translator import translate


def convert(source):
    """Прочитать результат переводчика независимым TOML-парсером Python."""
    return tomllib.loads(translate(source))


class TranslationTests(unittest.TestCase):
    """Проверить значения, ссылки, вложенность и числовую диагностику."""

    def test_empty_document(self):
        """Пустой документ соответствует пустому TOML-документу."""
        self.assertEqual(translate("' no values"), "")

    def test_signed_numbers(self):
        """Сохранять числовые значения обоих знаков и отрицательный ноль."""
        result = convert("a: +12.5; b: -0.25; c: -0.0;")
        self.assertEqual(result, {"a": 12.5, "b": -0.25, "c": -0.0})
        self.assertEqual(math.copysign(1.0, result["c"]), -1.0)

    def test_unicode_digits(self):
        """Поддерживать десятичные цифры по регулярному выражению тетради."""
        self.assertEqual(convert("x: ١.٥;"), {"x": 1.5})

    def test_strings_round_trip(self):
        """Сохранять Unicode, переносы, кавычки, слеши и маркеры языка."""
        values = (
            "", "Привет 🌍", "line\nnext\tcolumn", '"quote" \\ path',
            "' <!-- --> $+ 1 2$ {} ;", "\x00\x08\x7f", "a\r\nb",
        )
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(convert(f"x: [[{value}]];"), {"x": value})

    def test_nested_mixed_arrays(self):
        """Сохранять пустые и разнотипные массивы на нескольких уровнях."""
        source = "x: {1.0, [[a]], {}, {2.0, {[[b]], -3.5}}};"
        expected = [1.0, "a", [], [2.0, ["b", -3.5]]]
        self.assertEqual(convert(source), {"x": expected})

    def test_all_operations(self):
        """Проверить порядок операндов всех пяти бинарных операций."""
        cases = (("+", 10.0), ("-", 6.0), ("*", 16.0),
                 ("/", 4.0), ("pow", 64.0))
        for operation, expected in cases:
            with self.subTest(operation=operation):
                source = f"x: ${operation} 8.0 2$;"
                self.assertEqual(convert(source), {"x": expected})

    def test_signed_and_fractional_operands(self):
        """Допускать знаки и дробные степени внутри выражений."""
        source = "x: $+ -3 +2$; y: $pow 9.0 0.5$; z: $pow 2 -2$;"
        self.assertEqual(convert(source), {"x": -1.0, "y": 3.0, "z": 0.25})

    def test_references_and_nested_expressions(self):
        """Вычислять вложенные выражения со ссылками в массивах."""
        source = "a: 2.0; b: $+ a 1$; c: {$* b $pow a 3$$, {$- 1 a$}};"
        self.assertEqual(convert(source), {"a": 2.0, "b": 3.0,
                                           "c": [24.0, [-1.0]]})

    def test_names_are_case_sensitive(self):
        """Имена из латинских букв различаются по регистру."""
        self.assertEqual(convert("a: 1.0; A: 2.0;"), {"a": 1.0, "A": 2.0})

    def test_constant_errors(self):
        """Отвергать повторы, ссылки вперед, на себя и неизвестные имена."""
        sources = (
            "x: 1.0; x: 2.0;", "x: $+ absent 1$;",
            "x: $+ y 1$; y: 2.0;", "x: $+ x 1$;",
        )
        for source in sources:
            with self.subTest(source=source):
                with self.assertRaises(TranslationError):
                    translate(source)

    def test_semantic_error_position(self):
        """Ссылка на неизвестное имя содержит точную позицию токена."""
        with self.assertRaises(TranslationError) as caught:
            translate("a: 1.0;\nb: $+ missing 1$;")
        self.assertEqual(caught.exception.line, 2)
        self.assertEqual(caught.exception.column, 7)

    def test_non_numeric_references(self):
        """Строки и массивы нельзя использовать в арифметике."""
        for value in ("[[text]]", "{1.0}"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(TranslationError, "числа"):
                    translate(f"a: {value}; x: $+ a 1$;")

    def test_arithmetic_errors(self):
        """Диагностировать деление на ноль и недопустимую степень."""
        expressions = ("$/ 1 0$", "$/ 1 -0.0$", "$pow -2 0.5$",
                       "$pow 0 -1$")
        for expression in expressions:
            with self.subTest(expression=expression):
                with self.assertRaises(TranslationError):
                    translate(f"x: {expression};")

    def test_overflow(self):
        """Отвергать бесконечные литералы и результаты, включая pow."""
        huge = "9" * 310 + ".0"
        large = "1" + "0" * 200 + ".0"
        sources = (f"x: {huge};", f"x: $* {large} {large}$;",
                   "x: $pow 10 10000$;")
        for source in sources:
            with self.subTest(source=source):
                with self.assertRaises(TranslationError):
                    translate(source)

    def test_nesting_limit(self):
        """Граничная глубина допустима, превышение дает понятную ошибку."""
        value = "{" * MAX_NESTING + "1.0" + "}" * MAX_NESTING
        self.assertIn("x", convert(f"x: {value};"))
        with self.assertRaisesRegex(TranslationError, "вложенность"):
            translate(f"x: {{{value}}};")

    def test_expression_nesting_limit(self):
        """Ограничивать также вложенные префиксные выражения."""
        value = "$+ 1 " * MAX_NESTING + "1" + "$" * MAX_NESTING
        self.assertEqual(convert(f"x: {value};"), {"x": MAX_NESTING + 1.0})
        with self.assertRaisesRegex(TranslationError, "вложенность"):
            translate(f"x: $+ 1 {value}$;")

    def test_isolated_documents(self):
        """Константы одного запуска не переходят в другой документ."""
        convert("a: 1.0;")
        with self.assertRaisesRegex(TranslationError, "Неизвестная"):
            translate("x: $+ a 1$;")

    def test_declaration_order(self):
        """Выходные ключи следуют порядку объявлений входного текста."""
        self.assertEqual(list(convert("z: 1.0; a: 2.0;")), ["z", "a"])
