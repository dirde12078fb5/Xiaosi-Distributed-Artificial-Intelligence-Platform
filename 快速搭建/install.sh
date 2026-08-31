#!/usr/bin/env bash
# 小思分布式人工智能平台 - 一键安装依赖 (Linux / macOS)
set -u
cd "$(dirname "$0")/.."

echo "============================================================"
echo "  小思分布式人工智能平台 - 一键安装依赖 (Linux / macOS)"
echo "============================================================"
echo

echo "[1/4] 检查 python3 ..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "[X] 未检测到 python3，请先安装 Python 3.10+。"
    exit 1
fi
python3 --version

echo
echo "[2/4] 升级 pip ..."
python3 -m pip install --upgrade pip --user 2>/dev/null || python3 -m pip install --upgrade pip

echo
echo "[3/4] 安装各模块依赖 ..."
[ -f "requirements.txt" ]          && pip3 install --user -r "requirements.txt"
[ -f "requirements 视觉模块.txt" ] && pip3 install --user -r "requirements 视觉模块.txt"
[ -f "requirements 服务管理.txt" ] && pip3 install --user -r "requirements 服务管理.txt"

echo
echo "[4/4] 完成！下一步运行：bash 快速搭建/start.sh"
echo
