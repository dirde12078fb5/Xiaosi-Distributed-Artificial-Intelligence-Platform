#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台支持模块 - 增强版
"""

import os
import sys
import platform
import subprocess
import logging
import re

logger = logging.getLogger('SuperPXE.Platform')

def get_platform_info():
    """获取平台信息"""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version()
    }

def is_windows():
    """判断是否为Windows系统"""
    return platform.system() == 'Windows'

def is_linux():
    """判断是否为Linux系统"""
    return platform.system() == 'Linux'

def is_macos():
    """判断是否为macOS系统"""
    return platform.system() == 'Darwin'

def get_network_interfaces():
    """获取网络接口列表"""
    interfaces = []
    
    try:
        if is_windows():
            interfaces = _get_windows_interfaces()
        elif is_linux():
            interfaces = _get_linux_interfaces()
        elif is_macos():
            interfaces = _get_macos_interfaces()
    except Exception as e:
        logger.error(f"获取网络接口失败: {e}")
    
    return interfaces

def _get_windows_interfaces():
    """获取Windows网络接口"""
    interfaces = []
    
    try:
        import wmi
        c = wmi.WMI()
        for interface in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            if interface.IPAddress:
                interfaces.append({
                    'name': interface.Description,
                    'ip_addresses': interface.IPAddress,
                    'mac_address': interface.MACAddress,
                    'enabled': True
                })
        return interfaces
    except ImportError:
        pass
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', 
             'Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notmatch "Loopback"} | Select-Object InterfaceAlias, IPAddress | ConvertTo-Json'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            import json
            try:
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    if 'IPAddress' in item and item['IPAddress']:
                        interfaces.append({
                            'name': item.get('InterfaceAlias', 'Unknown'),
                            'ip_addresses': [item['IPAddress']],
                            'mac_address': None,
                            'enabled': True
                        })
                if interfaces:
                    return interfaces
            except json.JSONDecodeError:
                pass
    except Exception as e:
        logger.debug(f"PowerShell获取网卡失败: {e}")
    
    try:
        result = subprocess.run(
            ['ipconfig', '/all'],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore',
            timeout=5
        )
        if result.returncode == 0:
            current_adapter = None
            current_ips = []
            
            for line in result.stdout.split('\n'):
                line_clean = line.strip()
                
                if 'adapter' in line_clean.lower() or '适配器' in line_clean:
                    if current_adapter and current_ips:
                        interfaces.append({
                            'name': current_adapter,
                            'ip_addresses': current_ips,
                            'mac_address': None,
                            'enabled': True
                        })
                    parts = line_clean.split(':')
                    if len(parts) > 0:
                        current_adapter = parts[0].strip()
                        current_ips = []
                
                if line_clean.startswith('IPv4') or line_clean.startswith('本地链接 IPv4'):
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line_clean)
                    if match and current_adapter:
                        current_ips.append(match.group(1))
            
            if current_adapter and current_ips:
                interfaces.append({
                    'name': current_adapter,
                    'ip_addresses': current_ips,
                    'mac_address': None,
                    'enabled': True
                })
            
            return interfaces
    except Exception as e:
        logger.error(f"ipconfig方式获取网络接口失败: {e}")
    
    return interfaces

def _get_linux_interfaces():
    """获取Linux网络接口"""
    interfaces = []
    
    try:
        import netifaces
        for iface in netifaces.interfaces():
            if iface == 'lo':
                continue
            addrs = netifaces.ifaddresses(iface)
            ip_addresses = []
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip_addresses.append(addr['addr'])
            
            mac_address = None
            if netifaces.AF_LINK in addrs:
                mac_address = addrs[netifaces.AF_LINK][0]['addr']
            
            if ip_addresses:
                interfaces.append({
                    'name': iface,
                    'ip_addresses': ip_addresses,
                    'mac_address': mac_address,
                    'enabled': True
                })
        return interfaces
    except ImportError:
        pass
    
    try:
        result = subprocess.run(
            ['ip', 'addr', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            current_iface = None
            current_ips = []
            
            for line in result.stdout.split('\n'):
                if line.strip().startswith(('1:', '2:', '3:', '4:', '5:', '6:')):
                    if current_iface and current_ips:
                        interfaces.append({
                            'name': current_iface,
                            'ip_addresses': current_ips,
                            'mac_address': None,
                            'enabled': True
                        })
                    parts = line.split(':')
                    if len(parts) >= 2:
                        current_iface = parts[1].strip().split('@')[0]
                        current_ips = []
                
                elif 'inet ' in line and current_iface:
                    match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        current_ips.append(match.group(1))
            
            if current_iface and current_ips:
                interfaces.append({
                    'name': current_iface,
                    'ip_addresses': current_ips,
                    'mac_address': None,
                    'enabled': True
                })
            
            return interfaces
    except Exception as e:
        logger.error(f"获取Linux网络接口失败: {e}")
    
    return interfaces

def _get_macos_interfaces():
    """获取macOS网络接口"""
    interfaces = []
    try:
        result = subprocess.run(
            ['ifconfig'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            current_iface = None
            current_ips = []
            
            for line in result.stdout.split('\n'):
                if not line.startswith(' ') and line.strip():
                    if current_iface and current_ips:
                        interfaces.append({
                            'name': current_iface,
                            'ip_addresses': current_ips,
                            'mac_address': None,
                            'enabled': True
                        })
                    current_iface = line.split(':')[0].strip()
                    current_ips = []
                
                elif 'inet ' in line and current_iface:
                    match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        current_ips.append(match.group(1))
            
            if current_iface and current_ips:
                interfaces.append({
                    'name': current_iface,
                    'ip_addresses': current_ips,
                    'mac_address': None,
                    'enabled': True
                })
            
            return interfaces
    except Exception as e:
        logger.error(f"获取macOS网络接口失败: {e}")
    
    return interfaces

def get_interface_by_ip(ip_address):
    """根据IP地址查找对应的网络接口"""
    interfaces = get_network_interfaces()
    for iface in interfaces:
        if ip_address in iface['ip_addresses']:
            return iface
    return None

def check_admin_privileges():
    """检查是否有管理员/root权限"""
    if is_windows():
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0

def elevate_privileges():
    """请求提升权限"""
    if check_admin_privileges():
        return True
    
    if is_windows():
        try:
            import ctypes
            import sys
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        except Exception as e:
            logger.error(f"提升Windows权限失败: {e}")
            return False
    else:
        try:
            os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
        except Exception as e:
            logger.error(f"提升Linux/macOS权限失败: {e}")
            return False
    
    return False

def open_firewall_port(port, protocol='tcp'):
    """打开防火墙端口"""
    try:
        if is_windows():
            return _open_windows_firewall(port, protocol)
        elif is_linux():
            return _open_linux_firewall(port, protocol)
        elif is_macos():
            return _open_macos_firewall(port, protocol)
    except Exception as e:
        logger.error(f"打开防火墙端口失败: {e}")
    
    return False

def _open_windows_firewall(port, protocol):
    """打开Windows防火墙端口"""
    try:
        rule_name = f"SuperPXE_{protocol}_{port}"
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}',
            'dir=in',
            'action=allow',
            f'protocol={protocol}',
            f'localport={port}'
        ], check=True, capture_output=True)
        logger.info(f"已打开Windows防火墙端口 {port}/{protocol}")
        return True
    except Exception as e:
        logger.error(f"打开Windows防火墙端口失败: {e}")
        return False

def _open_linux_firewall(port, protocol):
    """打开Linux防火墙端口"""
    try:
        result = subprocess.run(
            ['which', 'firewall-cmd'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            subprocess.run([
                'firewall-cmd', '--permanent',
                f'--add-port={port}/{protocol}'
            ], check=True, capture_output=True)
            subprocess.run(['firewall-cmd', '--reload'], check=True, capture_output=True)
            logger.info(f"已打开firewalld端口 {port}/{protocol}")
            return True
        
        result = subprocess.run(
            ['which', 'ufw'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            subprocess.run(['ufw', 'allow', f'{port}/{protocol}'], check=True, capture_output=True)
            logger.info(f"已打开UFW端口 {port}/{protocol}")
            return True
        
        logger.warning("未检测到Linux防火墙管理工具")
        return False
    except Exception as e:
        logger.error(f"打开Linux防火墙端口失败: {e}")
        return False

def _open_macos_firewall(port, protocol):
    """打开macOS防火墙端口"""
    try:
        logger.info("macOS防火墙需要手动配置")
        return False
    except Exception as e:
        logger.error(f"打开macOS防火墙端口失败: {e}")
        return False

def get_local_ip():
    """获取本地IP地址"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"获取本地IP失败: {e}")
        return '127.0.0.1'
