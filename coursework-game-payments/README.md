# Встраиваемая игровая платёжная система

Статическая библиотека C++17 для локальных операций с виртуальными монетами. Демонстрационное приложение «Форпост» показывает начисление, покупку, инвентарь и историю. Модуль `game_payments` подключается отдельно от raylib и JSON-хранилища.

## Сборка для macOS

Нужны CMake 3.22 или новее и Apple Command Line Tools. Первая сборка скачивает raylib 6.2 и nlohmann/json 3.12.0 и проверяет SHA-256 архивов.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64
cmake --build build --parallel
ctest --test-dir build --output-on-failure
open build/Outpost.app
```

В Qt Creator откройте `CMakeLists.txt`, выберите настольный комплект с Clang и CMake и соберите `Outpost`.

## Проверка работы

1. Нажмите «Получить +50» или пробел.
2. Нажмите «Купить · 60» или клавишу 1. При балансе 50 появится сообщение о нехватке монет.
3. Получите ещё 50 и купите маяк. Баланс станет 40, справа появится маяк и запись о покупке.
4. Закройте окно клавишей Esc и откройте снова. Состояние восстановится.

Профиль хранится в `~/Library/Application Support/Outpost/shop.json`. Для показа с нуля запустите приложение с отдельным файлом:

```sh
demo_dir=$(mktemp -d)
./build/Outpost.app/Contents/MacOS/Outpost --save "$demo_dir/shop.json"
```

Повреждённый или занятый файл блокирует запись. Закройте окно перед повторным запуском с тем же профилем. Если файл повреждён, сохраните его копию и запустите приложение с новым путём.

## Подключение к другому проекту

```cmake
add_subdirectory(coursework-game-payments)
target_link_libraries(my_game PRIVATE game_payments)
```

Подключите `game_payments/service.hpp` и передайте свой `TransactionStore` в `PaymentService`. Чтобы использовать файловый адаптер, включите `GAME_PAYMENTS_BUILD_STORAGE` и подключите цель `game_payments_json`. Из корня проекта выполните:

```sh
example_dir=$(mktemp -d)
./build/console_shop "$example_dir/example.json"
./build/console_shop "$example_dir/example.json"
```

Оба запуска выводят `Balance: 40` и `Operations: 2`. Клиент создаёт новый идентификатор на каждую новую операцию. При повторной отправке использует прежний идентификатор.

## Тесты

```sh
ctest --test-dir build --output-on-failure
./tests/demo_smoke.sh "$PWD/build/Outpost.app/Contents/MacOS/Outpost" "$PWD/build/evidence"
```

Графический сценарий требует сеанса macOS и создаёт отдельный временный профиль. Для сборки ядра укажите `-DGAME_PAYMENTS_BUILD_STORAGE=OFF -DGAME_PAYMENTS_BUILD_DEMO=OFF`.

[Проектирование и схемы](docs/design.md) · [MIT](LICENSE) · [Лицензии компонентов](docs/dependencies.md)
