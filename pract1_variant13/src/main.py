"""Точка входа консольного прототипа."""

from .shell import Shell


def main():
    """Запускает интерактивный диалог первого этапа."""
    Shell("variant13").repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
