#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级NAS - Python版本
智能存储管理平台

作者: 小思AI团队
版本: 1.0.0
"""

import os
import time
import json
import hashlib
import mimetypes
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
import jwt
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv()

# ==================== 配置 ====================
class Config:
    """应用配置类"""
    # 服务器配置
    PORT = int(os.getenv('PORT', 8080))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # 路径配置
    STORAGE_PATH = os.getenv('STORAGE_PATH', './storage')
    TEMP_PATH = os.getenv('TEMP_PATH', './temp')
    PUBLIC_PATH = os.getenv('PUBLIC_PATH', '../public')
    
    # 安全配置
    JWT_SECRET = os.getenv('JWT_SECRET', 'xiaosi-super-nas-secret-key-2024-python')
    JWT_EXPIRY_HOURS = 24
    
    # 文件配置
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 1024 * 1024 * 1024))
    
    # 默认用户配置
    DEFAULT_USER = os.getenv('DEFAULT_USER', 'admin')
    DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD', 'admin123')
    
    # 支持的文件类型
    SUPPORTED_EXTENSIONS = {
        '.pdf': '📄', '.doc': '📝', '.docx': '📝',
        '.xls': '📊', '.xlsx': '📊', '.ppt': '📽️', '.pptx': '📽️',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.mp4': '🎬', '.avi': '🎬', '.mp3': '🎵', '.wav': '🎵',
        '.zip': '📦', '.rar': '📦', '.7z': '📦',
        '.js': '💻', '.html': '💻', '.css': '💻', '.py': '💻',
    }

config = Config()

# ==================== 数据存储 ====================
users = {}
user_sessions = {}

# ==================== 初始化 ====================
def initialize():
    """初始化应用"""
    for dir_path in [config.STORAGE_PATH, config.TEMP_PATH]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    init_default_users()

def init_default_users():
    """初始化默认用户"""
    # 管理员
    hashed_pw = bcrypt.hashpw(config.DEFAULT_PASSWORD.encode('utf-8'), bcrypt.gensalt())
    users[config.DEFAULT_USER] = {
        'id': 'default-admin-1',
        'username': config.DEFAULT_USER,
        'email': 'admin@xiaosi.com',
        'password_hash': hashed_pw.decode('utf-8'),
        'role': 'admin',
        'storage_quota': 10 * 1024 * 1024 * 1024,
        'created_at': datetime.now().isoformat(),
        'last_login': datetime.now().isoformat()
    }
    
    # 测试用户
    users['zhangsan'] = {
        'id': 'sample-user-1',
        'username': 'zhangsan',
        'email': 'zhangsan@xiaosi.com',
        'password_hash': bcrypt.hashpw(b'password', bcrypt.gensalt()).decode('utf-8'),
        'role': 'user',
        'storage_quota': 1 * 1024 * 1024 * 1024,
        'created_at': datetime.now().isoformat(),
        'last_login': datetime.now().isoformat()
    }

# ==================== 工具函数 ====================
def get_file_icon(filename, is_dir=False):
    """获取文件图标"""
    if is_dir:
        return "📁"
    ext = os.path.splitext(filename)[1].lower()
    return config.SUPPORTED_EXTENSIONS.get(ext, '📄')

def get_local_ips():
    """获取本机IP地址"""
    import socket
    hostname = socket.gethostname()
    ips = ['127.0.0.1']
    try:
        addrs = socket.getaddrinfo(hostname, None)
        for addr in addrs:
            ip = addr[4][0]
            if ip not in ips and not ip.startswith('::'):
                ips.append(ip)
    except:
        pass
    return ips

def format_file_size(size):
    """格式化文件大小"""
    if size == 0:
        return '0 Bytes'
    units = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"

# ==================== 认证中间件 ====================
def token_required(f):
    """Token认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'message': 'Authorization required'}), 401
        
        try:
            token = auth_header.replace('Bearer ', '')
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
            request.current_user = payload
        except:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated

