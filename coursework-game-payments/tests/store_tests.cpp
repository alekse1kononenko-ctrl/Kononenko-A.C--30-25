#include "game_payments/json_store.hpp"

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
#include <string_view>
#include <unistd.h>

using namespace game_payments;
namespace fs = std::filesystem;

namespace {

class TestDirectory {
public:
    TestDirectory() {
        std::string name = (fs::temp_directory_path() / "game-wallet-test-XXXXXX").string();
        if (::mkdtemp(name.data()) == nullptr) {
            throw std::runtime_error("Cannot create test directory");
        }
        path = name;
    }
    ~TestDirectory() {
        std::error_code ignored;
        fs::remove_all(path, ignored);
    }

    fs::path path;
};

void require(bool result, const char* message) {
    if (!result) {
        throw std::runtime_error(message);
    }
}

void write_file(const fs::path& file, std::string_view data) {
    std::ofstream stream(file);
    stream << data;
    stream.close();
    require(static_cast<bool>(stream), "Cannot write test fixture");
}

std::string read_file(const fs::path& file) {
    std::ifstream stream(file);
    require(static_cast<bool>(stream), "Cannot read test fixture");
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

void round_trip(const fs::path& file) {
    {
        JsonStore store(file);
        PaymentService service({{"shield", 60}}, store);
        require(service.balance() == 0 && service.history().empty(), "First run");
        require(service.reward("r-1", 100) == Result::success, "Reward");
        require(service.buy("b-1", "shield") == Result::success, "Purchase");
    }
    JsonStore store(file);
    PaymentService service({{"shield", 70}}, store);
    require(service.balance() == 40 && service.inventory().at("shield") == 1, "Restored state");
    require(service.history().size() == 2 && service.history().back().amount == 60,
            "Restored history");
    require(service.buy("b-1", "shield") == Result::duplicate && service.balance() == 40,
            "Replayed request was not rejected");
}

void expect_corrupt(const fs::path& file, std::string_view contents) {
    write_file(file, contents);
    JsonStore store(file);
    try {
        PaymentService service({}, store);
    } catch (const StorageError&) {
        require(read_file(file) == contents, "Corrupt file changed");
        return;
    }
    throw std::runtime_error("Corrupt save was accepted");
}

void damaged(const fs::path& file) {
    expect_corrupt(file, "{broken-json");
    expect_corrupt(file, R"({"version":2,"transactions":[]})");
}

void invalid_values(const fs::path& file) {
    expect_corrupt(file, R"({"version":1,"transactions":[{"id":"x","type":"reward","amount":9223372036854775808,"item":""}]})");
    expect_corrupt(file, R"({"version":1,"transactions":[{"id":"x","type":"reward","amount":1.2,"item":""}]})");
    expect_corrupt(file, R"({"version":1,"transactions":[{"id":"x","type":"reward","amount":1,"item":""},{"id":"x","type":"reward","amount":1,"item":""}]})");
}

void lock(const fs::path& file) {
    JsonStore first(file);
    try {
        JsonStore second(file);
    } catch (const StorageError&) {
        return;
    }
    throw std::runtime_error("Competing writer was allowed");
}

void real_write_failure(const fs::path& file) {
    JsonStore store(file);
    PaymentService service({{"shield", 60}}, store);
    require(service.reward("reward", 60) == Result::success, "Initial reward");
    const auto original = read_file(file);
    const auto backup = file.string() + ".retained";
    fs::rename(file, backup);
    fs::create_directory(file);
    require(service.buy("buy", "shield") == Result::storage_error, "Real save should fail");
    require(service.balance() == 60 && service.inventory().empty() &&
            service.history().size() == 1 && read_file(backup) == original, "State changed");
    for (const auto& entry : fs::directory_iterator(file.parent_path())) {
        require(entry.path().filename().string().find(".tmp.") == std::string::npos,
                "Temporary file was left behind");
    }
    fs::remove(file);
    fs::rename(backup, file);
    require(service.buy("buy", "shield") == Result::success, "Retry");
}

}  // namespace

int main(int argc, char* argv[]) {
    const std::map<std::string_view, void (*)(const fs::path&)> tests = {
        {"round_trip", round_trip}, {"damaged", damaged}, {"invalid_values", invalid_values},
        {"lock", lock}, {"real_write_failure", real_write_failure},
    };
    if (argc != 2 || tests.count(argv[1]) == 0) {
        return 2;
    }
    try {
        TestDirectory directory;
        tests.at(argv[1])(directory.path / "save.json");
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
    return 0;
}
