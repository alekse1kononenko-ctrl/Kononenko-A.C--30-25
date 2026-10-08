"""Подготовка данных и проверка ошибок без собственных классов."""

import base64

from src.shell import create_shell


def make_shell():
    """Готовит небольшую VFS и список для сбора вывода команд."""
    vfs = {
        "directories": {"/", "/docs", "/docs/a", "/empty", "/tmp"},
        "files": {},
    }
    entries = {
        "/docs/a/note.txt": b"Note\n",
        "/docs/file with spaces.txt": b"Space",
        "/f.txt": b"Text",
        "/binary.bin": b"\x00\xff",
        "/tmp/a.txt": b"A",
        "/tmp/b.txt": b"B",
    }
    for path, data in entries.items():
        vfs["files"][path] = base64.b64encode(data).decode("ascii")
    output = []
    return create_shell("test", vfs, output.append), output


def expect_error(function, *arguments):
    """Проверяет ValueError, возвращает текст возникшей ошибки."""
    try:
        function(*arguments)
    except ValueError as error:
        return str(error)
    raise AssertionError("Ожидалась ошибка ValueError")
