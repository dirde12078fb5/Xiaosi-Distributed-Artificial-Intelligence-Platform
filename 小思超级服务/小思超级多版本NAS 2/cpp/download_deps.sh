#!/bin/bash

echo "===================================="
echo "下载NAS服务所需第三方库"
echo "===================================="
echo

# 创建第三方库目录
if [ ! -d "third_party" ]; then
    echo "创建第三方库目录..."
    mkdir -p third_party
fi

cd third_party

# 下载 cpp-httplib
if [ -f "httplib.h" ]; then
    echo "httplib.h 已存在，跳过下载"
else
    echo "下载 cpp-httplib..."
    curl -L -o httplib.h https://raw.githubusercontent.com/yhirose/cpp-httplib/master/httplib.h
    if [ $? -ne 0 ]; then
        echo "下载 httplib.h 失败！"
        echo "请手动下载: https://raw.githubusercontent.com/yhirose/cpp-httplib/master/httplib.h"
    fi
fi

# 下载 nlohmann/json
if [ -f "json.hpp" ]; then
    echo "json.hpp 已存在，跳过下载"
else
    echo "下载 nlohmann/json..."
    curl -L -o json.hpp https://raw.githubusercontent.com/nlohmann/json/v3.11.2/single_include/nlohmann/json.hpp
    if [ $? -ne 0 ]; then
        echo "下载 json.hpp 失败！"
        echo "请手动下载: https://raw.githubusercontent.com/nlohmann/json/v3.11.2/single_include/nlohmann/json.hpp"
    fi
fi

cd ..

echo
echo "===================================="
echo "第三方库下载完成"
echo "===================================="
echo

# 构建项目
echo "开始构建项目..."
if [ ! -d "build" ]; then
    mkdir -p build
fi

cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

echo
echo "构建完成！"