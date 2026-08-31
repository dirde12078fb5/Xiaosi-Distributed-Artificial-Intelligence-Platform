#!/usr/bin/env bash
# 小思分布式人工智能平台 - 启动选单 (Linux / macOS)
set -u
cd "$(dirname "$0")/.."

while true; do
    clear
    echo "============================================================"
    echo "  小思分布式人工智能平台 - 启动选单 (Linux / macOS)"
    echo "============================================================"
    echo
    echo "  1. 网络管理模块   (WiFi 扫描 / 网络工具 GUI)"
    echo "  2. 视觉管理模块   (摄像头 / 图像处理 GUI)"
    echo "  3. 服务管理 - 内网通服"
    echo "  4. 服务管理 - 外网通服"
    echo "  5. 小思超级 PXE    (网络安装系统 GUI)"
    echo "  0. 退出"
    echo
    read -r -p "请输入编号后回车: " c
    case "$c" in
        1) python3 "小思分布式人工智能网络模块.py" ;;
        2) python3 "小思分布式视觉管理模块.py" ;;
        3) python3 "内网通服.py" ;;
        4) python3 "外网通服.py" ;;
        5) (cd "小思超级服务/小思超级PXE" && python3 gui.py) ;;
        0) exit 0 ;;
        *) continue ;;
    esac
    echo
    read -r -n 1 -p "已退出该模块，按任意键返回选单 ..." _
done
