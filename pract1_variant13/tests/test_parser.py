"""Проверки подстановки переменных, кавычек и ошибок разбора."""

from unittest.mock import patch

from src.parser import parse_command
from tests.helpers import expect_error


def test_environment():
    """Переменная в двойных кавычках сохраняет путь с пробелом."""
    assert parse_command('ls "$HOME"', {"HOME": "/a b"}) == ["ls", "/a b"]


def test_real_environment():
    """По умолчанию значения читаются из окружения реального процесса."""
    with patch.dict("os.environ", {"PR13_TEST": "/docs"}):
        assert parse_command("cd $PR13_TEST") == ["cd", "/docs"]


def test_single_quotes_and_escaping():
    """Одинарные кавычки и обратная косая черта сохраняют доллар."""
    result = parse_command(r"ls '$HOME' \$HOME", {"HOME": "/x"})
    assert result == ["ls", "$HOME", "$HOME"]


def test_braces_and_unknown():
    """Раскрывается ${NAME}; неизвестное имя заменяется пустой строкой."""
    result = parse_command('cd "${HOME}" "$UNKNOWN"', {"HOME": "/"})
    assert result == ["cd", "/", ""]
    assert parse_command("ls $UNKNOWN", {}) == ["ls"]


def test_splitting():
    """Без кавычек пробелы в значении разделяют аргументы."""
    for value in ["one two", " one two ", "one\ttwo"]:
        assert parse_command("ls $ITEMS", {"ITEMS": value}) == [
            "ls", "one", "two",
        ]


def test_malformed():
    """Незакрытые кавычки, скобки и неверные имена дают ошибку."""
    for line in ['ls "abc', "ls ${HOME", "ls \\", "ls ${1}"]:
        expect_error(parse_command, line)


def test_variable_value_is_not_syntax():
    """Кавычки и доллар из значения не становятся синтаксисом команды."""
    value = "a'\"\\$OTHER b"
    result = parse_command('cat "$ITEM"', {"ITEM": value})
    assert result == ["cat", value]
    result = parse_command("cat $ITEM", {"ITEM": value})
    assert result == ["cat", "a'\"\\$OTHER", "b"]


def test_empty_input_and_quoted_words():
    """Пустой ввод, пустые кавычки и части одного слова сохраняются."""
    assert parse_command("   ") == []
    assert parse_command('cat ""') == ["cat", ""]
    assert parse_command('cat a" b"c') == ["cat", "a bc"]
    assert parse_command('cat before${X}after', {"X": " middle "}) == [
        "cat", "before", "middle", "after",
    ]
