#pragma once

#include <cstdint>

namespace game_payments {

using Coins = std::int64_t;

class Wallet {
public:
    [[nodiscard]] Coins balance() const noexcept;
    [[nodiscard]] bool credit(Coins amount) noexcept;
    [[nodiscard]] bool debit(Coins amount) noexcept;

private:
    Coins balance_ = 0;
};

}  // namespace game_payments
