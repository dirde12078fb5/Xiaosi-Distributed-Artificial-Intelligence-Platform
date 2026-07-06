#!/bin/bash

echo "=================================================="
echo "  小思超级NAS服务启动 - Node.js版本"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "[错误] 未检测到Node.js环境，请先安装Node.js"
    echo "安装方法:"
    echo "  Ubuntu/Debian: sudo apt install nodejs npm"
    echo "  CentOS/RHEL:   sudo yum install nodejs npm"
    echo "  macOS:         brew install node"
    exit 1
fi

echo "Node.js版本: $(node --version)"
echo ""

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "未安装依赖，正在安装express..."
    npm install express --production
fi

echo ""
echo "启动NAS服务..."
echo "服务端口: 8081"
echo "访问地址: http://localhost:8081"
echo ""

node server.js