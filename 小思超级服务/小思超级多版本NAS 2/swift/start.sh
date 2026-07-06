#!/bin/bash

echo "🚀 启动小思NAS服务 (Swift版)"
echo "================================"

cd swift

# 检查Swift是否安装
if ! command -v swift &> /dev/null; then
    echo "❌ Swift未安装"
    echo "请安装Swift: https://swift.org/download/"
    exit 1
fi

echo "✅ Swift版本: $(swift --version)"
echo ""

# 检查配置文件
CONFIG_FILE="../config/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠️  配置文件不存在，将使用默认配置"
fi

# 构建项目
echo "📦 构建项目..."
swift build

if [ $? -ne 0 ]; then
    echo "❌ 构建失败"
    exit 1
fi

echo "✅ 构建成功"
echo ""

# 运行服务
echo "🎯 启动服务..."
swift run

echo ""
echo "服务已停止"