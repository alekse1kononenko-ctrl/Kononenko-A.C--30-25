#!/bin/sh
set -u
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir" || exit 1
if [ ! -x .venv/bin/python ]; then
    echo 'Сначала выполните установку из README.md: make setup'
    printf 'Нажмите Enter, чтобы закрыть окно: '
    read -r answer
    exit 1
fi
while :; do
    printf '\nПрактическая № 3, вариант 13\n'
    printf '1 - Веб-сервер -> TOML\n2 - Теплица -> TOML\n'
    printf '3 - Показать синтаксическую ошибку\n4 - Запустить тесты\n'
    printf '5 - Открыть папку проекта\n0 - Выход\nВыберите пункт: '
    read -r choice || exit 0
    case "$choice" in
        1) ./run.sh < examples/webserver.conf ;;
        2) ./run.sh < examples/greenhouse.conf ;;
        3) ./run.sh < examples/invalid.conf ;;
        4) .venv/bin/python -m unittest discover -s tests -v ;;
        5) open "$project_dir" ;;
        0) exit 0 ;;
        *) echo 'Введите число от 0 до 5.' ;;
    esac
done
