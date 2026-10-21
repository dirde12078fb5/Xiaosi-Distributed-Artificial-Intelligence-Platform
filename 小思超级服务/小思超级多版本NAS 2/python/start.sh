#!/bin/bash

echo "=========================================="
echo "  小思超级NAS服务启动脚本"
echo "  第二代 · Python实现 · 零依赖"
echo "=========================================="
echo ""

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[错误] 未检测到Python，请先安装Python 3.6+"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# 显示Python版本
PYTHON_VER=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "[信息] Python版本: $PYTHON_VER"
echo ""

# 设置端口（默认8080）
NAS_PORT=${1:-8080}

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo "[信息] 启动NAS服务..."
echo "[信息] 服务端口: $NAS_PORT"
echo ""
echo "=========================================="
echo "  按 Ctrl+C 可停止服务"
echo "=========================================="
echo ""

# 启动服务器
$PYTHON_CMD nas_server.py $NAS_PORT