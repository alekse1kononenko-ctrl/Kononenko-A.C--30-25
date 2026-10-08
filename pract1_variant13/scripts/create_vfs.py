"""Создает три учебных ZIP; эмулятор их не модифицирует."""

from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def save_archive(name, entries):
    """Записывает воспроизводимые файлы начальной VFS."""
    with ZipFile(DATA / name, "w", compression=ZIP_STORED) as archive:
        for path, content in entries.items():
            archive.writestr(path, content)


def main():
    """Готовит минимальный, плоский и вложенный варианты VFS."""
    DATA.mkdir(exist_ok=True)
    save_archive("minimal.zip", {"hello.txt": "Hello, VFS!\n"})
    save_archive("several.zip", {
        "alpha.txt": "Alpha\n", "beta.txt": "Beta\n",
        "binary.bin": bytes([0, 255, 16, 128]),
    })
    deep = {
        "readme.txt": "Variant 13: in-memory VFS.\n",
        "docs/guide.txt": "Commands: ls cd uname cat clear rm exit.\n",
        "docs/level2/level3/note.txt": "Three directory levels.\n",
        "docs/file with spaces.txt": "Quoted path works.\n",
        "tmp/delete_me.txt": "Remove only from memory.\n",
        "tmp/second.txt": "Second removable file.\n",
        "binary.bin": bytes([0, 255, 16, 128]),
        "empty/": "",
    }
    save_archive("deep.zip", deep)
    save_archive("path with spaces.zip", deep)
    (DATA / "invalid.zip").write_text("not a ZIP", encoding="utf-8")
    print("Созданы minimal.zip, several.zip, deep.zip и проверки ошибок")


if __name__ == "__main__":
    main()
