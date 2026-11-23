#include "game_payments/wallet.hpp"

#include <limits>

namespace game_payments {

Coins Wallet::balance() const noexcept {
    return balance_;
}

bool Wallet::credit(Coins amount) noexcept {
    if (amount <= 0 || amount > std::numeric_limits<Coins>::max() - balance_) {
        return false;
    }

    balance_ += amount;
    return true;
}

bool Wallet::debit(Coins amount) noexcept {
    if (amount <= 0 || amount > balance_) {
        return false;
    }

    balance_ -= amount;
    return true;
}

}  // namespace game_payments
