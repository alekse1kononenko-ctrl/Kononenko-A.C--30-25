"""Проверки конфигурации и остановки стартового скрипта."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from src.main import read_settings
from src.shell import Shell


class ConfigurationTests(unittest.TestCase):
    """Проверяет оба параметра и сценарии с ошибками."""

    def test_parameters(self):
        """Пути с пробелами передаются без изменения."""
        settings = read_settings([
            "--vfs", "a b.zip", "--script", "c d.txt",
        ])
        self.assertEqual(settings.vfs, "a b.zip")
        self.assertEqual(settings.script, "c d.txt")

    def test_missing_required(self):
        """Без пути VFS argparse завершает запуск с кодом 2."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                read_settings([])
        self.assertEqual(error.exception.code, 2)

    def test_stop_on_first_error(self):
        """Строка после неизвестной команды не выполняется."""
        output = []
        shell = Shell("test", write=output.append)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "start.txt"
            path.write_text("unknown\nexit\n", encoding="utf-8")
            self.assertFalse(shell.run_script(path))
        self.assertTrue(shell.running)
        self.assertFalse(any("$ exit" in line for line in output))

    def test_script_file_missing(self):
        """Отсутствующий скрипт дает понятную ошибку."""
        output = []
        shell = Shell("test", write=output.append)
        self.assertFalse(shell.run_script("missing-script.txt"))
        self.assertIn("Ошибка стартового скрипта", output[0])
