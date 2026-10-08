"""Диалог и стартовый скрипт; состояние оболочки хранится в словаре."""

from .commands import cat_command, cd_command, clear_command
from .commands import list_command, rm_command, uname_command
from .parser import parse_command


def create_shell(name, vfs, write=print):
    """Создает сессию; write позволяет тестам собирать строки вывода."""
    return {
        "name": name,
        "vfs": vfs,
        "cwd": "/",
        "running": True,
        "write": write,
    }


def get_prompt(shell):
    """Возвращает приглашение с именем VFS и текущей папкой."""
    return f"{shell['name']}:{shell['cwd']}$ "


def run_command(shell, command, arguments):
    """Выбирает команду через обычные if и elif."""
    if command == "ls":
        list_command(shell, arguments)
    elif command == "cd":
        cd_command(shell, arguments)
    elif command == "uname":
        uname_command(shell, arguments)
    elif command == "cat":
        cat_command(shell, arguments)
    elif command == "clear":
        clear_command(shell, arguments)
    elif command == "rm":
        rm_command(shell, arguments)
    elif command == "exit":
        if arguments:
            raise ValueError("exit: аргументы не поддерживаются")
        shell["running"] = False
    else:
        raise ValueError(f"неизвестная команда: {command}")


def execute(shell, line):
    """Разбирает строку, выполняет команду и сообщает об ошибке."""
    try:
        words = parse_command(line)
        if words:
            run_command(shell, words[0], words[1:])
        return True
    except (ValueError, OSError) as error:
        shell["write"](f"Ошибка: {error}")
        return False


def run_script(shell, path):
    """Показывает команды скрипта, останавливается на первой ошибке."""
    try:
        with open(path, encoding="utf-8-sig") as script:
            for number, line in enumerate(script, start=1):
                line = line.rstrip("\r\n")
                if not line.strip():
                    continue
                shell["write"](get_prompt(shell) + line)
                if not execute(shell, line):
                    shell["write"](f"Скрипт остановлен: строка {number}")
                    return False
                if not shell["running"]:
                    break
        return True
    except (OSError, UnicodeError) as error:
        shell["write"](f"Ошибка стартового скрипта: {error}")
        return False


def repl(shell):
    """Читает команды с клавиатуры до exit или конца ввода."""
    while shell["running"]:
        try:
            line = input(get_prompt(shell))
        except EOFError:
            break
        except KeyboardInterrupt:
            shell["write"]("")
            continue
        execute(shell, line)
