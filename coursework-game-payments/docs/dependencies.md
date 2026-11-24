# Лицензии компонентов

Исходники курсовой распространяются по MIT. Зависимости фиксируются версиями и SHA-256 архивов в CMake.

| Компонент | Версия | Условия |
| --- | --- | --- |
| raylib | 6.2 | zlib/libpng. Сохраняются уведомления raylib и вложенных компонентов. [Исходники](https://github.com/raysan5/raylib/tree/6.2) |
| GLFW | Копия из raylib 6.2 | zlib/libpng. [Уведомление](https://github.com/raysan5/raylib/blob/6.2/src/external/glfw/LICENSE.md) |
| nlohmann/json | 3.12.0 | MIT. [Уведомление](https://github.com/nlohmann/json/blob/v3.12.0/LICENSE.MIT) |
| Noto Sans Regular | `ffebf8c1ee449e544955a7e813c54f9b73848eac` | SIL OFL 1.1. TTF и лицензия находятся в `assets/`. [Источник](https://github.com/notofonts/noto-fonts/tree/ffebf8c1ee449e544955a7e813c54f9b73848eac/hinted/ttf/NotoSans) |
| CMake и CTest | 4.4.5 при испытаниях | BSD-3-Clause. [Лицензия](https://cmake.org/licensing/) |
| Qt Creator | Открытая редакция | GPLv3 с исключением Qt Company GPL Exception 1.0. [Условия](https://github.com/qt-creator/qt-creator/blob/master/README.md#licenses-and-attributions) |
| Git | Системная сборка Apple | GPLv2. [Лицензия](https://github.com/git/git/blob/master/COPYING) |

Тексты MIT, zlib и OFL копируются в `Outpost.app/Contents/Resources`. Исходный архив raylib содержит условия встроенных компонентов в заголовках и каталогах. Qt Creator, CMake и Git используются как отдельные инструменты разработки.
