#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE - TFTP服务器 (完全重写版)
高度兼容的跨平台TFTP服务器
"""

import socket
import struct
import threading
import logging
import platform
import os
from pathlib import Path

logger = logging.getLogger('SuperPXE.TFTP')


class TFTPSession:
    """TFTP会话"""
    
    def __init__(self, server, client_addr, filename, mode):
        self.server = server
        self.client_addr = client_addr
        self.filename = filename
        self.mode = mode
        self.block_num = 1
        self.finished = False
        self.file = None
        self.file_size = 0
        self.bytes_sent = 0
        self.socket = None
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(5.0)
        except Exception as e:
            logger.error(f"创建会话Socket失败: {e}")
            self.socket = None
    
    def send_data(self, data):
        """发送数据"""
        if not self.socket:
            return False
        
        try:
            self.socket.sendto(data, self.client_addr)
            return True
        except Exception as e:
            logger.error(f"发送数据失败: {e}")
            return False
    
    def recv_data(self):
        """接收数据"""
        if not self.socket:
            return None
        
        try:
            data, addr = self.socket.recvfrom(1024)
            return data
        except socket.timeout:
            logger.debug("接收超时")
            return None
        except Exception as e:
            logger.error(f"接收数据失败: {e}")
            return None
    
    def open_file(self):
        """打开文件"""
        try:
            safe_filename = Path(self.filename).name
            filepath = self.server.root_dir / safe_filename
            
            if not filepath.exists():
                logger.error(f"文件不存在: {self.filename}")
                return False
            
            if not str(filepath.resolve()).startswith(str(self.server.root_dir.resolve())):
                logger.error(f"访问被拒绝: {self.filename}")
                return False
            
            self.file = open(filepath, 'rb')
            self.file_size = os.path.getsize(filepath)
            logger.info(f"📂 打开文件: {safe_filename} ({self.file_size} 字节)")
            return True
        
        except Exception as e:
            logger.error(f"打开文件失败: {e}")
            return False
    
    def send_error(self, error_code, error_msg):
        """发送错误包"""
        try:
            error_packet = struct.pack('!HH', 5, error_code) + error_msg.encode('ascii') + b'\x00'
            self.send_data(error_packet)
        except Exception as e:
            logger.error(f"发送错误包失败: {e}")
    
    def send_data_packet(self):
        """发送数据包"""
        try:
            data = self.file.read(512)
            packet = struct.pack('!HH', 3, self.block_num) + data
            self.send_data(packet)
            self.bytes_sent += len(data)
            
            if len(data) < 512:
                self.finished = True
                logger.info(f"✅ 文件传输完成: {self.filename}")
            
            return len(data)
        except Exception as e:
            logger.error(f"发送数据包失败: {e}")
            return 0
    
    def run(self):
        """运行会话"""
        if not self.socket:
            return
        
        if not self.open_file():
            self.send_error(1, 'File not found')
            self.close()
            return
        
        retries = 3
        while retries > 0 and not self.finished:
            self.send_data_packet()
            
            ack = self.recv_data()
            if ack and len(ack) >= 4:
                opcode = struct.unpack('!H', ack[:2])[0]
                if opcode == 4:
                    block = struct.unpack('!H', ack[2:4])[0]
                    if block == self.block_num:
                        self.block_num += 1
                        retries = 3
                        continue
            
            retries -= 1
            logger.debug(f"重试 ({retries}/3): 块 {self.block_num}")
        
        self.close()
    
    def close(self):
        """关闭会话"""
        if self.file:
            self.file.close()
        if self.socket:
            self.socket.close()


class TFTPServer:
    """TFTP服务器 - 完全重写版"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.get('enabled', True)
        
        if not self.enabled:
            logger.info("TFTP服务已禁用")
            return
        
        self.interface = config.get('interface', '0.0.0.0')
        self.port = config.get('port', 69)
        self.root_dir = Path(config.get('root_dir', './tftpboot')).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        
        self.running = False
        self.socket = None
        self.thread = None
        self.sessions = []
        
        logger.info(f"TFTP服务器初始化完成: {self.root_dir}")
    
    def _create_dirs(self):
        """创建必要的目录"""
        if not self.root_dir.exists():
            self.root_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建TFTP根目录: {self.root_dir}")
        
        pxelinux_cfg = self.root_dir / 'pxelinux.cfg'
        if not pxelinux_cfg.exists():
            pxelinux_cfg.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建pxelinux.cfg目录: {pxelinux_cfg}")
    
    def _handle_request(self, data, addr):
        """处理TFTP请求"""
        try:
            if len(data) < 4:
                logger.warning("收到无效的TFTP请求")
                return
            
            opcode = struct.unpack('!H', data[:2])[0]
            
            if opcode == 1:
                logger.info(f"📥 TFTP读请求来自 {addr}")
                
                ptr = 2
                filename_end = data.find(b'\x00', ptr)
                if filename_end == -1:
                    return
                filename = data[ptr:filename_end].decode('ascii', errors='ignore')
                
                ptr = filename_end + 1
                mode_end = data.find(b'\x00', ptr)
                if mode_end == -1:
                    mode = 'octet'
                else:
                    mode = data[ptr:mode_end].decode('ascii', errors='ignore')
                
                logger.info(f"请求文件: {filename} (模式: {mode})")
                
                session = TFTPSession(self, addr, filename, mode)
                session_thread = threading.Thread(target=session.run, daemon=True)
                session_thread.start()
                self.sessions.append(session)
            
            elif opcode == 2:
                logger.warning("TFTP写请求不支持")
        
        except Exception as e:
            logger.error(f"处理TFTP请求失败: {e}")
    
    def _server_loop(self):
        """服务器主循环"""
        logger.info("TFTP服务器循环已启动")
        
        while self.running:
            try:
                self.socket.settimeout(1.0)
                try:
                    data, addr = self.socket.recvfrom(1024)
                    logger.debug(f"收到TFTP数据: {len(data)} 字节 来自 {addr}")
                    self._handle_request(data, addr)
                except socket.timeout:
                    self.sessions = [s for s in self.sessions if not s.finished]
                except Exception as e:
                    if self.running:
                        logger.error(f"接收TFTP数据出错: {e}")
            except Exception as e:
                logger.error(f"TFTP服务器循环出错: {e}")
                import time
                time.sleep(1)
        
        logger.info("TFTP服务器循环已停止")
    
    def start(self):
        """启动TFTP服务器"""
        if not self.enabled:
            logger.info("TFTP服务已禁用，不启动")
            return
        
        if self.running:
            logger.warning("TFTP服务器已在运行")
            return
        
        try:
            self._create_dirs()
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            if hasattr(socket, 'SO_REUSEPORT'):
                try:
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except Exception:
                    pass
            
            bind_addr = ('', self.port)
            
            try:
                self.socket.bind(bind_addr)
            except Exception as e:
                logger.warning(f"绑定通配符地址失败: {e}，尝试其他方式")
                if platform.system() == 'Windows':
                    try:
                        import socket as sock
                        hostname = sock.gethostname()
                        local_ip = sock.gethostbyname(hostname)
                        self.socket.bind((local_ip, self.port))
                    except Exception as e2:
                        logger.error(f"Windows绑定也失败: {e2}")
                        self.socket.bind(('127.0.0.1', self.port))
                else:
                    self.socket.bind(('0.0.0.0', self.port))
            
            logger.info(f"✅ TFTP服务器已绑定到: {bind_addr[0]}:{bind_addr[1]}")
            
            self.running = True
            self.thread = threading.Thread(target=self._server_loop, daemon=True, name="TFTP-Server")
            self.thread.start()
            
            logger.info("🚀 TFTP服务器启动成功!")
        
        except PermissionError:
            logger.error("❌ 权限不足！请以管理员/root权限运行！")
            raise
        except OSError as e:
            if e.errno in (98, 10048):
                logger.error(f"❌ 端口 {self.port} 已被占用！请检查是否有其他TFTP服务在运行")
            else:
                logger.error(f"❌ TFTP服务器启动失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ TFTP服务器启动失败: {e}")
            raise
    
    def stop(self):
        """停止TFTP服务器"""
        if not self.enabled:
            return
        
        logger.info("正在停止TFTP服务器...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.debug(f"关闭Socket出错: {e}")
            self.socket = None
        
        for session in self.sessions:
            session.close()
        
        logger.info("✅ TFTP服务器已停止")
