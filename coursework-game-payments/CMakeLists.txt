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
