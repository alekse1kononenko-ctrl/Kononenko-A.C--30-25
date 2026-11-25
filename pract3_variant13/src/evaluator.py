"""Последовательное вычисление констант и вложенных выражений Lark."""

from lark import Tree
from lark.visitors import Interpreter

from .arithmetic import calculate, finite_number
from .errors import located_error

MAX_NESTING = 64
NESTED_RULES = {"array", "expression"}
STRING_DELIMITER_LENGTH = 2


def check_nesting(tree):
    """Ограничить вложенность массивов и выражений до вычисления дерева."""
    pending = [(tree, 0)]
    while pending:
        node, depth = pending.pop()
        depth += node.data in NESTED_RULES
        if depth > MAX_NESTING:
            message = f"Превышена допустимая вложенность {MAX_NESTING}."
            raise located_error(message, node)
        pending.extend(
            (child, depth) for child in node.children
            if isinstance(child, Tree)
        )


class Evaluator(Interpreter):
    """Обходить дерево сверху вниз с таблицей уже объявленных констант."""

    def __init__(self):
        """Создать независимую таблицу констант для одного документа."""
        super().__init__()
        self.constants = {}

    def start(self, tree):
        """Вычислить объявления по порядку и вернуть таблицу результата."""
        for declaration in tree.children:
            self.visit(declaration)
        return self.constants

    def declaration(self, tree):
        """Вычислить значение нового имени, исключая переобъявление."""
        name, value = tree.children
        if name in self.constants:
            raise located_error(f"Повторное объявление {name}.", name)
        self.constants[str(name)] = self.visit(value)

    def number(self, tree):
        """Преобразовать числовой токен в конечное вещественное число."""
        return finite_number(float(tree.children[0]), tree)

    def string(self, tree):
        """Удалить только внешние скобки, сохранив исходное содержимое."""
        token = str(tree.children[0])
        return token[STRING_DELIMITER_LENGTH:-STRING_DELIMITER_LENGTH]

    def array(self, tree):
        """Вычислить каждый элемент массива, включая вложенные значения."""
        return [self.visit(child) for child in tree.children]

    def reference(self, tree):
        """Найти константу, объявленную ранее в текущем документе."""
        name = tree.children[0]
        if name not in self.constants:
            raise located_error(f"Неизвестная константа {name}.", name)
        return self.constants[name]

    def expression(self, tree):
        """Рекурсивно вычислить два операнда префиксной операции."""
        operation, left, right = tree.children
        return calculate(
            str(operation), self.visit(left), self.visit(right), tree,
        )


def evaluate(tree):
    """Проверить глубину дерева и вычислить документ с чистым окружением."""
    check_nesting(tree)
    return Evaluator().visit(tree)
