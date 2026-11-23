#pragma once

#include "game_payments/wallet.hpp"

#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_set>
#include <vector>

namespace game_payments {

struct Item {
    std::string id;
    Coins price;
};

enum class Operation { reward, purchase };

struct Transaction {
    std::string id;
    Operation operation;
    Coins amount;
    std::string item_id;
};

class StorageError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class TransactionStore {
public:
    virtual ~TransactionStore() = default;
    virtual std::vector<Transaction> load() = 0;
    virtual void save(const std::vector<Transaction>& history) = 0;
};

enum class Result {
    success, invalid_id, duplicate, invalid_amount, unknown_item,
    invalid_price, insufficient_funds, storage_error
};

class PaymentService {
public:
    // The store must outlive the service. Call the service from one thread.
    PaymentService(std::vector<Item> catalog, TransactionStore& store);

    [[nodiscard]] Coins balance() const noexcept;
    [[nodiscard]] const std::map<std::string, std::size_t>& inventory() const noexcept;
    [[nodiscard]] const std::vector<Transaction>& history() const noexcept;
    [[nodiscard]] Result reward(std::string_view request_id, Coins amount);
    [[nodiscard]] Result buy(std::string_view request_id, std::string_view item_id);

private:
    struct State {
        Wallet wallet;
        std::map<std::string, std::size_t> inventory;
        std::unordered_set<std::string> applied;
        std::vector<Transaction> history;
    };

    [[nodiscard]] Result check_request(std::string_view request_id) const;
    [[nodiscard]] Result commit(Transaction entry);
    static bool apply(State& state, const Transaction& entry);

    std::map<std::string, Coins, std::less<>> catalog_;
    TransactionStore& store_;
    State state_;
};

}  // namespace game_payments
