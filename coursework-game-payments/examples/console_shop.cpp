#include "game_payments/json_store.hpp"

#include <iostream>

int main(int argc, char* argv[]) {
    using namespace game_payments;
    if (argc != 2) {
        std::cerr << "Usage: console_shop SAVE_FILE\n";
        return 2;
    }
    try {
        JsonStore store(argv[1]);
        PaymentService payments({{"shield", 60}}, store);
        const auto reward = payments.reward("example-reward-1", 100);
        const auto purchase = payments.buy("example-purchase-1", "shield");
        if ((reward != Result::success && reward != Result::duplicate) ||
            (purchase != Result::success && purchase != Result::duplicate)) {
            std::cerr << "Could not run the example purchase\n";
            return 1;
        }
        std::cout << "Balance: " << payments.balance() << "\nOperations: "
                  << payments.history().size() << '\n';
    } catch (const StorageError& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
