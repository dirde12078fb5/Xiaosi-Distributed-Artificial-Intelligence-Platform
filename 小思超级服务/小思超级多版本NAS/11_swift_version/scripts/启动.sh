#!/bin/bash

# 小思超级NAS - Swift版本启动脚本
# 使用Vapor框架

set -e

echo ""
echo "========================================"
echo "  🚀 小思超级NAS (Swift/Vapor版本)"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 检查配置文件
if [ ! -f "config/.env" ]; then
    echo "[错误] 未找到配置文件 config/.env"
    echo "请确保配置文件存在"
    exit 1
fi

# 加载环境变量
export $(grep -v '^#' config/.env | xargs)

# 检查Swift环境
if ! command -v swift &> /dev/null; then
    echo "[错误] 未找到Swift命令，请安装Swift工具链"
    echo "下载地址: https://swift.org/download/"
    exit 1
fi

echo "[信息] Swift版本: $(swift --version | head -n 1)"
echo "[信息] 项目目录: $PROJECT_DIR"
echo ""

# 复制Package.swift到项目根目录（如果不存在）
if [ ! -f "Package.swift" ]; then
    if [ -f "config/Package.swift" ]; then
        cp config/Package.swift .
        echo "[信息] 已复制Package.swift到项目根目录"
    fi
fi

# 构建项目
echo "[信息] 正在构建项目..."
swift build -c release

if [ $? -ne 0 ]; then
    echo "[错误] 构建失败！"
    exit 1
fi

echo ""
echo "[信息] 构建成功！正在启动服务器..."
echo ""

# 启动服务器
# 使用.env文件中的配置
swift run XiaosiNAS

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "[错误] 服务器异常退出，退出码: $exit_code"
fi

exit $exit_code
