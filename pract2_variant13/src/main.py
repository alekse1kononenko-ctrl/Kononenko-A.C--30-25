"""Command line entry point."""

import argparse
from dataclasses import asdict
import sys
from pathlib import Path
import os
import xml.etree.ElementTree as ET

from src.config import load_config
from src.nuget import NuGetRepository


def main():
    """Print validated settings or a concise error with nonzero exit status."""
    parser = argparse.ArgumentParser(description="NuGet dependency graph")
    parser.add_argument("config", help="XML configuration path")
    parser.add_argument("--stage", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.stage == 1:
            for key, value in asdict(config).items():
                if isinstance(value, Path):
                    value = os.path.relpath(value)
                print(f"{key} — {value}")
        else:
            repository = NuGetRepository(config.repository, config.framework)
            node = (config.package, config.version)
            print(f"Direct dependencies of {node[0]}@{node[1]}:")
            for package, version in repository.dependencies(node):
                print(f"  {package}@{version}")
        return 0
    except (OSError, ValueError, ET.ParseError) as error:
        message = str(error).replace(str(Path.cwd()), ".")
        print(f"Error: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
