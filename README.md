# Конфигурационное управление, ИКБО-30-25

Эмулятор оболочки по варианту 13 находится в `pract1_variant13`.
Он написан на Python без собственных классов и внешних зависимостей.
Описание команд, функций и примеры есть в
[README проекта](pract1_variant13/README.md).

Для запуска нужен Python 3.10 или новее:

```sh
cd pract1_variant13
python3 scripts/create_vfs.py
python3 -m src.main --vfs data/deep.zip
python3 -m tests
```

В Windows используйте `python` вместо `python3`.
Из корня репозитория оболочку можно запустить через
`./run.sh --vfs data/deep.zip` или `run.bat --vfs data/deep.zip`.

Файл `pract1` содержит предыдущие упражнения и сохранен без изменений.

## Домашнее задание. Вариант 13

Переводчик учебного конфигурационного языка в TOML находится в
[pract3_variant13](pract3_variant13/README.md).
Вход и выход - стандартные потоки, разбор выполняется Lark LALR(1).
В README приведены установка на Mac, все функции, тесты и два примера.
Для демонстрации после установки запустите `pract3_variant13/demo.command`.
