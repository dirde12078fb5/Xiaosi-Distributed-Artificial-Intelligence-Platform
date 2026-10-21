#!/bin/bash

echo "============================================================"
echo "小思NAS服务 (Ruby版) v2.0.0"
echo "============================================================"

cd "$(dirname "$0")"

echo "正在检查Ruby环境..."
if ! command -v ruby &> /dev/null; then
    echo "[错误] 未找到Ruby，请先安装Ruby"
    echo "安装方法: https://www.ruby-lang.org/zh_cn/documentation/installation/"
    exit 1
fi

echo "Ruby版本:"
ruby --version
echo

echo "正在安装依赖..."
if [ -f "Gemfile" ]; then
    gem install bundler --quiet 2>/dev/null || true
    bundle install --quiet 2>/dev/null || true
fi
echo

echo "正在启动服务..."
echo "服务地址: http://localhost:8087"
echo "按 Ctrl+C 停止服务"
echo "============================================================"
echo

ruby server.rb