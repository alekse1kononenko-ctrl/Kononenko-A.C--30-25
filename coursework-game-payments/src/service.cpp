#include "game_payments/service.hpp"

#include <algorithm>
#include <type_traits>
#include <utility>

namespace game_payments {
namespace {

bool valid_id(std::string_view id) {
    return !id.empty() && id.size() <= 80 &&
        std::all_of(id.begin(), id.end(), [](char c) {
            return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                   (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.' || c == ':';
        });
}

}  // namespace

PaymentService::PaymentService(std::vector<Item> catalog, TransactionStore& store)
    : store_(store) {
    for (const auto& item : catalog) {
        if (!valid_id(item.id) || !catalog_.emplace(item.id, item.price).second) {
            throw std::invalid_argument("Invalid or duplicate catalog item ID");
        }
    }
    for (const auto& entry : store_.load()) {
        if (!apply(state_, entry)) {
            throw StorageError("Inconsistent transaction history");
        }
    }
}

Coins PaymentService::balance() const noexcept {
    return state_.wallet.balance();
}

const std::map<std::string, std::size_t>& PaymentService::inventory() const noexcept {
    return state_.inventory;
}

const std::vector<Transaction>& PaymentService::history() const noexcept {
    return state_.history;
}

Result PaymentService::check_request(std::string_view request_id) const {
    if (!valid_id(request_id)) {
        return Result::invalid_id;
    }
    if (state_.applied.count(std::string(request_id)) != 0) {
        return Result::duplicate;
    }
    return Result::success;
}

Result PaymentService::reward(std::string_view request_id, Coins amount) {
    if (const auto status = check_request(request_id); status != Result::success) {
        return status;
    }
    Wallet wallet = state_.wallet;
    if (!wallet.credit(amount)) {
        return Result::invalid_amount;
    }
    return commit({std::string(request_id), Operation::reward, amount, {}});
}

Result PaymentService::buy(std::string_view request_id, std::string_view item_id) {
    if (const auto status = check_request(request_id); status != Result::success) {
        return status;
    }
    const auto item = catalog_.find(item_id);
    if (item == catalog_.end()) {
        return Result::unknown_item;
    }
    const auto price = item->second;
    if (price <= 0) {
        return Result::invalid_price;
    }
    if (state_.wallet.balance() < price) {
        return Result::insufficient_funds;
    }
    return commit({std::string(request_id), Operation::purchase, price, item->first});
}

Result PaymentService::commit(Transaction entry) {
    State candidate = state_;
    if (!apply(candidate, entry)) {
        throw std::logic_error("Transaction was rejected after validation");
    }
    try {
        store_.save(candidate.history);
    } catch (const StorageError&) {
        return Result::storage_error;
    }
    static_assert(std::is_nothrow_move_assignable_v<State>);
    state_ = std::move(candidate);
    return Result::success;
}

bool PaymentService::apply(State& state, const Transaction& entry) {
    if (!valid_id(entry.id) || state.applied.count(entry.id) != 0) {
        return false;
    }
    switch (entry.operation) {
    case Operation::reward:
        if (!entry.item_id.empty() || !state.wallet.credit(entry.amount)) {
            return false;
        }
        break;
    case Operation::purchase:
        if (!valid_id(entry.item_id) || !state.wallet.debit(entry.amount)) {
            return false;
        }
        ++state.inventory[entry.item_id];
        break;
    default:
        return false;
    }
    state.applied.insert(entry.id);
    state.history.push_back(entry);
    return true;
}

}  // namespace game_payments
