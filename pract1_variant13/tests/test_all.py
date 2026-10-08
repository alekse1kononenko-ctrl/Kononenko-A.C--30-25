"""Поддержка команды python -m unittest discover -s tests -v."""

from tests.__main__ import build_suite


def load_tests(loader, tests, pattern):
    """Передает unittest набор обычных тестовых функций."""
    return build_suite()
