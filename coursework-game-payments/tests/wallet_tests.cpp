#include "game_payments/wallet.hpp"

#include <iostream>
#include <limits>
#include <string_view>

using game_payments::Coins;
using game_payments::Wallet;

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Expected one scenario name\n";
        return 2;
    }

    const std::string_view scenario = argv[1];
    Wallet wallet;
    bool passed = false;

    if (scenario == "credit") {
        passed = wallet.balance() == 0 && wallet.credit(50) && wallet.credit(10)
            && wallet.balance() == 60;
    } else if (scenario == "zero") {
        passed = wallet.credit(50) && !wallet.credit(0) && wallet.balance() == 50;
    } else if (scenario == "negative") {
        passed = wallet.credit(50) && !wallet.credit(-5) && wallet.balance() == 50;
    } else if (scenario == "overflow") {
        constexpr Coins max_coins = std::numeric_limits<Coins>::max();
        passed = wallet.credit(max_coins - 1) && wallet.credit(1)
            && !wallet.credit(1) && wallet.balance() == max_coins;
    } else {
        std::cerr << "Unknown scenario: " << scenario << '\n';
        return 2;
    }

    if (!passed) {
        std::cerr << "Wallet check failed: " << scenario << '\n';
        return 1;
    }

    return 0;
}
