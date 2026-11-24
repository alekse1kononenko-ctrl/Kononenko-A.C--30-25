#include "game_payments/json_store.hpp"

#include <raylib.h>
#include <rlgl.h>

#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>
#include <string_view>

namespace fs = std::filesystem;
using namespace game_payments;

namespace {

constexpr int width = 1120;
constexpr int height = 720;
constexpr Coins reward_amount = 50;
constexpr Color background{12, 20, 22, 255};
constexpr Color panel{19, 29, 31, 255};
constexpr Color edge{43, 58, 56, 255};
constexpr Color ink{238, 241, 229, 255};
constexpr Color muted{164, 180, 173, 255};
constexpr Color green{190, 237, 125, 255};
constexpr Color dark_green{39, 54, 35, 255};
constexpr Color orange{247, 179, 116, 255};
constexpr Rectangle reward_button{58, 238, 166, 44};

struct Product {
    const char* id;
    const char* name;
    const char* detail;
    Coins price;
    Color color;
};

constexpr std::array<Product, 3> products{{
    {"beacon", "Маяк", "Сигнал для отряда", 60, green},
    {"shield", "Щит", "Защита разведчика", 100, SKYBLUE},
    {"repair", "Ремкомплект", "Ремонт снаряжения", 140, orange},
}};

Rectangle card(std::size_t index) {
    return {36.0F + 224.0F * static_cast<float>(index), 359, 208, 247};
}

Rectangle purchase_button(std::size_t index) {
    const auto bounds = card(index);
    return {bounds.x + 14, bounds.y + 189, bounds.width - 28, 43};
}

const char* product_name(std::string_view id) {
    for (const auto& product : products) {
        if (id == product.id) {
            return product.name;
        }
    }
    return "Предмет";
}

const char* status_message(Result result) {
    switch (result) {
    case Result::success: return "Изменения сохранены";
    case Result::invalid_id: return "Недопустимый идентификатор операции";
    case Result::duplicate: return "Эта операция уже проведена";
    case Result::invalid_amount: return "Эту сумму нельзя начислить";
    case Result::unknown_item: return "Товар отсутствует в каталоге";
    case Result::invalid_price: return "Цена товара некорректна";
    case Result::insufficient_funds: return "Недостаточно монет для покупки";
    case Result::storage_error: return "Ошибка записи. Баланс и инвентарь прежние";
    }
    return "Ошибка операции";
}

class Shop {
public:
    PaymentService* payments = nullptr;
    std::string message = "Терминал готов. Получите монеты и выберите предмет.";
    Color message_color = muted;

    Result reward() {
        const auto result = payments->reward(request_id(), reward_amount);
        set_status(result, "Начислено 50 монет");
        return result;
    }

    Result buy(std::size_t index) {
        const auto result = payments->buy(request_id(), products[index].id);
        set_status(result, std::string("Предмет в инвентаре: ") + products[index].name);
        return result;
    }

private:
    std::string request_id() const {
        const auto& history = payments->history();
        auto sequence = history.size() + 1;
        for (;;) {
            const auto id = "outpost-" + std::to_string(sequence++);
            const auto used = std::find_if(history.begin(), history.end(),
                [&](const auto& entry) { return entry.id == id; });
            if (used == history.end()) {
                return id;
            }
        }
    }

