cmake_minimum_required(VERSION 3.20)
project(GamePayments LANGUAGES CXX)

add_library(game_payments STATIC src/wallet.cpp src/service.cpp)
target_include_directories(game_payments PUBLIC include)
target_compile_features(game_payments PUBLIC cxx_std_17)
set_target_properties(game_payments PROPERTIES CXX_EXTENSIONS OFF)

if(CMAKE_SOURCE_DIR STREQUAL PROJECT_SOURCE_DIR)
    include(CTest)
endif()

if(CMAKE_SOURCE_DIR STREQUAL PROJECT_SOURCE_DIR AND BUILD_TESTING)
    add_executable(wallet_tests tests/wallet_tests.cpp)
    target_link_libraries(wallet_tests PRIVATE game_payments)
    set_target_properties(wallet_tests PROPERTIES CXX_EXTENSIONS OFF)

    add_test(NAME wallet.credit COMMAND wallet_tests credit)
    add_test(NAME wallet.reject_zero COMMAND wallet_tests zero)
    add_test(NAME wallet.reject_negative COMMAND wallet_tests negative)
    add_test(NAME wallet.reject_overflow COMMAND wallet_tests overflow)

    add_executable(service_tests tests/service_tests.cpp)
    target_link_libraries(service_tests PRIVATE game_payments)
    foreach(scenario purchase rejections duplicate storage_failure invalid_history)
        add_test(NAME service.${scenario} COMMAND service_tests ${scenario})
    endforeach()
endif()

if(CMAKE_SOURCE_DIR STREQUAL PROJECT_SOURCE_DIR)
    set(full_build_default ON)
else()
    set(full_build_default OFF)
endif()
option(GAME_PAYMENTS_BUILD_STORAGE "Build the JSON storage adapter" ${full_build_default})

if(GAME_PAYMENTS_BUILD_STORAGE)
    include(FetchContent)
    if(POLICY CMP0135)
        cmake_policy(SET CMP0135 NEW)
    endif()
    set(JSON_BuildTests OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(nlohmann_json
        URL https://codeload.github.com/nlohmann/json/tar.gz/refs/tags/v3.12.0
        URL_HASH SHA256=4b92eb0c06d10683f7447ce9406cb97cd4b453be18d7279320f7b2f025c10187)
    FetchContent_MakeAvailable(nlohmann_json)

    add_library(game_payments_json STATIC storage/json_store.cpp)
    target_link_libraries(game_payments_json PUBLIC game_payments PRIVATE nlohmann_json::nlohmann_json)
    set_target_properties(game_payments_json PROPERTIES CXX_EXTENSIONS OFF)

    if(CMAKE_SOURCE_DIR STREQUAL PROJECT_SOURCE_DIR AND BUILD_TESTING)
        add_executable(store_tests tests/store_tests.cpp)
        target_link_libraries(store_tests PRIVATE game_payments_json)
        foreach(scenario round_trip damaged invalid_values lock real_write_failure)
            add_test(NAME storage.${scenario} COMMAND store_tests ${scenario})
        endforeach()
    endif()
endif()

if(GAME_PAYMENTS_BUILD_STORAGE AND CMAKE_SOURCE_DIR STREQUAL PROJECT_SOURCE_DIR)
    add_executable(console_shop examples/console_shop.cpp)
    target_link_libraries(console_shop PRIVATE game_payments_json)
endif()
