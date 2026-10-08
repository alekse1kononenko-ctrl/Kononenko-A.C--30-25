"""Проверки параметров, стартового скрипта и кодов завершения."""

import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

from src.main import main, read_settings
from src.shell import run_script
from tests.helpers import make_shell


def test_parameters():
    """Пути с пробелами передаются в настройки без изменений."""
    settings = read_settings(["--vfs", "a b.zip", "--script", "c d.txt"])
    assert settings.vfs == "a b.zip"
    assert settings.script == "c d.txt"


def test_missing_required():
    """Без пути VFS argparse завершает запуск с кодом 2."""
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            read_settings([])
        except SystemExit as error:
            assert error.code == 2
        else:
            raise AssertionError("Ожидалась ошибка параметров")


def test_stop_on_first_error():
    """Команда после ошибки не выполняется; вывод содержит номер строки."""
    shell, output = make_shell()
    with TemporaryDirectory() as directory:
        path = Path(directory) / "start.txt"
        path.write_text("\nunknown\nexit\n", encoding="utf-8")
        assert not run_script(shell, path)
    assert shell["running"]
    assert not any("$ exit" in line for line in output)
    assert output[-1] == "Скрипт остановлен: строка 2"


def test_script_file_missing():
    """Отсутствующий скрипт дает понятную ошибку."""
    shell, output = make_shell()
    with TemporaryDirectory() as directory:
        assert not run_script(shell, Path(directory) / "missing.txt")
    assert "Ошибка стартового скрипта" in output[0]


def test_script_dialog_and_exit():
    """Скрипт показывает ввод и вывод; строки после exit пропускаются."""
    shell, output = make_shell()
    with TemporaryDirectory() as directory:
        path = Path(directory) / "start.txt"
        path.write_text("\ufeffuname\nexit\nunknown\n", encoding="utf-8")
        assert run_script(shell, path)
    assert output == ["test:/$ uname", "UnixEmulator", "test:/$ exit"]
    assert not shell["running"]


def test_main_success_and_error_codes():
    """Загрузка, ошибка команды и отсутствие ZIP дают ожидаемые коды."""
    with TemporaryDirectory() as directory:
        archive = Path(directory) / "vfs.zip"
        script = Path(directory) / "script.txt"
        with ZipFile(archive, "w") as target:
            target.writestr("hello.txt", "Hello")
        script.write_text("cat hello.txt\nexit\n", encoding="utf-8")
        argv = ["--vfs", str(archive), "--script", str(script)]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert main(argv) == 0
            script.write_text("unknown\nexit\n", encoding="utf-8")
            assert main(argv) == 1
            assert main(["--vfs", str(archive) + ".missing"]) == 1
        assert "Конфигурация: VFS =" in output.getvalue()
        assert "Конфигурация: скрипт =" in output.getvalue()
        assert "Hello" in output.getvalue()


def test_script_without_exit_enters_repl():
    """Успешный скрипт без exit передает управление чтению с клавиатуры."""
    with TemporaryDirectory() as directory:
        archive = Path(directory) / "vfs.zip"
        script = Path(directory) / "script.txt"
        with ZipFile(archive, "w"):
            pass
        script.write_text("uname\n", encoding="utf-8")
        with patch("builtins.input", return_value="exit") as read_input:
            with contextlib.redirect_stdout(io.StringIO()):
                argv = ["--vfs", str(archive), "--script", str(script)]
                assert main(argv) == 0
        read_input.assert_called_once_with("vfs:/$ ")
