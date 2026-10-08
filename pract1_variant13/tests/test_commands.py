"""Проверки основных команд на небольшой VFS в памяти."""

from src.commands import CLEAR_SEQUENCE
from src.shell import execute
from tests.helpers import make_shell


def test_ls_directory_and_file():
    """ls поддерживает корень, файл и пустой каталог."""
    shell, output = make_shell()
    assert execute(shell, "ls")
    assert "docs" in output[-1]
    assert execute(shell, "ls /f.txt")
    assert output[-1] == "f.txt"
    assert execute(shell, "ls /empty")
    assert output[-1] == ""


def test_ls_multiple_paths():
    """При нескольких путях ls печатает подписи и списки файлов."""
    shell, output = make_shell()
    assert execute(shell, "ls /f.txt /empty")
    assert output == ["/f.txt:", "f.txt", "/empty:", ""]


def test_cd_paths():
    """cd поддерживает абсолютные пути, относительные пути, . и .."""
    shell, output = make_shell()
    cases = [
        ("cd /docs", "/docs"), ("cd a", "/docs/a"),
        ("cd .", "/docs/a"), ("cd ..", "/docs"), ("cd", "/"),
    ]
    for line, expected in cases:
        assert execute(shell, line)
        assert shell["cwd"] == expected


def test_cat_text_and_binary():
    """cat читает несколько файлов и показывает двоичные данные."""
    shell, output = make_shell()
    assert execute(shell, "cat /f.txt /docs/a/note.txt")
    assert output == ["Text", "Note"]
    assert execute(shell, "cat /binary.bin")
    assert output[-1] == "base64: AP8="


def test_quoted_file_path():
    """Кавычки позволяют читать файл с пробелами в имени."""
    shell, output = make_shell()
    assert execute(shell, 'cat "/docs/file with spaces.txt"')
    assert output == ["Space"]


def test_uname_and_clear():
    """uname возвращает имя системы, clear отправляет ANSI-код."""
    shell, output = make_shell()
    assert execute(shell, "uname")
    assert output[-1] == "UnixEmulator"
    assert execute(shell, "clear")
    assert output[-1] == CLEAR_SEQUENCE


def test_command_errors():
    """Ошибочные пути и аргументы дают неуспешный результат."""
    shell, output = make_shell()
    lines = [
        "ls /missing", "ls -x", "cd /f.txt", "cd /missing",
        "cd /docs /empty", "cat", "cat /docs", "cat /missing",
        "uname extra", "clear extra",
    ]
    for line in lines:
        assert not execute(shell, line), line
    assert shell["cwd"] == "/"


def test_sessions_are_independent():
    """Переход в каталог и удаление в одной сессии не меняют другую."""
    first, first_output = make_shell()
    second, second_output = make_shell()
    assert execute(first, "cd /docs")
    assert execute(first, "rm /f.txt")
    assert second["cwd"] == "/"
    assert execute(second, "cat /f.txt")
    assert second_output == ["Text"]
