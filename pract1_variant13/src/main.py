"""Чтение конфигурации и запуск консольного эмулятора."""

import argparse
from pathlib import Path
from .shell import Shell


def read_settings(argv=None):
    """Принимает путь ZIP VFS и необязательный стартовый скрипт."""
    parser = argparse.ArgumentParser(description="Эмулятор Вариант 13")
    parser.add_argument("--vfs", required=True, help="путь ZIP VFS")
    parser.add_argument("--script", help="путь стартового скрипта")
    return parser.parse_args(argv)


def main(argv=None):
    """Печатает настройки, выполняет скрипт и запускает REPL."""
    settings = read_settings(argv)
    print(f"Конфигурация: VFS = {settings.vfs}")
    print(f"Конфигурация: скрипт = {settings.script or '(не задан)'}")
    shell = Shell(Path(settings.vfs).stem)
    if settings.script and not shell.run_script(settings.script):
        return 1
    if shell.running:
        shell.repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