# ==================== 路由 ====================
@app.route('/')
def index():
    """首页"""
    return redirect(url_for('static', filename='index.html'))

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        user = users.get(username)
        if not user:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRY_HOURS)
        }, config.JWT_SECRET, algorithm='HS256')
        
        user['last_login'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'email': user['email']
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats():
    """获取系统统计"""
    data = {
        'storage': {
            'used': 2.5 * 1024 * 1024 * 1024,
            'total': 4 * 1024 * 1024 * 1024,
            'percentage': 62.5
        },
        'files': {
            'count': 1284,
            'recent': [
                {'name': '项目报告.pdf', 'user': 'admin', 'time': '5分钟前'},
                {'name': '新用户注册', 'user': 'system', 'time': '15分钟前'}
            ]
        },
        'users': {
            'total': len(users),
            'online': 2
        }
    }
    return jsonify({'success': True, 'data': data})

@app.route('/api/files', methods=['GET'])
@token_required
def get_files():
    """获取文件列表"""
    path = request.args.get('path', '/')
    target_path = os.path.join(config.STORAGE_PATH, path.lstrip('/'))
    
    files = []
    if os.path.exists(target_path) and os.path.isdir(target_path):
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            stat = os.stat(item_path)
            is_dir = os.path.isdir(item_path)
            files.append({
                'id': str(stat.st_mtime),
                'name': item,
                'type': 'folder' if is_dir else 'file',
                'size': stat.st_size,
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'icon': get_file_icon(item, is_dir),
                'owner': 'admin'
            })
    
    if not files:
        files = [
            {'id': '1', 'name': '项目文档', 'type': 'folder', 'size': 0, 'modified_at': datetime.now().isoformat(), 'icon': '📁', 'owner': 'admin'},
            {'id': '2', 'name': '照片备份', 'type': 'folder', 'size': 0, 'modified_at': datetime.now().isoformat(), 'icon': '📁', 'owner': 'admin'},
            {'id': '3', 'name': '项目报告.pdf', 'type': 'file', 'size': 2621440, 'modified_at': datetime.now().isoformat(), 'icon': '📄', 'owner': 'admin'},
        ]
    
    return jsonify({'success': True, 'data': files})

@app.route('/api/files/upload', methods=['POST'])
@token_required
def upload_files():
    """上传文件"""
    path = request.args.get('path', '/')
    target_path = os.path.join(config.STORAGE_PATH, path.lstrip('/'))
    
    if not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)
    
    uploaded = []
    for filename, file in request.files.items():
        if file.content_length > config.MAX_FILE_SIZE:
            continue
        filepath = os.path.join(target_path, file.filename)
        file.save(filepath)
        uploaded.append({
            'id': str(time.time()),
            'name': file.filename,
            'size': os.path.getsize(filepath),
            'path': path
        })
    
    return jsonify({
        'success': True,
        'message': f'成功上传 {len(uploaded)} 个文件',
        'data': uploaded
    })

@app.route('/api/files/download', methods=['GET'])
@token_required
def download_file():
    """下载文件"""
    path = request.args.get('path')
    target_path = os.path.join(config.STORAGE_PATH, path.lstrip('/'))
    
    if not os.path.exists(target_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    return send_file(target_path, as_attachment=True)

@app.route('/api/files/folder', methods=['POST'])
@token_required
def create_folder():
    """创建文件夹"""
    data = request.json
    name = data.get('name')
    path = data.get('path', '/')
    
    target_path = os.path.join(config.STORAGE_PATH, path.lstrip('/'), name)
    
    if os.path.exists(target_path):
        return jsonify({'success': False, 'message': 'Folder already exists'}), 400
    
    os.makedirs(target_path, exist_ok=True)
    
    return jsonify({
        'success': True,
        'message': 'Folder created successfully',
        'data': {'name': name, 'type': 'folder', 'path': path}
    })

@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    """获取用户列表"""
    user_list = []
    for username, user in users.items():
        last_login = datetime.fromisoformat(user['last_login'])
        status = 'online' if (datetime.now() - last_login).total_seconds() < 3600 else 'offline'
        
        user_list.append({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'storage_quota': user['storage_quota'],
            'status': status,
            'last_login': user['last_login']
        })
    
    return jsonify({'success': True, 'data': user_list})

@app.route('/api/settings', methods=['GET'])
@token_required
def get_settings():
    """获取系统设置"""
    return jsonify({
        'success': True,
        'data': {
            'general': {
                'system_name': '小思超级NAS',
                'timezone': 'Asia/Shanghai',
                'language': 'zh-CN',
                'theme': 'dark'
            },
            'network': {
                'ip': config.HOST,
                'port': config.PORT
            }
        }
    })

def print_startup_info():
    """打印启动信息"""
    print("=" * 60)
    print("  🚀 小思超级NAS (Python版本) 已启动！")
    print("=" * 60)
    print()
    print("📡 访问地址：")
    print(f"   本地访问：http://localhost:{config.PORT}")
    
    local_ips = get_local_ips()
    for ip in local_ips:
        if ip != '127.0.0.1':
            print(f"   局域网访问：http://{ip}:{config.PORT}")
    
    print()
    print("👤 默认登录：")
    print(f"   用户名：{config.DEFAULT_USER}")
    print(f"   密码：{config.DEFAULT_PASSWORD}")
    print()
    print("=" * 60)
    print()

if __name__ == '__main__':
    initialize()
    print_startup_info()
    app.run(host=config.HOST, port=config.PORT, debug=False)
