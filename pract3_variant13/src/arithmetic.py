"""Числовые операции и проверка конечности результатов трансляции."""

import math
import operator

from .errors import located_error

OPERATIONS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "pow": math.pow,
}


def finite_number(value, node):
    """Отвергнуть бесконечность и NaN в литералах и результатах операций."""
    if not math.isfinite(value):
        raise located_error("Число выходит за допустимый диапазон.", node)
    return value


def calculate(operation, left, right, node):
    """Вычислить одну бинарную операцию над двумя вещественными числами."""
    if not all(isinstance(value, float) for value in (left, right)):
        raise located_error("Арифметическая операция требует числа.", node)
    try:
        result = OPERATIONS[operation](left, right)
    except ZeroDivisionError:
        raise located_error("Деление на ноль.", node) from None
    except OverflowError:
        raise located_error("Переполнение числового результата.", node)
    except ValueError:
        message = "Недопустимые аргументы pow в вещественных числах."
        raise located_error(message, node) from None
    return finite_number(result, node)
