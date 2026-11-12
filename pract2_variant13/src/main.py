"""Command line entry point."""

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as element_tree

from src.application import run
from src.config import load_config


def main():
    """Run a development stage and report user errors with a nonzero status."""
    parser = argparse.ArgumentParser(description="NuGet dependency graph")
    parser.add_argument("config", help="XML configuration path")
    parser.add_argument("--stage", type=int, choices=(1, 2, 3, 4, 5), default=5)
    args = parser.parse_args()
    try:
        run(load_config(args.config), args.stage)
        return 0
    except (OSError, ValueError, element_tree.ParseError) as error:
        message = str(error).replace(str(Path.cwd()), ".")
        print(f"Error: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
