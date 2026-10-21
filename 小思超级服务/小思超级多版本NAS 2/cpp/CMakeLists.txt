cmake_minimum_required(VERSION 3.15)
project(NASServer VERSION 2.0.0 LANGUAGES CXX)

# C++标准设置
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
if(MSVC)
    add_compile_options(/W4 /utf-8)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 查找依赖包
find_package(Threads REQUIRED)

# 添加可执行文件
add_executable(nas_server
    main.cpp
)

# 包含目录
target_include_directories(nas_server PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)

# 链接库
target_link_libraries(nas_server PRIVATE
    Threads::Threads
)

# 平台特定设置
if(WIN32)
    target_link_libraries(nas_server PRIVATE ws2_32)
elseif(UNIX AND NOT APPLE)
    target_link_libraries(nas_server PRIVATE pthread)
endif()

# 安装目标
install(TARGETS nas_server
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

# 打印配置信息
message(STATUS "========== NAS Server Build Configuration ==========")
message(STATUS "CMake version: ${CMAKE_VERSION}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "====================================================")