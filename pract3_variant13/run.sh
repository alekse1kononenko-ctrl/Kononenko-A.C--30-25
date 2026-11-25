#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"
if [ -x .venv/bin/python ]; then
    default_python=.venv/bin/python
else
    default_python=python3
fi
python_command=${PYTHON:-$default_python}
if ! "$python_command" -c 'import sys; assert sys.version_info >= (3, 11); import lark, tomli_w'; then
    echo 'Нужен Python 3.11+ с зависимостями. Инструкция: README.md, раздел «Установка».' >&2
    exit 1
fi
exec "$python_command" -m src.main "$@"
