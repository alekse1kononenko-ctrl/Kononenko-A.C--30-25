#include "game_payments/json_store.hpp"

#include <nlohmann/json.hpp>

#include <cerrno>
#include <cstdio>
#include <fcntl.h>
#include <fstream>
#include <limits>
#include <system_error>
#include <sys/file.h>
#include <unistd.h>
#include <utility>

namespace game_payments {
namespace {

using nlohmann::json;
constexpr std::size_t max_file_size = 8 * 1024 * 1024;
constexpr int schema_version = 1;

StorageError io_error(const char* message) {
    return StorageError(std::string(message) + ": " +
                        std::error_code(errno, std::generic_category()).message());
}

Coins parse_amount(const json& value) {
    if (!value.is_number_integer() ||
        (value.is_number_unsigned() &&
         value.get<std::uint64_t>() > static_cast<std::uint64_t>(std::numeric_limits<Coins>::max()))) {
        throw StorageError("Amount must be a signed 64-bit integer");
    }
    return value.get<Coins>();
}

class TemporaryFile {
public:
    explicit TemporaryFile(const std::filesystem::path& target)
        : path_(target.string() + ".tmp.XXXXXX"), fd_(::mkstemp(path_.data())) {
        if (fd_ < 0) {
            throw io_error("Cannot create temporary save");
        }
    }

    ~TemporaryFile() {
        if (fd_ >= 0) {
            ::close(fd_);
        }
        if (!path_.empty()) {
            ::unlink(path_.c_str());
        }
    }

    void replace(const std::filesystem::path& target, std::string_view data) {
        while (!data.empty()) {
            const auto count = ::write(fd_, data.data(), data.size());
            if (count < 0 && errno == EINTR) {
                continue;
            }
            if (count <= 0) {
                throw io_error("Cannot write temporary save");
            }
            data.remove_prefix(static_cast<std::size_t>(count));
        }
        if (::fsync(fd_) < 0) {
            throw io_error("Cannot flush temporary save");
        }
        if (::close(std::exchange(fd_, -1)) < 0) {
            throw io_error("Cannot close temporary save");
        }
        if (::rename(path_.c_str(), target.c_str()) < 0) {
            throw io_error("Cannot replace save");
        }
        path_.clear();
    }

private:
    std::string path_;
    int fd_;
};

}  // namespace

JsonStore::JsonStore(std::filesystem::path file) : file_(std::move(file)), lock_fd_(-1) {
    if (file_.filename().empty()) {
        throw StorageError("Missing save filename");
    }
    if (const auto parent = file_.parent_path(); !parent.empty()) {
        std::error_code error;
        std::filesystem::create_directories(parent, error);
        if (error) {
            throw StorageError("Cannot create save directory: " + error.message());
        }
    }

    const auto lock_path = file_.string() + ".lock";
    lock_fd_ = ::open(lock_path.c_str(), O_WRONLY | O_CREAT | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (lock_fd_ < 0) {
        throw io_error("Cannot open save lock");
    }
    if (::flock(lock_fd_, LOCK_EX | LOCK_NB) < 0) {
        const auto error = io_error("Cannot lock save");
        ::close(lock_fd_);
        throw error;
    }
}

JsonStore::~JsonStore() {
    ::close(lock_fd_);
}

std::vector<Transaction> JsonStore::load() {
    std::error_code error;
    const auto type = std::filesystem::symlink_status(file_, error).type();
    if (type == std::filesystem::file_type::not_found) {
        return {};
    }
    if (error || type != std::filesystem::file_type::regular) {
        throw StorageError("Save is not a readable regular file");
    }
    const auto size = std::filesystem::file_size(file_, error);
    if (error || size > max_file_size) {
        throw StorageError("Cannot read save size, or file exceeds 8 MiB");
    }

    std::ifstream input(file_, std::ios::binary);
    std::string data(static_cast<std::size_t>(size), '\0');
    if (!input || !input.read(data.data(), static_cast<std::streamsize>(data.size())) ||
        input.peek() != std::char_traits<char>::eof() || input.bad()) {
        throw StorageError("Cannot read save");
    }

    try {
        const auto document = json::parse(data);
        const auto& version = document.at("version");
        const auto& entries = document.at("transactions");
        if (!version.is_number_integer() || version != schema_version || !entries.is_array()) {
            throw StorageError("Unsupported save schema");
        }
        std::vector<Transaction> result;
        result.reserve(entries.size());
        for (const auto& value : entries) {
            const auto type_name = value.at("type").get<std::string>();
            if (type_name != "reward" && type_name != "purchase") {
                throw StorageError("Unknown transaction type");
            }
            result.push_back({value.at("id").get<std::string>(),
                              type_name == "reward" ? Operation::reward : Operation::purchase,
                              parse_amount(value.at("amount")), value.at("item").get<std::string>()});
        }
        return result;
    } catch (const json::exception&) {
        throw StorageError("Malformed JSON or transaction fields");
    }
}

void JsonStore::save(const std::vector<Transaction>& history) {
    auto entries = json::array();
    for (const auto& entry : history) {
        entries.push_back({{"id", entry.id},
                           {"type", entry.operation == Operation::reward ? "reward" : "purchase"},
                           {"amount", entry.amount}, {"item", entry.item_id}});
    }
    const auto data = json{{"version", schema_version}, {"transactions", std::move(entries)}}.dump(2) + "\n";
    if (data.size() > max_file_size) {
        throw StorageError("Save exceeds 8 MiB");
    }
    TemporaryFile temporary(file_);
    temporary.replace(file_, data);
}

}  // namespace game_payments
