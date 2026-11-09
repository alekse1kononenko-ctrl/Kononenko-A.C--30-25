"""Application operations independent from command line parsing."""

from dataclasses import asdict
import os
from pathlib import Path

from src.graph import breadth_first, describe, label
from src.local import LocalRepository
from src.nuget import NuGetRepository
from src.versions import normalize


def settings(config):
    """Display validated settings with portable output paths."""
    for key, value in asdict(config).items():
        if isinstance(value, Path) or (config.test_mode and key == "repository"):
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
    graph = breadth_first([node], repository.dependencies)
    print(describe(graph))
