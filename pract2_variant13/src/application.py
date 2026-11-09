"""Application operations independent from command line parsing."""

from dataclasses import asdict
import os
from pathlib import Path

from src.graph import breadth_first, describe, label
from src.local import LocalRepository
from src.nuget import NuGetRepository
from src.versions import normalize
from src.reverse import reverse_dependencies, scope_roots
from src.visualize import visualize


def settings(config):
    """Display validated settings with portable output paths."""
    for key, value in asdict(config).items():
        local_path = config.test_mode and key == "repository"
        if isinstance(value, Path) or local_path:
            value = os.path.relpath(value)
        print(f"{key} — {value}")


def repository_for(config):
    """Construct either a local or a standard-library NuGet repository."""
    if config.test_mode:
        return LocalRepository(config.repository)
    return NuGetRepository(config.repository, config.framework)


def run(config, stage):
    """Execute the requested development stage against actual data."""
    if stage == 1:
        settings(config)
        return
    repository = repository_for(config)
    name = config.package if config.test_mode else config.package.lower()
    node = (name, normalize(config.version))
    if stage == 2:
        print(f"Direct dependencies of {label(node)}:")
        for child in repository.dependencies(node):
            print("  " + label(child))
        return
    if stage == 4 or config.reverse:
        graph = find_reverse(config, repository, node)
        print("Reverse dependencies (target -> dependent):")
        print(", ".join(map(label, graph.order[1:])) or "(none)")
    else:
        graph = breadth_first([node], repository.dependencies)
    print(describe(graph))
    if stage == 5:
        visualize(graph, node, config.output, config.ascii)


def find_reverse(config, repository, node):
    """Require an explicit finite universe for remote reverse dependencies."""
    if config.test_mode:
        roots = repository.nodes()
        print("Scope: complete local repository")
    else:
        if not config.scope:
            raise ValueError("NuGet reverse queries require an explicit scope")
        roots = scope_roots(config.scope)
        print("Scope: closure of explicit roots, not all of NuGet")
    return reverse_dependencies(repository, node, roots)
