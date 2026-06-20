#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE - Python跨平台网络安装系统
主要功能：DHCP服务器、TFTP服务器、HTTP文件服务器
"""

import os
import sys
import socket
import threading
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SuperPXE')

class SuperPXE:
    def __init__(self, config_path='config.json'):
        self.config = self.load_config(config_path)
        self.services = {}
        self.running = False
        
    def load_config(self, config_path):
        """加载配置文件"""
        default_config = {
            'dhcp': {
                'enabled': True,
                'interface': '0.0.0.0',
                'port': 67,
                'start_ip': '192.168.1.100',
                'end_ip': '192.168.1.200',
                'subnet_mask': '255.255.255.0',
                'gateway': '192.168.1.1',
                'dns_servers': ['8.8.8.8', '8.8.4.4'],
                'boot_file': 'pxelinux.0'
            },
            'tftp': {
                'enabled': True,
                'interface': '0.0.0.0',
                'port': 69,
                'root_dir': './tftpboot'
            },
            'http': {
                'enabled': True,
                'interface': '0.0.0.0',
                'port': 8080,
                'root_dir': './httpboot'
            },
            'log_level': 'INFO'
        }
        
        if os.path.exists(config_path):
            import json
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return default_config
    
    def create_directories(self):
        """创建必要的目录"""
        for service in ['tftp', 'http']:
            if self.config[service]['enabled']:
                dir_path = Path(self.config[service]['root_dir'])
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {dir_path}")
    
    def start_dhcp_server(self):
        """启动DHCP服务器"""
        if not self.config['dhcp']['enabled']:
            logger.info("DHCP服务已禁用")
            return
        
        from servers.dhcp_server import DHCPServer
        dhcp = DHCPServer(self.config['dhcp'])
        self.services['dhcp'] = dhcp
        dhcp.start()
        logger.info("DHCP服务器已启动")
    
    def start_tftp_server(self):
        """启动TFTP服务器"""
        if not self.config['tftp']['enabled']:
            logger.info("TFTP服务已禁用")
            return
        
        from servers.tftp_server import TFTPServer
        tftp = TFTPServer(self.config['tftp'])
        self.services['tftp'] = tftp
        tftp.start()
        logger.info("TFTP服务器已启动")
    
    def start_http_server(self):
        """启动HTTP服务器"""
        if not self.config['http']['enabled']:
            logger.info("HTTP服务已禁用")
            return
        
        from servers.http_server import HTTPServer
        http = HTTPServer(self.config['http'])
        self.services['http'] = http
        http.start()
        logger.info("HTTP服务器已启动")
    
    def start(self):
        """启动所有服务"""
        logger.info("启动小思超级PXE系统...")
        self.create_directories()
        self.running = True
        
        try:
            self.start_dhcp_server()
            self.start_tftp_server()
            self.start_http_server()
            
            logger.info("所有服务已启动，按Ctrl+C停止")
            while self.running:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
            self.stop()
    
    def stop(self):
        """停止所有服务"""
        logger.info("正在停止服务...")
        self.running = False
        
        for name, service in self.services.items():
            try:
                service.stop()
                logger.info(f"{name.upper()}服务已停止")
            except Exception as e:
                logger.error(f"停止{name.upper()}服务时出错: {e}")
        
        logger.info("小思超级PXE系统已停止")

def main():
    pxe = SuperPXE()
    pxe.start()

if __name__ == '__main__':
    main()
