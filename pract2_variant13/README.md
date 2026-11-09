# Граф зависимостей NuGet — практическая работа 2, вариант 13

Python 3.10+, стандартная библиотека. Установка пакетов Python не нужна.

## Запуск

`./run.sh configs/nuget.xml`

`python3 -m unittest discover -s tests -v`

Этап 1 выводит проверенные параметры XML. Пути разрешаются относительно XML.
Обязательны package, repository, test_mode, version, output и ascii.
Логические значения: true/false. output должен иметь расширение .png.
В обычном режиме repository — NuGet V3 Service Index HTTP(S).
В тестовом режиме repository — существующий локальный файл.
Дополнительные параметры: framework (net8.0), reverse (false), scope.
Ошибки возвращают код 1, неверный синтаксис CLI — код 2.
