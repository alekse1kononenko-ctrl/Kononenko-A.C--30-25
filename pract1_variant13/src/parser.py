"""Подстановка переменных ОС и разбор команды стандартным shlex."""

import os
import re
import shlex

VARIABLE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def read_variable(line, index, environment):
    """Читает $NAME или ${NAME}, возвращает значение и новую позицию."""
    start = index + 1
    if start < len(line) and line[start] == "{":
        end = line.find("}", start)
        if end < 0:
            raise ValueError("не закрыта фигурная скобка переменной")
        name = line[start + 1:end]
        if not VARIABLE.fullmatch(name):
            raise ValueError("неверное имя переменной окружения")
        return environment.get(name, ""), end + 1
    match = VARIABLE.match(line, start)
    if match is None:
        return "$", start
    return environment.get(match.group(), ""), match.end()


def escape_value(value, quote):
    """Сохраняет кавычки из значения переменной как обычный текст."""
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    if quote != '"':
        value = value.replace("'", "\\'")
    return value


def expand_variables(line, environment):
    """Подставляет переменные вне одинарных кавычек перед разбором."""
    result = ""
    quote = ""
    index = 0
    while index < len(line):
        character = line[index]
        if character == "\\" and quote != "'":
            result += line[index:index + 2]
            index += 2
            continue
        if character in "\"'":
            if not quote:
                quote = character
            elif quote == character:
                quote = ""
        if character == "$" and quote != "'":
            value, index = read_variable(line, index, environment)
            result += escape_value(value, quote)
        else:
            result += character
            index += 1
    return result


def parse_command(line, environment=None):
    """Возвращает слова команды; незакрытые кавычки дают ValueError."""
    if environment is None:
        environment = os.environ
    return shlex.split(expand_variables(line, environment))
