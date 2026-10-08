"""Чтение двух параметров и запуск консольного эмулятора."""

import argparse
from pathlib import Path

from .shell import create_shell, repl, run_script
from .vfs import load_vfs


def read_settings(argv=None):
    """Принимает обязательный путь ZIP и необязательный путь скрипта."""
    parser = argparse.ArgumentParser(description="Эмулятор: вариант 13")
    parser.add_argument("--vfs", required=True, help="путь ZIP VFS")
    parser.add_argument("--script", help="путь стартового скрипта")
    return parser.parse_args(argv)


def main(argv=None):
    """Печатает параметры, загружает ZIP, выполняет скрипт и диалог."""
    settings = read_settings(argv)
    print(f"Конфигурация: VFS = {settings.vfs}")
    print(f"Конфигурация: скрипт = {settings.script or '(не задан)'}")
    try:
        vfs = load_vfs(settings.vfs)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return 1
    print(f"VFS загружена: файлов {len(vfs['files'])}, "
          f"каталогов {len(vfs['directories'])}")
    shell = create_shell(Path(settings.vfs).stem, vfs)
    if settings.script and not run_script(shell, settings.script):
        return 1
    if shell["running"]:
        repl(shell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
