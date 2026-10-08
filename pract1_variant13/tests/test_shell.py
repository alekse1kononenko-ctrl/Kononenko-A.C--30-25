"""Проверки диалога, приглашения и завершения сессии."""

from unittest.mock import patch

from src.shell import execute, get_prompt, repl
from tests.helpers import make_shell


def test_prompt():
    """Приглашение содержит имя VFS и текущий путь."""
    shell, output = make_shell()
    assert get_prompt(shell) == "test:/$ "
    assert execute(shell, "cd /docs")
    assert get_prompt(shell) == "test:/docs$ "


def test_unknown_and_parser_error():
    """Ошибки разбора и команд не завершают интерактивную сессию."""
    shell, output = make_shell()
    assert not execute(shell, "unknown")
    assert not execute(shell, 'ls "')
    assert shell["running"]
    assert len(output) == 2


def test_exit():
    """exit без аргументов завершает сессию."""
    shell, output = make_shell()
    assert not execute(shell, "exit extra")
    assert shell["running"]
    assert execute(shell, "exit")
    assert not shell["running"]


def test_empty_command():
    """Пустая строка ничего не печатает и считается успешной."""
    shell, output = make_shell()
    assert execute(shell, "  ")
    assert output == []
    assert shell["running"]


def test_repl_continues_after_error():
    """После ошибочной команды пользователь может выполнить uname и exit."""
    shell, output = make_shell()
    with patch("builtins.input", side_effect=["unknown", "uname", "exit"]):
        repl(shell)
    assert "неизвестная команда" in output[0]
    assert output[-1] == "UnixEmulator"
    assert not shell["running"]


def test_repl_eof_and_interrupt():
    """Конец ввода завершает диалог, Ctrl+C позволяет продолжить ввод."""
    shell, output = make_shell()
    with patch("builtins.input", side_effect=[KeyboardInterrupt, EOFError]):
        repl(shell)
    assert output == [""]
