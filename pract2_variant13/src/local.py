"""Strict local JSON repository with capital Latin package names."""

import json
from pathlib import Path
import re

from src.versions import normalize

NAME = re.compile(r"[A-Z]+")


class LocalRepository:
    """A complete finite repository; all nodes share one explicit version."""

    def __init__(self, filename):
        """Load a JSON graph and validate all vertices and edge targets."""
        raw = json.loads(Path(filename).read_text(encoding="utf-8"),
                         object_pairs_hook=unique_object)
        if not isinstance(raw, dict) or set(raw) != {"version", "packages"}:
            raise ValueError("Expected JSON version and packages fields")
        self.version = normalize(raw["version"])
        self.packages = raw["packages"]
        if not isinstance(self.packages, dict) or not self.packages:
            raise ValueError("packages must be a nonempty object")
        for name, children in self.packages.items():
            self.validate_entry(name, children)

    def validate_entry(self, name, children):
        """Require capital names, adjacency lists and declared endpoints."""
        if not NAME.fullmatch(name):
            raise ValueError(f"Local package must match [A-Z]+: {name}")
        if not isinstance(children, list):
            raise ValueError(f"Dependencies must be a list: {name}")
        for child in children:
            if not isinstance(child, str) or child not in self.packages:
                raise ValueError(f"Unknown dependency from {name}: {child}")
        if len(set(children)) != len(children):
            raise ValueError(f"Duplicate dependency from {name}")

    def dependencies(self, node):
        """Return outgoing edges for the exact requested package version."""
        name, version = node
        if name not in self.packages:
            raise ValueError(f"Package not found: {name}")
        if normalize(version) != self.version:
            raise ValueError(f"Version not available: {name}@{version}")
        return [(child, self.version) for child in self.packages[name]]

    def nodes(self):
        """Enumerate every node, including isolated vertices."""
        return [(name, self.version) for name in self.packages]


def unique_object(pairs):
    """Reject repeated JSON keys rather than silently replacing a vertex."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result
