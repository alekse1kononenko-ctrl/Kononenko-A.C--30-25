#include "game_payments/service.hpp"

#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string_view>

using namespace game_payments;

namespace {

class MemoryStore final : public TransactionStore {
public:
    std::vector<Transaction> entries;
    bool fail = false;

    std::vector<Transaction> load() override { return entries; }
    void save(const std::vector<Transaction>& history) override {
        if (fail) {
            throw StorageError("Simulated failure");
        }
        entries = history;
    }
};

void require(bool condition, std::string_view message) {
    if (!condition) {
        throw std::runtime_error(std::string(message));
    }
}

void purchase() {
    MemoryStore store;
    PaymentService service({{"shield", 60}}, store);
    require(service.reward("reward-1", 100) == Result::success, "Reward");
    require(service.buy("buy-1", "shield") == Result::success, "Purchase");
    require(service.balance() == 40 && service.inventory().at("shield") == 1, "State");
    const auto& entry = service.history().at(1);
    require(entry.id == "buy-1" && entry.operation == Operation::purchase &&
            entry.item_id == "shield" && entry.amount == 60, "Purchase history");
    require(store.entries.size() == 2, "Store history");
}

void rejected_operations() {
    MemoryStore store;
    PaymentService service({{"shield", 60}, {"invalid", 0}, {"negative", -1}}, store);
    require(service.reward("reward", 20) == Result::success, "Initial reward");
    require(service.buy("buy", "shield") == Result::insufficient_funds, "Insufficient funds");
    require(service.buy("buy", "missing") == Result::unknown_item, "Missing item");
    require(service.buy("buy", "invalid") == Result::invalid_price, "Zero price");
    require(service.buy("buy", "negative") == Result::invalid_price, "Negative price");
    require(service.buy("bad id", "shield") == Result::invalid_id, "Invalid ID");
    require(service.reward("bad", -1) == Result::invalid_amount, "Negative reward");
    require(service.reward("bad", 0) == Result::invalid_amount, "Zero reward");
    require(service.reward("bad", std::numeric_limits<Coins>::max()) ==
            Result::invalid_amount, "Overflow");
    require(service.balance() == 20 && service.inventory().empty() &&
            service.history().size() == 1 && store.entries.size() == 1, "State mutated");
}

void duplicate() {
    MemoryStore store;
    {
        PaymentService service({{"shield", 60}}, store);
        require(service.reward("reward", 120) == Result::success, "Initial reward");
        require(service.buy("buy", "shield") == Result::success, "First purchase");
        require(service.buy("buy", "shield") == Result::duplicate, "Repeated purchase");
        require(service.reward("buy", 5) == Result::duplicate, "Same ID for another operation");
    }
    PaymentService restored({{"shield", 50}}, store);
    require(restored.buy("buy", "shield") == Result::duplicate, "Repeat after restoration");
    require(restored.balance() == 60 && restored.inventory().at("shield") == 1 &&
            restored.history().size() == 2, "Original purchase price was retained");
    require(restored.buy("new-buy", "shield") == Result::success && restored.balance() == 10 &&
            restored.inventory().at("shield") == 2, "Different ID and current price");
}

void storage_failure() {
    MemoryStore store;
    PaymentService service({{"shield", 60}}, store);
    require(service.reward("reward", 60) == Result::success, "Initial reward");
    store.fail = true;
    require(service.buy("buy", "shield") == Result::storage_error, "Storage error");
    require(service.balance() == 60 && service.inventory().empty() &&
            service.history().size() == 1 && store.entries.size() == 1, "Partial mutation");
    store.fail = false;
    require(service.buy("buy", "shield") == Result::success && service.balance() == 0,
            "Retry after storage failure and exact debit");
}

void invalid_history() {
    MemoryStore store;
    store.entries = {{"1", Operation::purchase, 3, "shield"}};
    try {
        PaymentService service({}, store);
    } catch (const StorageError&) {
        return;
    }
    throw std::runtime_error("Inconsistent transaction loaded");
}

}  // namespace

int main(int argc, char* argv[]) {
    const std::map<std::string_view, void (*)()> tests = {
        {"purchase", purchase}, {"rejections", rejected_operations}, {"duplicate", duplicate},
        {"storage_failure", storage_failure}, {"invalid_history", invalid_history},
    };
    if (argc != 2 || tests.count(argv[1]) == 0) {
        return 2;
    }
    try {
        tests.at(argv[1])();
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
    return 0;
}
