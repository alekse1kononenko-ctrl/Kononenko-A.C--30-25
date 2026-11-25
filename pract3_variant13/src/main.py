"""Интерфейс командной строки: UTF-8 stdin, TOML stdout, ошибки stderr."""

import argparse
import sys

from .errors import TranslationError
from .translator import translate

VERSION = "1.0.0"
EXIT_SUCCESS = 0
EXIT_ERROR = 1


def run(input_stream, output_stream, error_stream):
    """Записать полный TOML только после успешной трансляции документа."""
    try:
        result = translate(input_stream.read())
        output_stream.write(result)
    except TranslationError as error:
        print(f"Ошибка: {error}", file=error_stream)
        return EXIT_ERROR
    except (UnicodeError, OSError) as error:
        print(f"Ошибка ввода/вывода: {error}", file=error_stream)
        return EXIT_ERROR
    return EXIT_SUCCESS


def configure_streams():
    """Настроить стандартные потоки на UTF-8 без замены переносов строк."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="strict", newline="")


def main(argv=None):
    """Обработать справку и версию, затем перевести стандартный ввод."""
    parser = argparse.ArgumentParser(
        description="Вариант 13: учебный конфигурационный язык -> TOML.",
        epilog="Ввод: stdin, вывод: stdout, диагностика: stderr. UTF-8.",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    configure_streams()
    parser.parse_args(argv)
    return run(sys.stdin, sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
