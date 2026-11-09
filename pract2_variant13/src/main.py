"""Command line entry point."""

import argparse
from dataclasses import asdict
import sys
from pathlib import Path
import os
import xml.etree.ElementTree as ET

from src.config import load_config


def main():
    """Print validated settings or a concise error with nonzero exit status."""
    parser = argparse.ArgumentParser(description="NuGet dependency graph")
    parser.add_argument("config", help="XML configuration path")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        for key, value in asdict(config).items():
            if isinstance(value, Path):
                value = os.path.relpath(value)
            print(f"{key} — {value}")
        return 0
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
