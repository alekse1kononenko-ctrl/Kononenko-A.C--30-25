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


class ParseState:
    """Хранит разобранные слова и состояние текущего символа."""

    def __init__(self):
        """Начинает разбор без открытой кавычки и без текущего слова."""
        self.words, self.word = [], []
        self.quote, self.index, self.started = "", 0, False

    def consume(self, line, environment):
        """Разбирает один символ с учетом открытых кавычек."""
        character = line[self.index]
        if self.quote == "'":
            # В одинарных кавычках доллар является обычным символом.
            if character == self.quote:
                self.quote = ""
            else:
                self.word.append(character)
            self.index += 1
        elif character == "\\":
            value, self.index = escaped_character(line, self.index)
            self.word.append(value)
            self.started = True
        elif character == "$":
            self.expand(line, environment)
        else:
            self.quote, self.started = read_plain(
                character, self.quote, self.started, self.word, self.words,
            )
            self.index += 1

    def expand(self, line, environment):
        """Подставляет значение из окружения реального процесса Python."""
        value, self.index = read_variable(line, self.index, environment)
        if self.quote:
            # Двойные кавычки сохраняют пробелы внутри одного аргумента.
            self.word.append(value)
            self.started = True
        else:
            append_unquoted(value, self.word, self.words)
            self.started = bool(self.word) or self.started and not value


def parse_command(line, environment=None):
    """Разбирает слова, кавычки, экранирование и $NAME/${NAME}."""
    environment = os.environ if environment is None else environment
    state = ParseState()
    while state.index < len(line):
        state.consume(line, environment)
    if state.quote:
        raise ValueError("не закрыта кавычка")
    if state.word or state.started:
        state.words.append("".join(state.word))
    return state.words


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
