"""Reverse dependency queries over an explicit finite repository scope."""

import json
from pathlib import Path

from src.config import PACKAGE
from src.graph import breadth_first
from src.versions import normalize


def scope_roots(filename):
    """Read explicitly chosen NuGet roots for a bounded reverse query."""
    values = json.loads(Path(filename).read_text(encoding="utf-8"))
    if not isinstance(values, list) or not values:
        raise ValueError("scope must be a nonempty JSON list of roots")
    roots = []
    for value in values:
        if not isinstance(value, dict) or set(value) != {"package", "version"}:
            raise ValueError("scope roots require package and version")
        name = value["package"]
        if not isinstance(name, str) or not PACKAGE.fullmatch(name):
            raise ValueError("Invalid scope package")
        roots.append((name.lower(), normalize(value["version"])))
    return roots


def reverse_graph(graph, target):
    """Reverse every edge, then search ancestors with recursive BFS."""
    incoming = {node: [] for node in graph.edges}
    for parent, children in graph.edges.items():
        for child in children:
            incoming.setdefault(child, []).append(parent)
    if target not in incoming:
        raise ValueError("Target is not present in the declared scope")
    return breadth_first([target], incoming.__getitem__)


def reverse_dependencies(repository, target, roots):
    """Collect the finite scope and run the same BFS over reversed edges."""
    universe = breadth_first(roots, repository.dependencies)
    return reverse_graph(universe, target)
