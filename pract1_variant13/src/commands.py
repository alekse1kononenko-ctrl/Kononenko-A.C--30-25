"""Команды эмулятора, работающие с виртуальными путями."""

import base64

UNIX_NAME = "UnixEmulator"
CLEAR_SEQUENCE = "\033[2J\033[H"
MAX_CD_ARGUMENTS = 1


def no_options(arguments, command):
    """Отклоняет неподдерживаемые опции команды."""
    if any(argument.startswith("-") for argument in arguments):
        raise ValueError(f"{command}: опции не поддерживаются")


def list_command(shell, arguments):
    """Выводит файл или содержимое одного либо нескольких каталогов."""
    no_options(arguments, "ls")
    paths = arguments or [shell.cwd]
    for argument in paths:
        path = shell.vfs.resolve(argument, shell.cwd)
        if len(paths) > MAX_CD_ARGUMENTS:
            shell.write(f"{argument}:")
        shell.write("  ".join(shell.vfs.list_path(path)))


def cd_command(shell, arguments):
    """Меняет каталог; без аргумента переходит в виртуальный корень."""
    no_options(arguments, "cd")
    if len(arguments) > MAX_CD_ARGUMENTS:
        raise ValueError("cd: требуется не более одного пути")
    path = shell.vfs.resolve(arguments[0] if arguments else "/", shell.cwd)
    shell.vfs.require_directory(path)
    shell.cwd = path


def cat_command(shell, arguments):
    """Печатает текст файлов; двоичное содержимое выводит как base64."""
    no_options(arguments, "cat")
    if not arguments:
        raise ValueError("cat: укажите хотя бы один файл")
    for argument in arguments:
        path = shell.vfs.resolve(argument, shell.cwd)
        data = shell.vfs.read_file(path)
        try:
            text = data.decode("utf-8")
            if "\x00" in text:
                raise UnicodeError("двоичный файл")
        except UnicodeError:
            text = "base64: " + base64.b64encode(data).decode("ascii")
        shell.write(text.rstrip("\n"))


def uname_command(shell, arguments):
    """Возвращает имя эмулируемой системы."""
    if arguments:
        raise ValueError("uname: аргументы не поддерживаются")
    shell.write(UNIX_NAME)


def clear_command(shell, arguments):
    """Передает ANSI-последовательность очистки экрана терминалу."""
    if arguments:
        raise ValueError("clear: аргументы не поддерживаются")
    shell.write(CLEAR_SEQUENCE)


COMMANDS = {
    "ls": list_command,
    "cd": cd_command,
    "cat": cat_command,
    "uname": uname_command,
    "clear": clear_command,
}
