"""Диагностика ошибок учебного языка с координатами в исходном тексте."""


class TranslationError(ValueError):
    """Ошибка синтаксиса или вычисления пользовательской конфигурации."""

    def __init__(self, message, line=None, column=None):
        """Добавить к сообщению строку и столбец при их наличии."""
        self.line = line
        self.column = column
        if line is not None and column is not None:
            message = f"Строка {line}, столбец {column}: {message}"
        super().__init__(message)


def located_error(message, node):
    """Создать ошибку с позицией узла Lark или его токена."""
    position = getattr(node, "meta", node)
    return TranslationError(message, position.line, position.column)
