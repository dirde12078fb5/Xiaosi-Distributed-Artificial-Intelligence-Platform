#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE - DHCP服务器 (完全重写版)
高度兼容的跨平台DHCP服务器
"""

import socket
import struct
import threading
import logging
import platform
import time
from datetime import datetime, timedelta

logger = logging.getLogger('SuperPXE.DHCP')


class DHCPLease:
    """DHCP租约管理"""
    def __init__(self, mac, ip, lease_time=3600):
        self.mac = mac.lower()
        self.ip = ip
        self.lease_time = lease_time
        self.start_time = datetime.now()
        self.expiry_time = self.start_time + timedelta(seconds=lease_time)
    
    def is_expired(self):
        return datetime.now() > self.expiry_time
    
    def __repr__(self):
        return f"<DHCPLease {self.mac} -> {self.ip}>"


class DHCPServer:
    """DHCP服务器 - 完全重写版"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.get('enabled', True)
        
        if not self.enabled:
            logger.info("DHCP服务已禁用")
            return
        
        self.interface = config.get('interface', '0.0.0.0')
        self.port = config.get('port', 67)
        self.server_ip = config.get('server_ip', '0.0.0.0')
        
        if self.server_ip == '0.0.0.0' or not self.server_ip:
            self.server_ip = self._guess_server_ip()
        
        self.start_ip = config.get('start_ip', '192.168.1.100')
        self.end_ip = config.get('end_ip', '192.168.1.200')
        self.subnet_mask = config.get('subnet_mask', '255.255.255.0')
        self.gateway = config.get('gateway', self.server_ip)
        self.dns_servers = config.get('dns_servers', ['8.8.8.8', '8.8.4.4'])
        self.boot_file = config.get('boot_file', 'pxelinux.0')
        self.lease_time = config.get('lease_time', 3600)
        
        self.running = False
        self.socket = None
        self.thread = None
        self.leases = {}
        self.used_ips = set()
        
        self._init_ip_pool()
        
        logger.info(f"DHCP服务器初始化完成: {self.server_ip}:{self.port}")
    
    def _guess_server_ip(self):
        """自动猜测服务器IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.warning(f"无法自动获取IP: {e}，使用192.168.1.1")
            return '192.168.1.1'
    
    def _init_ip_pool(self):
        """初始化IP池"""
        try:
            start = self._ip_to_int(self.start_ip)
            end = self._ip_to_int(self.end_ip)
            self.ip_pool = [self._int_to_ip(ip) for ip in range(start, end + 1)]
            logger.info(f"IP池初始化: {len(self.ip_pool)} 个IP地址 ({self.start_ip} - {self.end_ip})")
        except Exception as e:
            logger.error(f"IP池初始化失败: {e}")
            self.ip_pool = []
    
    def _ip_to_int(self, ip_str):
        """IP字符串转整数"""
        return struct.unpack('!I', socket.inet_aton(ip_str))[0]
    
    def _int_to_ip(self, ip_int):
        """整数转IP字符串"""
        return socket.inet_ntoa(struct.pack('!I', ip_int))
    
    def _get_next_ip(self, mac):
        """获取下一个可用IP"""
        mac_key = mac.lower()
        
        if mac_key in self.leases:
            lease = self.leases[mac_key]
            if not lease.is_expired():
                logger.debug(f"返回已分配IP: {mac} -> {lease.ip}")
                return lease.ip
            else:
                logger.debug(f"租约已过期，重新分配: {mac}")
                self.used_ips.discard(lease.ip)
                del self.leases[mac_key]
        
        for ip in self.ip_pool:
            if ip not in self.used_ips:
                logger.debug(f"分配新IP: {mac} -> {ip}")
                return ip
        
        logger.warning("IP池耗尽!")
        return None
    
    def _assign_lease(self, mac, ip):
        """分配租约"""
        mac_key = mac.lower()
        if mac_key in self.leases:
            self.used_ips.discard(self.leases[mac_key].ip)
        
        lease = DHCPLease(mac, ip, self.lease_time)
        self.leases[mac_key] = lease
        self.used_ips.add(ip)
        logger.info(f"✅ 租约分配: {mac} -> {ip}")
        return lease
    
    def _parse_dhcp_message(self, data):
        """解析DHCP消息"""
        if len(data) < 240:
            return None
        
        op = data[0]
        htype = data[1]
        hlen = data[2]
        hops = data[3]
        xid = struct.unpack('!I', data[4:8])[0]
        secs = struct.unpack('!H', data[8:10])[0]
        flags = struct.unpack('!H', data[10:12])[0]
        ciaddr = socket.inet_ntoa(data[12:16])
        yiaddr = socket.inet_ntoa(data[16:20])
        siaddr = socket.inet_ntoa(data[20:24])
        giaddr = socket.inet_ntoa(data[24:28])
        chaddr = data[28:28 + hlen]
        
        options = {}
        ptr = 240
        while ptr < len(data) and data[ptr] != 255:
            if data[ptr] == 0:
                ptr += 1
                continue
            if ptr + 2 > len(data):
                break
            code = data[ptr]
            length = data[ptr + 1]
            if ptr + 2 + length > len(data):
                break
            option_data = data[ptr + 2:ptr + 2 + length]
            options[code] = option_data
            ptr += 2 + length
        
        return {
            'op': op,
            'htype': htype,
            'hlen': hlen,
            'hops': hops,
            'xid': xid,
            'secs': secs,
            'flags': flags,
            'ciaddr': ciaddr,
            'yiaddr': yiaddr,
            'siaddr': siaddr,
            'giaddr': giaddr,
            'chaddr': chaddr,
            'options': options
        }
    
    def _mac_to_str(self, mac_bytes):
        """MAC字节转字符串"""
        return ':'.join(f'{b:02x}' for b in mac_bytes)
    
    def _build_dhcp_response(self, msg_type, request):
        """构建DHCP响应"""
        client_mac = request['chaddr']
        mac_str = self._mac_to_str(client_mac)
        xid = request['xid']
        
        yiaddr = self._get_next_ip(mac_str)
        if not yiaddr:
            logger.error("无法分配IP地址，IP池耗尽")
            return None
        
        response = bytearray()
        
        response.append(2)
        response.append(1)
        response.append(6)
        response.append(0)
        
        response.extend(struct.pack('!I', xid))
        response.extend(struct.pack('!H', 0))
        response.extend(struct.pack('!H', 0x8000))
        
        response.extend(socket.inet_aton('0.0.0.0'))
        response.extend(socket.inet_aton(yiaddr))
        response.extend(socket.inet_aton(self.server_ip))
        response.extend(socket.inet_aton('0.0.0.0'))
        
        response.extend(client_mac)
        response.extend(b'\x00' * (16 - len(client_mac)))
        response.extend(b'\x00' * 64)
        response.extend(b'\x00' * 128)
        
        response.extend(b'\x63\x82\x53\x63')
        
        response.append(53)
        response.append(1)
        response.append(msg_type)
        
        response.append(54)
        response.append(4)
        response.extend(socket.inet_aton(self.server_ip))
        
        response.append(1)
        response.append(4)
        response.extend(socket.inet_aton(self.subnet_mask))
        
        response.append(3)
        response.append(4)
        response.extend(socket.inet_aton(self.gateway))
        
        response.append(6)
        response.append(len(self.dns_servers) * 4)
        for dns in self.dns_servers:
            response.extend(socket.inet_aton(dns))
        
        response.append(51)
        response.append(4)
        response.extend(struct.pack('!I', self.lease_time))
        
        response.append(67)
        boot_file_bytes = self.boot_file.encode('ascii')
        response.append(len(boot_file_bytes))
        response.extend(boot_file_bytes)
        
        response.append(255)
        
        if msg_type == 5:
            self._assign_lease(mac_str, yiaddr)
        
        return bytes(response)
    
    def _handle_packet(self, data, addr):
        """处理接收到的数据包"""
        try:
            request = self._parse_dhcp_message(data)
            if not request:
                return
            
            options = request.get('options', {})
            msg_type = options.get(53)
            
            if not msg_type:
                return
            
            msg_code = msg_type[0]
            mac_str = self._mac_to_str(request['chaddr'])
            
            logger.debug(f"收到DHCP消息: 类型={msg_code}, 来自={mac_str}")
            
            if msg_code == 1:
                logger.info(f"📡 DHCP Discover 来自: {mac_str}")
                response = self._build_dhcp_response(2, request)
                if response:
                    self._send_response(response)
                    logger.info(f"📤 DHCP Offer 发送: {mac_str}")
            
            elif msg_code == 3:
                logger.info(f"📡 DHCP Request 来自: {mac_str}")
                response = self._build_dhcp_response(5, request)
                if response:
                    self._send_response(response)
                    logger.info(f"📤 DHCP ACK 发送: {mac_str}")
        
        except Exception as e:
            logger.error(f"处理DHCP数据包失败: {e}")
    
    def _send_response(self, response_data):
        """发送DHCP响应"""
        if not self.socket:
            return
        
        try:
            self.socket.sendto(response_data, ('255.255.255.255', 68))
        except Exception as e:
            logger.error(f"发送DHCP响应失败: {e}")
    
    def _cleanup_expired(self):
        """清理过期租约"""
        expired = [mac for mac, lease in self.leases.items() if lease.is_expired()]
        for mac in expired:
            ip = self.leases[mac].ip
            logger.info(f"释放过期租约: {mac} -> {ip}")
            self.used_ips.discard(ip)
            del self.leases[mac]
    
    def _server_loop(self):
        """服务器主循环"""
        logger.info("DHCP服务器循环已启动")
        
        last_cleanup = time.time()
        
        while self.running:
            try:
                self.socket.settimeout(1.0)
                try:
                    data, addr = self.socket.recvfrom(2048)
                    logger.debug(f"收到数据: {len(data)} 字节 来自 {addr}")
                    self._handle_packet(data, addr)
                except socket.timeout:
                    if time.time() - last_cleanup > 60:
                        self._cleanup_expired()
                        last_cleanup = time.time()
                except Exception as e:
                    if self.running:
                        logger.error(f"接收数据出错: {e}")
            except Exception as e:
                logger.error(f"DHCP服务器循环出错: {e}")
                time.sleep(1)
        
        logger.info("DHCP服务器循环已停止")
    
    def start(self):
        """启动DHCP服务器"""
        if not self.enabled:
            logger.info("DHCP服务已禁用，不启动")
            return
        
        if self.running:
            logger.warning("DHCP服务器已在运行")
            return
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            if hasattr(socket, 'SO_REUSEPORT'):
                try:
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except Exception:
                    pass
            
            bind_addr = ('', self.port)
            if platform.system() != 'Windows':
                try:
                    self.socket.bind(bind_addr)
                except Exception as e:
                    logger.warning(f"绑定通配符地址失败: {e}，尝试绑定到 {self.server_ip}")
                    bind_addr = (self.server_ip, self.port)
                    self.socket.bind(bind_addr)
            else:
                try:
                    self.socket.bind(bind_addr)
                except Exception as e:
                    logger.warning(f"Windows绑定失败: {e}，尝试绑定到 {self.server_ip}")
                    bind_addr = (self.server_ip, self.port)
                    self.socket.bind(bind_addr)
            
            logger.info(f"✅ DHCP服务器已绑定到: {bind_addr[0]}:{bind_addr[1]}")
            
            self.running = True
            self.thread = threading.Thread(target=self._server_loop, daemon=True, name="DHCP-Server")
            self.thread.start()
            
            logger.info("🚀 DHCP服务器启动成功!")
        
        except PermissionError:
            logger.error("❌ 权限不足！请以管理员/root权限运行！")
            raise
        except OSError as e:
            if e.errno in (98, 10048):
                logger.error(f"❌ 端口 {self.port} 已被占用！请检查是否有其他DHCP服务在运行")
                logger.error("   检查命令: Windows: netstat -ano | findstr :67")
                logger.error("                Linux: sudo netstat -ulpn | grep :67")
            else:
                logger.error(f"❌ DHCP服务器启动失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ DHCP服务器启动失败: {e}")
            raise
    
    def stop(self):
        """停止DHCP服务器"""
        if not self.enabled:
            return
        
        logger.info("正在停止DHCP服务器...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.debug(f"关闭Socket出错: {e}")
            self.socket = None
        
        logger.info("✅ DHCP服务器已停止")
