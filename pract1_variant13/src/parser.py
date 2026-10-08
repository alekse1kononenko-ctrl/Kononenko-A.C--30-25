"""Разбор команд с раскрытием переменных реальной ОС."""

import os
import re

VARIABLE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def read_variable(line, index, environment):
    """Возвращает значение переменной и позицию после ее имени."""
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


def escaped_character(line, index):
    """Читает символ после обратной косой черты."""
    if index + 1 >= len(line):
        raise ValueError("обратная косая черта в конце команды")
    return line[index + 1], index + 2


def append_unquoted(value, word, words):
    """Разделяет значение без кавычек по пробельным символам."""
    for character in value:
        if character.isspace():
            if word:
                words.append("".join(word))
                word.clear()
        else:
            word.append(character)


def parse_command(line, environment=None):
    """Разбирает слова, кавычки, экранирование и $NAME/${NAME}."""
    environment = os.environ if environment is None else environment
    words, word = [], []
    quote, index, started = "", 0, False
    while index < len(line):
        character = line[index]
        if quote == "'":
            if character == quote:
                quote = ""
            else:
                word.append(character)
            index += 1
        elif character == "\\":
            value, index = escaped_character(line, index)
            word.append(value)
            started = True
        elif character == "$":
            value, index = read_variable(line, index, environment)
            if quote:
                word.append(value)
            else:
                append_unquoted(value, word, words)
            started = started or bool(value)
        else:
            quote, started = read_plain(
                character, quote, started, word, words,
            )
            index += 1
    if quote:
        raise ValueError("не закрыта кавычка")
    if word or started:
        words.append("".join(word))
    return words


def read_plain(character, quote, started, word, words):
    """Обрабатывает обычный символ, границу слова или кавычку."""
    if character == quote:
        return "", True
    if not quote and character in "\"'":
        return character, True
    if not quote and character.isspace():
        if word or started:
            words.append("".join(word))
            word.clear()
        return quote, False
    word.append(character)
    return quote, True
