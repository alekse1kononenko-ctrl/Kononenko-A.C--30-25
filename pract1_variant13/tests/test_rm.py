"""Проверки удаления файлов только в памяти текущей сессии."""

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from src.shell import create_shell, execute
from src.vfs import list_path, load_vfs, read_file
from tests.helpers import make_shell


def test_remove_and_archive_unchanged():
    """Удаление меняет словарь; повторная загрузка возвращает файл."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "vfs.zip"
        with ZipFile(path, "w") as archive:
            archive.writestr("tmp/a.txt", "A")
            archive.writestr("tmp/b.txt", "B")
        before = path.read_bytes()
        output = []
        shell = create_shell("test", load_vfs(path), output.append)
        assert execute(shell, "rm /tmp/a.txt")
        assert "/tmp/a.txt" not in shell["vfs"]["files"]
        assert not execute(shell, "cat /tmp/a.txt")
        assert path.read_bytes() == before
        assert list(Path(directory).iterdir()) == [path]
        assert read_file(load_vfs(path), "/tmp/a.txt") == b"A"


def test_multiple_relative_files():
    """Несколько файлов удаляются относительно текущей папки."""
    shell, output = make_shell()
    assert execute(shell, "cd /tmp")
    assert execute(shell, "rm a.txt b.txt")
    assert list_path(shell["vfs"], "/tmp") == []


def test_remove_errors():
    """rm отклоняет каталог, отсутствующий файл и неверный вызов."""
    shell, output = make_shell()
    before = shell["vfs"]["files"].copy()
    for line in ["rm", "rm /tmp", "rm /missing", "rm -r /tmp"]:
        assert not execute(shell, line), line
    assert shell["vfs"]["files"] == before


def test_multiple_files_stop_at_error():
    """Файлы обрабатываются слева направо до первой ошибки."""
    shell, output = make_shell()
    assert not execute(shell, "rm /tmp/a.txt /missing /tmp/b.txt")
    assert "/tmp/a.txt" not in shell["vfs"]["files"]
    assert "/tmp/b.txt" in shell["vfs"]["files"]
