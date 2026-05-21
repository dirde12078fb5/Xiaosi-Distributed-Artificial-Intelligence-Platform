#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP服务器模块
"""

import socket
import threading
import os
import logging
from pathlib import Path
import mimetypes
import urllib.parse

logger = logging.getLogger('SuperPXE.HTTP')

class HTTPRequest:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.method = None
        self.path = None
        self.protocol = None
        self.headers = {}
        self.body = b''
        self.parse()
    
    def parse(self):
        try:
            text = self.raw_data.decode('utf-8', errors='ignore')
            lines = text.split('\r\n')
            
            if len(lines) > 0 and lines[0]:
                parts = lines[0].split(' ')
                if len(parts) >= 3:
                    self.method = parts[0]
                    self.path = urllib.parse.unquote(parts[1])
                    self.protocol = parts[2]
            
            i = 1
            while i < len(lines) and lines[i]:
                line = lines[i]
                if ':' in line:
                    key, value = line.split(':', 1)
                    self.headers[key.strip()] = value.strip()
                i += 1
        except Exception as e:
            logger.error(f"解析HTTP请求时出错: {e}")

class HTTPResponse:
    def __init__(self):
        self.status_code = 200
        self.status_text = 'OK'
        self.headers = {}
        self.body = b''
    
    def set_content_type(self, filename):
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            self.headers['Content-Type'] = mime_type
        else:
            self.headers['Content-Type'] = 'application/octet-stream'
    
    def to_bytes(self):
        response = f'HTTP/1.1 {self.status_code} {self.status_text}\r\n'
        for key, value in self.headers.items():
            response += f'{key}: {value}\r\n'
        response += '\r\n'
        return response.encode('utf-8') + self.body

class HTTPSession:
    def __init__(self, server, client_socket, addr, root_dir):
        self.server = server
        self.client_socket = client_socket
        self.addr = addr
        self.root_dir = Path(root_dir)
    
    def handle_request(self):
        try:
            self.client_socket.settimeout(10.0)
            raw_data = self.client_socket.recv(8192)
            if not raw_data:
                return
            
            request = HTTPRequest(raw_data)
            response = self.process_request(request)
            self.client_socket.sendall(response.to_bytes())
        except socket.timeout:
            logger.warning(f"客户端连接超时: {self.addr}")
        except Exception as e:
            logger.error(f"处理HTTP请求时出错: {e}")
        finally:
            try:
                self.client_socket.close()
            except:
                pass
    
    def process_request(self, request):
        response = HTTPResponse()
        
        if request.method == 'GET':
            self.handle_get(request, response)
        else:
            response.status_code = 405
            response.status_text = 'Method Not Allowed'
            response.headers['Content-Type'] = 'text/plain'
            response.body = b'Method Not Allowed'
        
        return response
    
    def handle_get(self, request, response):
        file_path = self.root_dir / request.path.lstrip('/')
        
        if not file_path.exists():
            response.status_code = 404
            response.status_text = 'Not Found'
            response.headers['Content-Type'] = 'text/plain'
            response.body = b'404 Not Found'
            logger.warning(f"文件不存在: {request.path}")
            return
        
        if file_path.is_dir():
            index_path = file_path / 'index.html'
            if index_path.exists():
                file_path = index_path
            else:
                self.generate_directory_listing(file_path, request.path, response)
                return
        
        try:
            with open(file_path, 'rb') as f:
                response.body = f.read()
            
            response.set_content_type(str(file_path))
            response.headers['Content-Length'] = str(len(response.body))
            logger.info(f"发送文件: {request.path}")
        except Exception as e:
            response.status_code = 500
            response.status_text = 'Internal Server Error'
            response.headers['Content-Type'] = 'text/plain'
            response.body = b'Internal Server Error'
            logger.error(f"读取文件时出错: {e}")
    
    def generate_directory_listing(self, dir_path, request_path, response):
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>目录列表 - {path}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>目录列表: {path}</h1>
    <table>
        <tr>
            <th>名称</th>
            <th>类型</th>
            <th>大小</th>
        </tr>
'''.format(path=request_path)
        
        if request_path != '/':
            parent_path = os.path.dirname(request_path.rstrip('/')) or '/'
            html += f'''
        <tr>
            <td><a href="{parent_path}">..</a></td>
            <td>目录</td>
            <td>-</td>
        </tr>
'''
        
        try:
            items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for item in items:
                item_path = request_path.rstrip('/') + '/' + item.name
                if item.is_dir():
                    size = '-'
                    item_type = '目录'
                    link = item_path + '/'
                else:
                    size = str(item.stat().st_size)
                    item_type = '文件'
                    link = item_path
                
                html += f'''
        <tr>
            <td><a href="{link}">{item.name}</a></td>
            <td>{item_type}</td>
            <td>{size}</td>
        </tr>
'''
        except Exception as e:
            logger.error(f"生成目录列表时出错: {e}")
        
        html += '''
    </table>
</body>
</html>
'''
        
        response.body = html.encode('utf-8')
        response.headers['Content-Type'] = 'text/html; charset=utf-8'

class HTTPServer:
    def __init__(self, config):
        self.config = config
        self.interface = config['interface']
        self.port = config['port']
        self.root_dir = config['root_dir']
        self.running = False
        self.socket = None
        self.thread = None
    
    def _server_loop(self):
        while self.running:
            try:
                self.socket.settimeout(1.0)
                try:
                    client_socket, addr = self.socket.accept()
                    logger.info(f"接受连接: {addr}")
                    
                    session = HTTPSession(self, client_socket, addr, self.root_dir)
                    client_thread = threading.Thread(
                        target=session.handle_request,
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    pass
            except Exception as e:
                if self.running:
                    logger.error(f"HTTP服务器错误: {e}")
    
    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.interface, self.port))
        self.socket.listen(128)
        
        self.running = True
        self.thread = threading.Thread(target=self._server_loop, daemon=True)
        self.thread.start()
        logger.info(f"HTTP服务器监听 {self.interface}:{self.port}, 根目录: {self.root_dir}")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.socket:
            self.socket.close()
        logger.info("HTTP服务器已停止")
