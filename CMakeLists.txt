cmake_minimum_required(VERSION 3.24)
project(warwarden_protocol LANGUAGES CXX)

add_library(warwarden_protocol STATIC
    cpp/src/protobuf_codec.cpp
    cpp/src/protocol_validation.cpp)
add_library(WarWarden::Protocol ALIAS warwarden_protocol)

target_compile_features(warwarden_protocol PUBLIC cxx_std_20)
target_include_directories(warwarden_protocol
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/cpp/include>
        $<INSTALL_INTERFACE:include>)

option(WARWARDEN_PROTOCOL_BUILD_TESTS "Build protocol contract tests" ${PROJECT_IS_TOP_LEVEL})

if(WARWARDEN_PROTOCOL_BUILD_TESTS)
    include(FetchContent)
    FetchContent_Declare(
        googletest
        URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE)
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)

    enable_testing()
    add_executable(warwarden_protocol_tests
        tests/development_pose_test.cpp
        tests/protobuf_codec_test.cpp
        tests/protocol_status_test.cpp)
    target_link_libraries(warwarden_protocol_tests
        PRIVATE WarWarden::Protocol GTest::gtest_main)

    include(GoogleTest)
    gtest_discover_tests(warwarden_protocol_tests)
endif()
