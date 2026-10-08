"""Проверки ZIP, вложенных путей и сохранности данных на диске."""

import base64
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from src.vfs import list_path, load_vfs, read_file, resolve_path
from tests.helpers import expect_error


def create_archive(path):
    """Готовит ZIP с тремя уровнями, двоичными данными и пустой папкой."""
    with ZipFile(path, "w") as archive:
        archive.writestr("a/b/c/file.txt", "text")
        archive.writestr("binary.bin", b"\x00\xff\x80")
        archive.writestr("empty/", "")


def test_three_levels():
    """Родительские каталоги создаются даже без отдельных ZIP-записей."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "vfs.zip"
        create_archive(path)
        vfs = load_vfs(path)
    assert "/a/b/c" in vfs["directories"]
    assert list_path(vfs, "/a/b/c") == ["file.txt"]
    assert read_file(vfs, "/a/b/c/file.txt") == b"text"


def test_binary_base64():
    """Двоичные байты представлены строкой base64 без потерь."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "vfs.zip"
        create_archive(path)
        vfs = load_vfs(path)
    encoded = vfs["files"]["/binary.bin"]
    assert base64.b64decode(encoded) == b"\x00\xff\x80"


def test_no_disk_modification():
    """После загрузки на диске остается только исходный неизменный ZIP."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "vfs.zip"
        create_archive(path)
        before = path.read_bytes()
        load_vfs(path)
        assert path.read_bytes() == before
        assert list(Path(directory).iterdir()) == [path]


def test_path_normalization():
    """Переход к родителю не выходит за виртуальный корень."""
    assert resolve_path("../c", "/a/b") == "/a/c"
    assert resolve_path("../../..", "/a") == "/"
    assert resolve_path("//a", "/") == "/a"
    assert resolve_path(".", "/a") == "/a"
    expect_error(resolve_path, "")


def test_loading_errors():
    """Отсутствующий файл и обычный текст не принимаются как VFS."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "invalid.zip"
        assert "не найден" in expect_error(load_vfs, path)
        path.write_text("invalid", encoding="utf-8")
        assert "ZIP" in expect_error(load_vfs, path)


def test_invalid_archive_paths():
    """Архивы с выходом за корень и конфликтами путей отклоняются."""
    cases = [
        ["../bad"], ["/absolute"], ["a\\b"],
        ["a", "a/file.txt"], ["a/file.txt", "a"],
        ["a/", "a"], ["a", "a/"], ["same", "./same"],
    ]
    with TemporaryDirectory() as directory:
        path = Path(directory) / "unsafe.zip"
        for entries in cases:
            with ZipFile(path, "w") as archive:
                for name in entries:
                    archive.writestr(name, "x")
            expect_error(load_vfs, path)


def test_empty_archive():
    """Пустой ZIP содержит виртуальный корень без файлов."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "empty.zip"
        with ZipFile(path, "w"):
            pass
        vfs = load_vfs(path)
    assert vfs == {"directories": {"/"}, "files": {}}
    assert list_path(vfs, "/") == []
