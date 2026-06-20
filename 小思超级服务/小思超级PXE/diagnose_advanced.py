#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE - 高级诊断与修复工具
用于彻底解决DHCP和TFTP连接问题
"""

import socket
import sys
import os
import platform
import json
import time
import subprocess
import threading
from pathlib import Path


class DHCPTester:
    """DHCP测试器"""
    @staticmethod
    def test_bind_udp_port(port, bind_ip='0.0.0.0'):
        """测试绑定UDP端口"""
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            if platform.system() == 'Windows':
                try:
                    s.bind(('', port))
                except:
                    s.bind((bind_ip, port))
            else:
                try:
                    s.bind(('', port))
                except:
                    s.bind((bind_ip, port))
            
            return True, f"✅ 端口 {port} 绑定成功"
        except PermissionError:
            return False, f"❌ 端口 {port} - 权限不足，请以管理员/root权限运行"
        except OSError as e:
            if e.errno in (98, 10048):
                return False, f"❌ 端口 {port} - 已被占用"
            return False, f"❌ 端口 {port} - {e}"
        finally:
            if s:
                s.close()
    
    @staticmethod
    def test_broadcast():
        """测试广播功能"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(0.5)
            
            try:
                s.bind(('0.0.0.0', 6868))
            except:
                pass
            
            try:
                s.sendto(b'test', ('255.255.255.255', 6969))
            except Exception:
                pass
            
            s.close()
            return True, "✅ 广播功能正常"
        except Exception as e:
            return False, f"❌ 广播测试失败: {e}"


