"""Проверки грамматики варианта 13 и диагностики синтаксиса."""

import unittest

from src.errors import TranslationError
from src.parser import parse


class ParserTests(unittest.TestCase):
    """Разбирать допустимые конструкции и отвергать иной синтаксис."""

    def test_empty_and_comments(self):
        """Пустой документ и оба вида комментариев допустимы."""
        for source in ("", "' comment", "<!-- multi\nline -->"):
            with self.subTest(source=source):
                self.assertFalse(parse(source).children)

    def test_numbers(self):
        """Распознавать числа со знаком и обязательной дробной частью."""
        for literal in ("0.0", "+12.5", "-0.25", "001.20", "١.٥"):
            with self.subTest(literal=literal):
                self.assertEqual(parse(f"x: {literal};").data, "start")

    def test_nested_values_and_expressions(self):
        """Разбирать вложенные массивы, строки и префиксные выражения."""
        source = "x: {[[Привет]], {}, {1.0, $+ 2 $pow 3 2$$}};"
        self.assertEqual(parse(source).data, "start")

    def test_comments_between_tokens(self):
        """Комментарии могут разделять токены объявления и выражения."""
        source = "x<!-- a -->: $+ ' b\n1 2$; ' eof"
        self.assertEqual(parse(source).data, "start")

    def test_comment_markers_inside_strings(self):
        """Маркеры комментариев внутри строки остаются частью токена."""
        tree = parse("x: [[' <!-- not a comment -->]];")
        token = tree.children[0].children[1].children[0]
        self.assertEqual(str(token), "[[' <!-- not a comment -->]]")

    def test_invalid_syntax(self):
        """Отклонять неверные имена, числа, разделители и выражения."""
        sources = (
            "x: 1;", "x: .5;", "x: 5.;", "x: 1e3;", "x: 1.0",
            "x1: 1.0;", "x_y: 1.0;", "имя: 1.0;", "x: 'text';",
            "x: {1.0 2.0};", "x: {1.0,};", "x: [1.0];",
            "x: [[unclosed;", "<!-- unclosed", "x: 1.0; garbage",
            "x: $+ 1$;", "x: $+ 1 2 3$;", "x: $mod 1 2$;",
            "x: name;", "x: $name$;", "x: $pow(2, 3)$;",
        )
        for source in sources:
            with self.subTest(source=source):
                with self.assertRaises(TranslationError):
                    parse(source)

    def test_error_position(self):
        """Синтаксическая ошибка содержит строку, столбец и указатель."""
        with self.assertRaises(TranslationError) as caught:
            parse("x: 1.0;\ny: @;")
        self.assertEqual(caught.exception.line, 2)
        self.assertEqual(caught.exception.column, 4)
        self.assertIn("^", str(caught.exception))
