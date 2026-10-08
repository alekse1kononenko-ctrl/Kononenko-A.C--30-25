"""Простые функции команд: состояние сессии передается словарем."""

import base64

from .vfs import check_directory, list_path, read_file, remove_file
from .vfs import resolve_path

UNIX_NAME = "UnixEmulator"
CLEAR_SEQUENCE = "\033[2J\033[H"
ONE_PATH = 1


def no_options(arguments, command):
    """Проверяет отсутствие опций, например ls -l или rm -r."""
    for argument in arguments:
        if argument.startswith("-"):
            raise ValueError(f"{command}: опции не поддерживаются")


def list_command(shell, arguments):
    """Печатает содержимое текущей папки или указанных путей."""
    no_options(arguments, "ls")
    paths = arguments or [shell["cwd"]]
    for argument in paths:
        path = resolve_path(argument, shell["cwd"])
        if len(paths) > ONE_PATH:
            shell["write"](f"{argument}:")
        shell["write"]("  ".join(list_path(shell["vfs"], path)))


def cd_command(shell, arguments):
    """Меняет текущую папку; без аргумента переходит в корень VFS."""
    no_options(arguments, "cd")
    if len(arguments) > ONE_PATH:
        raise ValueError("cd: требуется не более одного пути")
    path = arguments[0] if arguments else "/"
    path = resolve_path(path, shell["cwd"])
    check_directory(shell["vfs"], path)
    shell["cwd"] = path


def cat_command(shell, arguments):
    """Печатает текст файлов, двоичные данные показывает как base64."""
    no_options(arguments, "cat")
    if not arguments:
        raise ValueError("cat: укажите хотя бы один файл")
    for argument in arguments:
        path = resolve_path(argument, shell["cwd"])
        data = read_file(shell["vfs"], path)
        try:
            text = data.decode("utf-8")
            if "\x00" in text:
                raise UnicodeError("двоичный файл")
        except UnicodeError:
            text = "base64: " + base64.b64encode(data).decode("ascii")
        shell["write"](text.rstrip("\n"))


def uname_command(shell, arguments):
    """Печатает имя эмулируемой системы."""
    if arguments:
        raise ValueError("uname: аргументы не поддерживаются")
    shell["write"](UNIX_NAME)


def clear_command(shell, arguments):
    """Очищает экран с помощью ANSI-последовательности терминала."""
    if arguments:
        raise ValueError("clear: аргументы не поддерживаются")
    shell["write"](CLEAR_SEQUENCE)


def rm_command(shell, arguments):
    """Удаляет один или несколько файлов только из памяти сессии."""
    no_options(arguments, "rm")
    if not arguments:
        raise ValueError("rm: укажите хотя бы один файл")
    for argument in arguments:
        path = resolve_path(argument, shell["cwd"])
        remove_file(shell["vfs"], path)
