"""Синтаксический анализ полной конфигурации средствами Lark LALR(1)."""

from functools import lru_cache
from pathlib import Path

from lark import Lark, UnexpectedInput

from .errors import TranslationError


@lru_cache(maxsize=1)
def language_parser():
    """Загрузить и сохранить анализатор из отдельной EBNF-грамматики."""
    grammar_path = Path(__file__).with_name("grammar.lark")
    return Lark.open(
        str(grammar_path), parser="lalr", propagate_positions=True,
        maybe_placeholders=False,
    )


def parse(source):
    """Разобрать весь текст или сообщить координаты синтаксической ошибки."""
    try:
        return language_parser().parse(source)
    except UnexpectedInput as error:
        context = error.get_context(source).rstrip()
        message = f"Синтаксическая ошибка.\n{context}"
        raise TranslationError(message, error.line, error.column) from None
