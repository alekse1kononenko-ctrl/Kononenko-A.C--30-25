"""Enforce coursework limits with AST, pycodestyle and radon."""

import ast
from pathlib import Path
import sys

import pycodestyle
from radon.complexity import cc_visit

FILE_LIMIT = 1000
FUNCTION_LIMIT = 40
ARGUMENT_LIMIT = 7
COMPLEXITY_LIMIT = 10
LINE_LIMIT = 80
ROOT = Path(__file__).resolve().parents[1]


def check_function(path, node):
    """Require bounded documented functions."""
    errors = []
    length = node.end_lineno - node.lineno + 1
    arguments = len(node.args.args) + len(node.args.kwonlyargs)
    if length > FUNCTION_LIMIT:
        errors.append(f"{path}:{node.name}: function too long")
    if arguments > ARGUMENT_LIMIT:
        errors.append(f"{path}:{node.name}: too many arguments")
    if not ast.get_docstring(node):
        errors.append(f"{path}:{node.name}: missing docstring")
    return errors


def check_file(path):
    """Check AST limits and independent radon complexity metrics."""
    source = path.read_text(encoding="utf-8")
    errors = []
    if len(source.splitlines()) > FILE_LIMIT:
        errors.append(f"{path}: file too long")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            errors.extend(check_function(path, node))
    for block in cc_visit(source):
        if block.complexity > COMPLEXITY_LIMIT:
            errors.append(f"{path}:{block.name}: complexity >10")
    return errors


def main():
    """Audit source, tests and tools; return a nonzero status on failure."""
    folders = [ROOT / name for name in ("src", "tests", "tools")]
    errors = []
    for folder in folders:
        for path in folder.rglob("*.py"):
            errors.extend(check_file(path))
    style = pycodestyle.StyleGuide(max_line_length=LINE_LIMIT)
    result = style.check_files([str(folder) for folder in folders])
    for error in errors:
        print(error)
    print(f"AST/radon violations: {len(errors)}")
    print(f"PEP8 violations: {result.total_errors}")
    print("PASS" if not errors and not result.total_errors else "FAIL")
    return bool(errors or result.total_errors)


if __name__ == "__main__":
    sys.exit(main())
