"""Полный конвейер: учебный язык, дерево Lark, значения, текст TOML."""

import tomli_w

from .evaluator import evaluate
from .parser import parse


def translate(source):
    """Преобразовать весь документ в TOML, сохраняя порядок объявлений."""
    return tomli_w.dumps(evaluate(parse(source)))
