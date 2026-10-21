#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE - 一键启动工具
自动诊断、配置和启动PXE服务器
"""

import sys
import os
import subprocess
import time
from pathlib import Path


def print_banner():
    """打印启动横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                    🚀 小思超级PXE v2.0                         ║
║              Python跨平台网络安装系统                          ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_diagnose():
    """运行诊断工具"""
    print("🔍 正在运行系统诊断...\n")
    try:
        result = subprocess.run(
            [sys.executable, 'diagnose_advanced.py'],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"诊断工具运行失败: {e}")
        return False


def launch_gui():
    """启动GUI"""
    print("\n🎨 正在启动图形界面...\n")
    try:
        subprocess.Popen([sys.executable, 'gui.py'])
        print("✅ GUI已启动")
        return True
    except Exception as e:
        print(f"启动GUI失败: {e}")
        return False


def main():
    """主函数"""
    print_banner()
    
    # 检查是否在正确目录
    if not Path('gui.py').exists():
        print("❌ 请在项目根目录运行此脚本！")
        time.sleep(2)
        return
    
    # 询问用户
    print("请选择操作:")
    print("  1. 运行诊断工具 (推荐首先运行)")
    print("  2. 启动图形界面 (GUI)")
    print("  3. 同时运行诊断 + 启动GUI")
    print("  4. 退出")
    
    try:
        choice = input("\n请输入选项 (1-4): ").strip()
    except KeyboardInterrupt:
        print("\n已取消")
        return
    
    if choice == '1':
        run_diagnose()
    elif choice == '2':
        launch_gui()
    elif choice == '3':
        ok = run_diagnose()
        if ok:
            input("\n按回车键启动GUI...")
            launch_gui()
    elif choice == '4':
        print("再见！")
    else:
        print("无效的选项")


if __name__ == '__main__':
    main()