class FirewallManager:
    """防火墙管理器"""
    @staticmethod
    def check_and_open_ports():
        """检查并打开防火墙端口"""
        results = []
        ports = [
            (67, 'udp', 'DHCP服务器'),
            (68, 'udp', 'DHCP客户端'),
            (69, 'udp', 'TFTP'),
            (8080, 'tcp', 'HTTP')
        ]
        
        for port, proto, name in ports:
            status, msg = FirewallManager._open_port(port, proto, name)
            results.append(msg)
        
        return results
    
    @staticmethod
    def _open_port(port, proto, name):
        """打开单个端口"""
        system = platform.system()
        
        if system == 'Windows':
            return FirewallManager._windows_open_port(port, proto, name)
        elif system == 'Linux':
            return FirewallManager._linux_open_port(port, proto, name)
        elif system == 'Darwin':
            return FirewallManager._macos_open_port(port, proto, name)
        else:
            return False, f"⚠️ 不支持的平台: {system}"
    
    @staticmethod
    def _windows_open_port(port, proto, name):
        """Windows打开端口"""
        try:
            rule_name = f"SuperPXE_{name}_{port}"
            result = subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={rule_name}'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return True, f"✅ Windows防火墙规则已存在: {name} ({port}/{proto})"
            
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                f'name={rule_name}', 'dir=in', 'action=allow',
                f'protocol={proto}', f'localport={port}'
            ], capture_output=True, check=True, timeout=10)
            
            return True, f"✅ Windows防火墙已打开: {name} ({port}/{proto})"
        except Exception as e:
            return False, f"❌ Windows防火墙配置失败: {name} ({port}/{proto}) - {e}"
    
    @staticmethod
    def _linux_open_port(port, proto, name):
        """Linux打开端口"""
        try:
            result = subprocess.run(['which', 'ufw'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                subprocess.run(['ufw', 'allow', f'{port}/{proto}'], capture_output=True, timeout=5)
                return True, f"✅ UFW防火墙已打开: {name} ({port}/{proto})"
            
            result = subprocess.run(['which', 'firewall-cmd'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                subprocess.run([
                    'firewall-cmd', '--permanent', f'--add-port={port}/{proto}'
                ], capture_output=True, timeout=5)
                subprocess.run(['firewall-cmd', '--reload'], capture_output=True, timeout=5)
                return True, f"✅ firewalld已打开: {name} ({port}/{proto})"
            
            return True, f"⚠️ 未检测到防火墙管理工具，需要手动配置: {name} ({port}/{proto})"
        except Exception as e:
            return False, f"❌ Linux防火墙配置失败: {name} ({port}/{proto}) - {e}"
    
    @staticmethod
    def _macos_open_port(port, proto, name):
        """macOS打开端口"""
        try:
            return True, f"⚠️ macOS防火墙需要手动打开: {name} ({port}/{proto})"
        except Exception as e:
            return False, f"❌ macOS防火墙配置失败: {name} ({port}/{proto}) - {e}"


def check_admin():
    """检查管理员权限"""
    if platform.system() == 'Windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0


def get_local_ip():
    """获取本地IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def print_section(title):
    """打印分区标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "🔧 小思超级PXE - 高级诊断工具" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n正在执行全面诊断和修复...\n")
    
    results = []
    
    # 1. 系统信息
    print_section("1. 系统信息")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    print(f"本地IP: {get_local_ip()}")
    
    # 2. 权限检查
    print_section("2. 权限检查")
    if check_admin():
        print("✅ 已获得管理员/root权限")
        results.append(("admin", True))
    else:
        print("❌ 未获得管理员/root权限 - 这是最常见的问题!")
        print("   请以管理员身份运行程序")
        results.append(("admin", False))
    
    # 3. 端口绑定测试
    print_section("3. 端口绑定测试")
    port_tests = [
        (67, 'DHCP服务器'),
        (68, 'DHCP客户端'),
        (69, 'TFTP'),
        (8080, 'HTTP')
    ]
    
    for port, name in port_tests:
        ok, msg = DHCPTester.test_bind_udp_port(port)
        print(msg)
        results.append((name, ok))
    
    # 4. 广播测试
    print_section("4. 广播功能测试")
    ok, msg = DHCPTester.test_broadcast()
    print(msg)
    results.append(("broadcast", ok))
    
    # 5. 防火墙配置
    print_section("5. 防火墙自动配置")
    firewall_results = FirewallManager.check_and_open_ports()
    for res in firewall_results:
        print(res)
    
    # 6. 配置文件检查
    print_section("6. 配置文件检查")
    config_path = Path('config.json')
    if not config_path.exists():
        example = Path('config.example.json')
        if example.exists():
            import shutil
            shutil.copy(example, config_path)
            print("✅ 已自动创建 config.json")
        else:
            print("❌ 找不到 config.example.json")
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            dhcp = config.get('dhcp', {})
            print(f"   DHCP服务器IP: {dhcp.get('server_ip', '未设置')}")
            print(f"   DHCP起始IP: {dhcp.get('start_ip', '未设置')}")
            print(f"   DHCP结束IP: {dhcp.get('end_ip', '未设置')}")
            print(f"   网关: {dhcp.get('gateway', '未设置')}")
            
            if not dhcp.get('server_ip') or dhcp.get('server_ip') == '192.168.1.1':
                local_ip = get_local_ip()
                if local_ip != '127.0.0.1':
                    print(f"\n⚠️ 自动将服务器IP更新为: {local_ip}")
                    config['dhcp']['server_ip'] = local_ip
                    
                    gateway_parts = local_ip.split('.')
                    gateway_parts[3] = '1'
                    suggested_gateway = '.'.join(gateway_parts)
                    
                    start_parts = local_ip.split('.')
                    start_parts[3] = '100'
                    suggested_start = '.'.join(start_parts)
                    
                    end_parts = local_ip.split('.')
                    end_parts[3] = '200'
                    suggested_end = '.'.join(end_parts)
                    
                    if not dhcp.get('gateway') or dhcp.get('gateway') == '192.168.1.1':
                        config['dhcp']['gateway'] = suggested_gateway
                    
                    if not dhcp.get('start_ip') or dhcp.get('start_ip') == '192.168.1.100':
                        config['dhcp']['start_ip'] = suggested_start
                    
                    if not dhcp.get('end_ip') or dhcp.get('end_ip') == '192.168.1.200':
                        config['dhcp']['end_ip'] = suggested_end
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=4, ensure_ascii=False)
                    
                    print("✅ 配置已自动优化")
        except Exception as e:
            print(f"❌ 配置文件处理失败: {e}")
    
    # 7. 目录检查
    print_section("7. 目录检查")
    directories = ['tftpboot', 'httpboot', 'tftpboot/pxelinux.cfg']
    for d in directories:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 已创建目录: {d}")
        else:
            print(f"✅ 目录存在: {d}")
    
    # 8. 总结
    print_section("8. 诊断总结")
    print("\n📋 检查结果:")
    
    all_ok = True
    for name, ok in results:
        if name == 'admin' and not ok:
            print("   ❌ 缺少管理员/root权限 (关键问题)")
            all_ok = False
        elif not ok:
            print(f"   ⚠️ {name} 存在问题")
    
    if all_ok and check_admin():
        print("\n🎉 所有检查通过!")
        print("\n下一步:")
        print("  1. 运行: python gui.py")
        print("  2. 选择正确的网卡")
        print("  3. 启动服务器")
    else:
        print("\n⚠️ 发现问题，请按以下步骤修复:")
        if not check_admin():
            print("  1. 以管理员/root身份重新运行此程序")
        print("  2. 检查是否有其他程序占用端口 (特别是DHCP服务)")
        print("  3. 确保客户端和服务器在同一网络")
    
    print("\n" + "=" * 70)
    print("\n诊断完成！\n")


if __name__ == '__main__':
    main()
