"""Цикл диалога и выполнение команд эмулятора."""

from .parser import parse_command
from .commands import COMMANDS


class Shell:
    """Хранит состояние одной сессии оболочки."""

    def __init__(self, name, vfs=None, write=print):
        """Задает имя VFS, файловую систему и функцию вывода."""
        self.name = name
        self.vfs = vfs
        self.write = write
        self.cwd = "/"
        self.running = True

    @property
    def prompt(self):
        """Формирует приглашение с именем VFS и текущим путем."""
        return f"{self.name}:{self.cwd}$ "

    def execute(self, line):
        """Выполняет строку и возвращает признак успешной команды."""
        try:
            words = parse_command(line)
            if not words:
                return True
            self.dispatch(words[0], words[1:])
            return True
        except (ValueError, OSError) as error:
            self.write(f"Ошибка: {error}")
            return False

    def dispatch(self, command, arguments):
        """Выбирает команду по ее имени и обрабатывает exit."""
        if command == "exit":
            if arguments:
                raise ValueError("exit: аргументы не поддерживаются")
            self.running = False
        elif command in ("ls", "cd"):
            if self.vfs is None:
                self.write(f"{command}: аргументы = {arguments!r}")
            else:
                COMMANDS[command](self, arguments)
        elif command in COMMANDS:
            COMMANDS[command](self, arguments)
        else:
            raise ValueError(f"неизвестная команда: {command}")

    def run_script(self, path):
        """Показывает диалог и останавливается на первой ошибке."""
        try:
            with open(path, encoding="utf-8-sig") as script:
                for number, line in enumerate(script, start=1):
                    line = line.rstrip("\r\n")
                    if not line.strip():
                        continue
                    self.write(self.prompt + line)
                    if not self.execute(line):
                        self.write(f"Скрипт остановлен: строка {number}")
                        return False
                    if not self.running:
                        break
            return True
        except (OSError, UnicodeError) as error:
            self.write(f"Ошибка стартового скрипта: {error}")
            return False

    def repl(self):
        """Повторяет чтение и выполнение, пока не введен exit."""
        while self.running:
            try:
                line = input(self.prompt)
            except EOFError:
                break
            except KeyboardInterrupt:
                self.write("")
                continue
            self.execute(line)