    void set_status(Result result, std::string success) {
        message = result == Result::success ? std::move(success) : status_message(result);
        message_color = result == Result::success ? green : orange;
    }
};

void text(Font font, std::string_view value, float x, float y, float size, Color color) {
    const std::string terminated(value);
    DrawTextEx(font, terminated.c_str(), {x, y}, size, 0.5F, color);
}

void tile(Rectangle rect, Color color, Color border = edge) {
    DrawRectangleRounded(rect, 0.13F, 9, color);
    DrawRectangleRoundedLinesEx(rect, 0.13F, 9, 1, border);
}

void button(Font font, Rectangle rect, std::string_view label, bool primary) {
    const bool hover = CheckCollisionPointRec(GetMousePosition(), rect);
    tile(rect, primary ? (hover ? Color{211, 249, 164, 255} : green)
                       : (hover ? Color{52, 69, 55, 255} : dark_green),
         primary ? green : edge);
    text(font, label, rect.x + 13, rect.y + 10, 17, primary ? background : ink);
}

void emblem(std::size_t index, Vector2 center, Color color) {
    DrawCircleV(center, 41, Fade(color, 0.13F));
    DrawCircleLinesV(center, 41, Fade(color, 0.32F));
    if (index == 0) {
        DrawTriangle({center.x, center.y - 24}, {center.x - 13, center.y + 13},
                     {center.x + 13, center.y + 13}, color);
        for (int radius : {20, 29}) {
            DrawRing(center, static_cast<float>(radius - 1), static_cast<float>(radius),
                     205, 335, 12, Fade(color, 0.72F));
        }
    } else if (index == 1) {
        DrawPoly(center, 6, 26, 90, Fade(color, 0.32F));
        DrawPolyLinesEx(center, 6, 26, 90, 3, color);
        DrawLineEx({center.x, center.y - 13}, {center.x, center.y + 10}, 3, color);
        DrawLineEx({center.x - 8, center.y - 1}, {center.x + 8, center.y - 1}, 3, color);
    } else {
        Rectangle shape{center.x - 20, center.y - 16, 40, 32};
        DrawRectangleRoundedLinesEx(shape, 0.29F, 8, 3, color);
        DrawRectangle(static_cast<int>(center.x) - 2, static_cast<int>(center.y) - 8, 4, 16, color);
        DrawRectangle(static_cast<int>(center.x) - 8, static_cast<int>(center.y) - 2, 16, 4, color);
    }
}

void draw(Font font, const Shop& shop) {
    ClearBackground(background);
    DrawRectangle(0, 0, width, 5, green);
    text(font, "ФОРПОСТ", 36, 18, 40, ink);
    text(font, "Тренировочная станция", 38, 75, 17, muted);
    tile({823, 31, 261, 63}, panel);
    const auto balance = shop.payments ? std::to_string(shop.payments->balance()) : "—";
    text(font, "БАЛАНС", 843, 54, 14, muted);
    text(font, balance, 930, 47, balance.size() > 10 ? 13 : 23, green);

    if (!shop.payments) {
        tile({36, 126, 1048, 187}, panel);
        text(font, "Сохранение недоступно", 58, 150, 30, orange);
        text(font, shop.message, 59, 205, 18, ink);
        text(font, "Закройте второе окно или проверьте файл сохранения.", 59, 243, 17, muted);
        return;
    }

    tile({36, 120, 656, 183}, Color{23, 42, 34, 255}, Color{56, 87, 62, 255});
    const Vector2 terminal{590, 210};
    for (float radius : {32.0F, 48.0F, 68.0F}) {
        DrawCircleLinesV(terminal, radius, Fade(green, 0.28F));
    }
    DrawCircleV(terminal, 23, Fade(green, 0.26F));
    DrawPoly(terminal, 4, 14, 0, green);
    text(font, "ТЕРМИНАЛ / ТРЕНИРОВКА", 59, 141, 14, green);
    text(font, "Соберите заряд", 58, 171, 31, ink);
    text(font, "За заряд станция начисляет 50 монет.", 60, 211, 15, muted);
    button(font, reward_button, "Получить +50", true);

    text(font, "Магазин", 36, 318, 25, ink);
    text(font, "Цена в монетах", 540, 327, 14, muted);
    for (std::size_t i = 0; i < products.size(); ++i) {
        const auto& product = products[i];
        const auto rect = card(i);
        tile(rect, panel);
        emblem(i, {rect.x + rect.width / 2, rect.y + 56}, product.color);
        text(font, product.name, rect.x + 15, rect.y + 108, 20, ink);
        text(font, product.detail, rect.x + 15, rect.y + 140, 14, muted);
        button(font, purchase_button(i), "Купить · " + std::to_string(product.price), false);
    }

    tile({712, 120, 372, 486}, panel);
    text(font, "Инвентарь", 735, 139, 25, ink);
    const auto& inventory = shop.payments->inventory();
    if (inventory.empty()) {
        text(font, "Предметов пока нет", 737, 193, 17, muted);
    }
    int row = 0;
    for (const auto& [item, quantity] : inventory) {
        if (row == 3) {
            break;
        }
        text(font, product_name(item), 737, 182 + row * 29, 16, muted);
        text(font, "×" + std::to_string(quantity), 1000, 182 + row * 29, 16, ink);
        ++row;
    }
    DrawLine(735, 273, 1060, 273, edge);
    text(font, "Последние операции", 735, 289, 23, ink);
    const auto& history = shop.payments->history();
    if (history.empty()) {
        text(font, "Операций пока нет", 737, 341, 17, muted);
    }
    row = 0;
    for (auto it = history.rbegin(); it != history.rend() && row < 4; ++it, ++row) {
        const int y = 333 + row * 60;
        const bool incoming = it->operation == Operation::reward;
        const auto label = incoming ? "Заряд станции" : product_name(it->item_id);
        const auto sum = (incoming ? "+" : "-") + std::to_string(it->amount);
        DrawCircle(745, y + 15, 5, incoming ? green : orange);
        text(font, label, 762, y, 16, ink);
        text(font, incoming ? "Начисление" : "Покупка", 762, y + 22, 13, muted);
        const float size = sum.size() > 10 ? 11 : 16;
        const Vector2 measure = MeasureTextEx(font, sum.c_str(), size, 0.5F);
        text(font, sum, 1059 - measure.x, y + 5, size, incoming ? green : orange);
        DrawLine(737, y + 47, 1060, y + 47, edge);
    }
    tile({36, 622, 1048, 51}, panel);
    DrawCircle(56, 648, 4, shop.message_color);
    text(font, shop.message, 70, 635, 17, shop.message_color);
    text(font, "Пробел — заряд    1 / 2 / 3 — покупка", 36, 687, 13, muted);
    text(font, "Esc — выход", 1000, 687, 13, muted);
}

void handle_input(Shop& shop) {
    const bool clicked = IsMouseButtonPressed(MOUSE_BUTTON_LEFT);
    const auto pointer = GetMousePosition();
    if (IsKeyPressed(KEY_SPACE) || (clicked && CheckCollisionPointRec(pointer, reward_button))) {
        shop.reward();
    }
    for (std::size_t i = 0; i < products.size(); ++i) {
        if (IsKeyPressed(KEY_ONE + static_cast<int>(i)) ||
            (clicked && CheckCollisionPointRec(pointer, purchase_button(i)))) {
            shop.buy(i);
        }
    }
}

Font load_font() {
    auto executable_directory = fs::path(GetApplicationDirectory());
    if (!executable_directory.has_filename()) {
        executable_directory = executable_directory.parent_path();
    }
    const auto file = executable_directory.parent_path() / "Resources" / "NotoSans-Regular.ttf";
    if (!fs::is_regular_file(file)) {
        throw std::runtime_error("Bundled font is missing");
    }
    std::vector<int> codepoints;
    for (int glyph = 32; glyph <= 126; ++glyph) {
        codepoints.push_back(glyph);
    }
    for (int glyph = 0x400; glyph <= 0x451; ++glyph) {
        codepoints.push_back(glyph);
    }
    for (int glyph : {0x00B7, 0x00D7, 0x2014}) {
        codepoints.push_back(glyph);
    }
    Font font = LoadFontEx(file.c_str(), 50, codepoints.data(), static_cast<int>(codepoints.size()));
    SetTextureFilter(font.texture, TEXTURE_FILTER_BILINEAR);
    return font;
}

void frame(Font font, const Shop& shop, const fs::path& capture = {}) {
    BeginDrawing();
    draw(font, shop);
    bool captured = true;
    if (!capture.empty()) {
        rlDrawRenderBatchActive();
        Image image = LoadImageFromScreen();
        captured = ExportImage(image, capture.c_str());
        UnloadImage(image);
    }
    EndDrawing();
    if (!captured) {
        throw std::runtime_error("Cannot export demo screenshot");
    }
}

void check(bool expectation, const char* error) {
    if (!expectation) {
        throw std::runtime_error(error);
    }
}

void run_scenario(std::string_view name, Shop& shop, Font font, const fs::path& screenshots) {
    auto record = [&](const char* filename) {
        frame(font, shop);
        frame(font, shop, screenshots.empty() ? fs::path{} : screenshots / filename);
    };
    auto* payments = shop.payments;
    if (name == "first") {
        check(payments && payments->history().empty(), "Expected a clean profile");
        record("01-shop.png");
        check(shop.reward() == Result::success && payments->balance() == 50, "Expected balance 50");
        check(shop.buy(0) == Result::insufficient_funds && payments->balance() == 50 &&
              payments->inventory().empty() && payments->history().size() == 1,
              "Insufficient balance did not leave the state intact");
        record("02-insufficient.png");
        check(shop.reward() == Result::success && shop.buy(0) == Result::success &&
              payments->balance() == 40 && payments->inventory().at("beacon") == 1 &&
              payments->history().size() == 3, "Expected the beacon purchase");
        record("03-purchased.png");
    } else if (name == "restore") {
        check(payments && payments->balance() == 40 && payments->inventory().at("beacon") == 1 &&
              payments->history().size() == 3, "Restored state differs");
        check(payments->buy("outpost-3", "beacon") == Result::duplicate && payments->balance() == 40,
              "Restored purchase was applied twice");
        shop.message = "Сохранение загружено. Баланс и предметы восстановлены.";
        shop.message_color = green;
        record("04-restored.png");
    } else if (name == "damaged") {
        check(payments == nullptr, "Invalid file loaded");
        record("05-damaged.png");
    } else {
        throw std::runtime_error("Unknown scenario");
    }
    std::cout << "Demo " << name << ": PASS\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        fs::path save_file;
        fs::path screenshots;
        std::string_view scenario;
        for (int i = 1; i < argc; ++i) {
            const std::string_view flag(argv[i]);
            if (++i == argc) {
                throw std::runtime_error("Missing argument value");
            }
            if (flag == "--save") {
                save_file = argv[i];
            } else if (flag == "--scenario") {
                scenario = argv[i];
            } else if (flag == "--screens") {
                screenshots = argv[i];
            } else {
                throw std::runtime_error("Unknown argument");
            }
        }
        if (save_file.empty()) {
            if (const auto* directory = std::getenv("HOME"); directory && scenario.empty()) {
                save_file = fs::path(directory) / "Library/Application Support/Outpost/shop.json";
            } else {
                throw std::runtime_error("Specify --save PATH");
            }
        }
        if (!screenshots.empty()) {
            fs::create_directories(screenshots);
        }
        std::vector<Item> catalog;
        for (const auto& product : products) {
            catalog.push_back({product.id, product.price});
        }
        Shop shop;
        std::unique_ptr<JsonStore> store;
        std::unique_ptr<PaymentService> payments;
        try {
            store = std::make_unique<JsonStore>(save_file);
            payments = std::make_unique<PaymentService>(std::move(catalog), *store);
            shop.payments = payments.get();
        } catch (const StorageError& error) {
            std::cerr << error.what() << '\n';
            shop.message = "Операции приостановлены. Файл сохранён без изменений.";
        }
        SetTraceLogLevel(LOG_WARNING);
        InitWindow(width, height, "Форпост");
        if (!IsWindowReady()) {
            throw std::runtime_error("Cannot initialize the graphics window");
        }
        SetTargetFPS(60);
        const Font font = load_font();
    if (!IsFontValid(font) || font.texture.id == GetFontDefault().texture.id) {
            CloseWindow();
            throw std::runtime_error("Bundled font could not be loaded");
        }
        if (!scenario.empty()) {
            DisableCursor();
            run_scenario(scenario, shop, font, screenshots);
        } else {
            SetExitKey(KEY_ESCAPE);
            while (!WindowShouldClose()) {
                if (shop.payments) {
                    handle_input(shop);
                }
                frame(font, shop);
            }
        }
        UnloadFont(font);
        CloseWindow();
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
