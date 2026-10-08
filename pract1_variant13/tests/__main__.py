"""Запуск тестовых функций стандартной библиотекой unittest."""

import unittest

from . import test_commands, test_configuration, test_parser
from . import test_rm, test_shell, test_vfs

TEST_MODULES = [
    test_parser, test_configuration, test_vfs,
    test_shell, test_commands, test_rm,
]


def build_suite():
    """Собирает функции с префиксом test_ из шести модулей."""
    suite = unittest.TestSuite()
    for module in TEST_MODULES:
        for name, function in vars(module).items():
            if name.startswith("test_"):
                suite.addTest(unittest.FunctionTestCase(function))
    return suite


def main():
    """Печатает результаты и возвращает код 1 при провале теста."""
    result = unittest.TextTestRunner(verbosity=2).run(build_suite())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
