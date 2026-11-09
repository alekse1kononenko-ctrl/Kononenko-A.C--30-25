"""Read and validate the XML application settings."""

from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

PACKAGE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
VERSION = re.compile(r"\d+(?:\.\d+){0,3}(?:-[0-9A-Za-z.-]+)?")
REQUIRED = {"package", "repository", "test_mode", "version", "output", "ascii"}
OPTIONAL = {"framework", "reverse", "scope"}


@dataclass(frozen=True)
class Config:
    """Validated settings; paths are relative to the XML file."""

    package: str
    repository: str
    test_mode: bool
    version: str
    output: Path
    ascii: bool
    framework: str = "net8.0"
    reverse: bool = False
    scope: str = ""


def boolean(value):
    """Accept only explicit XML boolean values."""
    if value not in {"true", "false"}:
        raise ValueError("Boolean must be true or false")
    return value == "true"


def http_url(value):
    """Require an absolute HTTP(S) URL without credentials or fragments."""
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("Repository must be an absolute HTTP(S) URL")
    if parts.username or parts.password or parts.fragment or parts.query:
        raise ValueError("URL credentials, query and fragment are forbidden")
    if any(char.isspace() for char in value):
        raise ValueError("Whitespace in URL")
    _ = parts.port
    return value


def resolve_file(base, value):
    """Resolve a required existing input file."""
    path = (base / value).resolve()
    if not path.is_file():
        raise ValueError(f"Input file does not exist: {value}")
    return str(path)


def output_file(base, value):
    """Require a PNG path with an existing writable parent."""
    path = (base / value).resolve()
    if path.suffix.lower() != ".png" or path.is_dir():
        raise ValueError("Output must be a PNG file")
    if not path.parent.is_dir():
        raise ValueError("Output directory does not exist")
    import os
    if not os.access(path.parent, os.W_OK):
        raise ValueError("Output directory is not writable")
    if path.exists() and not os.access(path, os.W_OK):
        raise ValueError("Output file is not writable")
    return path


def read_fields(path):
    """Reject malformed XML, unknown, repeated or empty settings."""
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("XML entities and DTD are forbidden")
    root = ET.fromstring(raw)
    if root.tag != "config" or root.attrib:
        raise ValueError("Expected <config> without attributes")
    fields = {}
    for element in root:
        if element.tag in fields or element.tag not in REQUIRED | OPTIONAL:
            raise ValueError(f"Unknown or duplicate setting: {element.tag}")
        if element.attrib or list(element) or not (element.text or "").strip():
            raise ValueError(f"Empty or nested setting: {element.tag}")
        fields[element.tag] = element.text.strip()
    missing = REQUIRED - fields.keys()
    if missing:
        raise ValueError(f"Missing settings: {', '.join(sorted(missing))}")
    return fields


def load_config(filename):
    """Load settings and validate each value before accessing a repository."""
    path = Path(filename).resolve()
    fields = read_fields(path)
    if not PACKAGE.fullmatch(fields["package"]):
        raise ValueError("Invalid package name")
    if not VERSION.fullmatch(fields["version"]):
        raise ValueError("Invalid package version")
    test_mode = boolean(fields["test_mode"])
    repository = fields["repository"]
    if test_mode:
        repository = resolve_file(path.parent, repository)
    else:
        repository = http_url(repository)
    output = output_file(path.parent, fields["output"])
    if str(output) == repository or output == path:
        raise ValueError("Output must not overwrite an input file")
    scope = fields.get("scope", "")
    if scope:
        scope = resolve_file(path.parent, scope)
    return Config(fields["package"], repository, test_mode,
                  fields["version"], output, boolean(fields["ascii"]),
                  fields.get("framework", "net8.0"),
                  boolean(fields.get("reverse", "false")), scope)
