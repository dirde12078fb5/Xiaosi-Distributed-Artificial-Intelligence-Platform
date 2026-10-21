#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE - 诊断工具
用于检查DHCP/TFTP/HTTP服务器的运行环境
"""

import socket
import sys
import os
import platform
import json
from pathlib import Path

def print_header(title):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_platform():
    print_header("1. 系统信息")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    print(f"机器架构: {platform.machine()}")
    return platform.system()

def check_privileges():
    print_header("2. 权限检查")
    is_admin = False
    
    if platform.system() == 'Windows':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            pass
        print(f"管理员权限: {'✅ 已获得' if is_admin else '❌ 未获得 (需要管理员权限)'}")
    else:
        is_admin = os.geteuid() == 0
        print(f"Root权限: {'✅ 已获得' if is_admin else '❌ 未获得 (需要sudo)'}")
    
    if not is_admin:
        print("\n⚠️  警告: 没有足够的权限绑定低端口 (67/68/69)!")
        print("   请以管理员/root身份重新运行程序。")
    return is_admin

def check_network_interfaces():
    print_header("3. 网络接口")
    interfaces = []
    try:
        if platform.system() == 'Windows':
            import subprocess
            result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, encoding='gbk', errors='ignore')
            print(result.stdout)
        elif platform.system() == 'Linux':
            import subprocess
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            print(result.stdout)
        elif platform.system() == 'Darwin':
            import subprocess
            result = subprocess.run(['ifconfig', '-a'], capture_output=True, text=True)
            print(result.stdout)
    except Exception as e:
        print(f"获取网络接口信息时出错: {e}")
    
    return interfaces

def check_ports():
    print_header("4. 端口检查")
    ports = [
        (67, 'DHCP服务器'),
        (68, 'DHCP客户端'),
        (69, 'TFTP'),
        (8080, 'HTTP')
    ]
    
    for port, name in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.bind(('0.0.0.0', port))
            print(f"✅ {name} (端口 {port}): 可用")
        except OSError as e:
            if e.errno == 13 or e.errno == 10013:
                print(f"❌ {name} (端口 {port}): 权限不足")
            elif e.errno == 98 or e.errno == 10048:
                print(f"❌ {name} (端口 {port}): 已被占用")
            else:
                print(f"❌ {name} (端口 {port}): {e}")
        finally:
            s.close()

def check_config():
    print_header("5. 配置文件检查")
    config_path = Path('config.json')
    if not config_path.exists():
        config_path = Path('config.example.json')
    
    if config_path.exists():
        print(f"✅ 配置文件存在: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("\n配置内容:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            
            # 验证配置
            dhcp_config = config.get('dhcp', {})
            required = ['start_ip', 'end_ip', 'subnet_mask', 'gateway']
            missing = [k for k in required if k not in dhcp_config]
            if missing:
                print(f"\n⚠️  警告: 缺少DHCP配置项: {missing}")
            
            return config
        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
            return None
    else:
        print("❌ 配置文件不存在")
        return None

def check_directories():
    print_header("6. 目录检查")
    directories = ['tftpboot', 'httpboot', 'tftpboot/pxelinux.cfg']
    
    for d in directories:
        path = Path(d)
        if path.exists() and path.is_dir():
            print(f"✅ 目录存在: {d}")
            if d in ['tftpboot', 'httpboot']:
                files = list(path.iterdir())
                if files:
                    print(f"   文件数量: {len(files)}")
        else:
            print(f"⚠️  目录不存在: {d} (程序会自动创建)")

def check_local_ip():
    print_header("7. 本地IP地址")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"✅ 检测到本地IP: {local_ip}")
        return local_ip
    except Exception as e:
        print(f"❌ 无法获取本地IP: {e}")
        return None

def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "小思超级PXE - 诊断工具" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    check_platform()
    print()
    
    is_admin = check_privileges()
    print()
    
    check_network_interfaces()
    print()
    
    check_ports()
    print()
    
    config = check_config()
    print()
    
    check_directories()
    print()
    
    local_ip = check_local_ip()
    print()
    
    print_header("8. 总结和建议")
    
    issues = []
    
    if not is_admin:
        issues.append("1. 需要以管理员/root身份运行程序")
    
    if not config:
        issues.append("2. 缺少配置文件，请复制 config.example.json 为 config.json")
    
    if not local_ip:
        issues.append("3. 无法检测到网络连接，请检查网络设置")
    
    if issues:
        print("发现以下问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ 系统环境检查通过！")
        print("\n下一步:")
        print("1. 运行 'python gui.py' 启动图形界面")
        print("2. 或运行 'python cli.py server' 启动命令行服务器")
        print("3. 确保防火墙允许相关端口")
    
    print()
    print("=" * 60)
    print()

if __name__ == '__main__':
    main()
