#pragma once

#include "game_payments/service.hpp"

#include <filesystem>

namespace game_payments {

class JsonStore final : public TransactionStore {
public:
    explicit JsonStore(std::filesystem::path file);
    ~JsonStore() override;

    JsonStore(const JsonStore&) = delete;
    JsonStore& operator=(const JsonStore&) = delete;

    std::vector<Transaction> load() override;
    void save(const std::vector<Transaction>& history) override;

private:
    std::filesystem::path file_;
    int lock_fd_;
};

}  // namespace game_payments
