"""
小思超级多版本NAS服务 - Python实现
无需Go语言环境，直接运行
支持IP地址检测、文件夹推送
"""
import os
import json
import hashlib
import socket
import uuid
import time
import shutil
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ==========================================
# 多语言翻译
# ==========================================
TRANSLATIONS = {
    "zh_CN": {
        "app_name": "小思超级NAS", "dashboard": "控制台", "storage": "存储管理",
        "users": "用户管理", "shares": "共享管理", "push": "推送管理",
        "settings": "设置", "volumes": "存储卷", "create": "创建", "delete": "删除",
        "edit": "编辑", "save": "保存", "cancel": "取消", "name": "名称", "path": "路径",
        "quota": "配额", "used": "已用", "available": "可用", "username": "用户名",
        "password": "密码", "admin": "管理员", "storage_quota": "存储配额",
        "home_directory": "主目录", "smb_status": "SMB状态", "smb_shares": "SMB共享",
        "share_name": "共享名称", "comment": "备注", "read_only": "只读",
        "browseable": "可浏览", "guest_access": "访客访问", "language": "语言",
        "running": "运行中", "stopped": "已停止", "operation_success": "操作成功",
        "operation_failed": "操作失败", "confirm_delete": "确认删除", "no_data": "暂无数据",
        "create_volume": "创建存储卷", "create_user": "创建用户", "create_share": "创建共享",
        "operation": "操作", "yes": "是", "no": "否", "system_info": "系统信息",
        "service_status": "服务状态", "ip_address": "IP地址", "push_targets": "推送目标",
        "push_files": "推送文件", "local_folder": "本地文件夹", "target_device": "目标设备",
        "add_target": "添加目标", "target_name": "目标名称", "target_ip": "目标IP",
        "target_port": "目标端口", "push_folder": "推送文件夹", "select_folder": "选择文件夹",
        "push_now": "立即推送", "pushing": "推送中", "push_history": "推送历史",
        "scan_ip": "扫描IP", "local_ips": "本机IP", "scan": "扫描",
        "found_devices": "发现设备", "online": "在线", "offline": "离线",
        "send": "发送", "receive": "接收", "push_status": "推送状态",
        "success": "成功", "failed": "失败", "progress": "进度",
        "file_count": "文件数", "total_size": "总大小"
    },
    "en_US": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Storage",
        "users": "Users", "shares": "Shares", "push": "Push Manager",
        "settings": "Settings", "volumes": "Volumes", "create": "Create", "delete": "Delete",
        "edit": "Edit", "save": "Save", "cancel": "Cancel", "name": "Name", "path": "Path",
        "quota": "Quota", "used": "Used", "available": "Available", "username": "Username",
        "password": "Password", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Shares",
        "share_name": "Share Name", "comment": "Comment", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Language",
        "running": "Running", "stopped": "Stopped", "operation_success": "Operation Success",
        "operation_failed": "Operation Failed", "confirm_delete": "Confirm Delete", "no_data": "No Data",
        "create_volume": "Create Volume", "create_user": "Create User", "create_share": "Create Share",
        "operation": "Operation", "yes": "Yes", "no": "No", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP Address", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Local Folder", "target_device": "Target Device",
        "add_target": "Add Target", "target_name": "Target Name", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Select Folder",
        "push_now": "Push Now", "pushing": "Pushing", "push_history": "Push History",
        "scan_ip": "Scan IP", "local_ips": "Local IPs", "scan": "Scan",
        "found_devices": "Found Devices", "online": "Online", "offline": "Offline",
        "send": "Send", "receive": "Receive", "push_status": "Push Status",
        "success": "Success", "failed": "Failed", "progress": "Progress",
        "file_count": "File Count", "total_size": "Total Size"
    },
    "ja_JP": {
        "app_name": "小思スーパーNAS", "dashboard": "ダッシュボード", "storage": "ストレージ",
        "users": "ユーザー", "shares": "共有", "push": "プッシュ管理",
        "settings": "設定", "volumes": "ボリューム", "create": "作成", "delete": "削除",
        "edit": "編集", "save": "保存", "cancel": "キャンセル", "name": "名前", "path": "パス",
        "quota": "クォータ", "used": "使用中", "available": "利用可能", "username": "ユーザー名",
        "password": "パスワード", "admin": "管理者", "storage_quota": "ストレージクォータ",
        "home_directory": "ホームディレクトリ", "smb_status": "SMB状態", "smb_shares": "SMB共有",
        "share_name": "共有名", "comment": "コメント", "read_only": "読み取り専用",
        "browseable": "参照可能", "guest_access": "ゲストアクセス", "language": "言語",
        "running": "実行中", "stopped": "停止中", "operation_success": "操作成功",
        "operation_failed": "操作失敗", "confirm_delete": "削除の確認", "no_data": "データなし",
        "create_volume": "ボリューム作成", "create_user": "ユーザー作成", "create_share": "共有作成",
        "operation": "操作", "yes": "はい", "no": "いいえ", "system_info": "システム情報",
        "service_status": "サービス状態", "ip_address": "IPアドレス", "push_targets": "プッシュ先",
        "push_files": "ファイル送信", "local_folder": "ローカルフォルダ", "target_device": "対象デバイス",
        "add_target": "対象を追加", "target_name": "対象名", "target_ip": "対象IP",
        "target_port": "対象ポート", "push_folder": "フォルダ送信", "select_folder": "フォルダ選択",
        "push_now": "今すぐ送信", "pushing": "送信中", "push_history": "送信履歴",
        "scan_ip": "IPスキャン", "local_ips": "ローカルIP", "scan": "スキャン",
        "found_devices": "発見デバイス", "online": "オンライン", "offline": "オフライン",
        "send": "送信", "receive": "受信", "push_status": "送信状態",
        "success": "成功", "failed": "失敗", "progress": "進捗",
        "file_count": "ファイル数", "total_size": "合計サイズ"
    }
}

LANG_NAMES = {
    "zh_CN": "简体中文", "zh_TW": "繁體中文", "en_US": "English (US)", "en_GB": "English (UK)",
    "ja_JP": "日本語", "ko_KR": "한국어", "fr_FR": "Français", "de_DE": "Deutsch",
    "es_ES": "Español", "it_IT": "Italiano", "pt_BR": "Português (BR)", "ru_RU": "Русский",
    "ar_SA": "العربية", "hi_IN": "हिन्दी", "tr_TR": "Türkçe", "th_TH": "ไทย",
    "vi_VN": "Tiếng Việt", "id_ID": "Bahasa Indonesia", "nl_NL": "Nederlands", "pl_PL": "Polski",
    "sv_SE": "Svenska", "da_DK": "Dansk", "fi_FI": "Suomi", "he_IL": "עברית",
    "hu_HU": "Magyar", "cs_CZ": "Čeština", "uk_UA": "Українська", "ro_RO": "Română"
}


# ==========================================
# 配置管理
# ==========================================
class Config:
    def __init__(self):
        self.volumes = []
        self.users = []
        self.shares = []
        self.push_targets = []
        self.server_port = 8080
        self.language = "zh_CN"
        self.data_dir = "nas_data"
        self.receive_dir = "nas_data/received"
        self.load()

    def load(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.server_port = data.get("server", {}).get("port", 8080)
                self.language = data.get("server", {}).get("language", "zh_CN")
                for v in data.get("storage", {}).get("volumes", []):
                    self.volumes.append(v)
                for u in data.get("users", []):
                    self.users.append(u)
                for s in data.get("smb", {}).get("shares", []):
                    self.shares.append(s)
                for t in data.get("push", {}).get("targets", []):
                    self.push_targets.append(t)
                self.data_dir = data.get("data_dir", "nas_data")
                self.receive_dir = data.get("receive_dir", "nas_data/received")
        except:
            pass
        os.makedirs(self.receive_dir, exist_ok=True)

    def save(self):
        data = {
            "server": {"port": self.server_port, "language": self.language},
            "storage": {"volumes": self.volumes},
            "users": self.users,
            "smb": {"shares": self.shares},
            "push": {"targets": self.push_targets},
            "data_dir": self.data_dir,
            "receive_dir": self.receive_dir
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ==========================================
# IP地址管理
# ==========================================
class IPManager:
    # 设备唯一标识（基于机器名+随机ID）
    DEVICE_ID = None

    @classmethod
    def get_device_id(cls):
        if cls.DEVICE_ID is None:
            hostname = socket.gethostname()
            # 结合机器名和随机后缀确保同一WiFi下多台设备有不同ID
            cls.DEVICE_ID = f"{hostname}-{uuid.uuid4().hex[:6]}"
        return cls.DEVICE_ID

    @staticmethod
    def get_adapter_name_windows(line_before):
        """从ipconfig输出中提取网卡名称（Windows）"""
        # 向上查找网卡名称
        name = "Network Adapter"
        for line in line_before:
            if "adapter" in line.lower() or "适配器" in line:
                # 提取适配器名称（通常在冒号前）
                parts = line.split(":")
                if len(parts) >= 1:
                    name = parts[0].strip()
                    # 清理常见前缀
                    for prefix in ["适配器", "adapter", "Adapter", "连接"]:
                        if name.startswith(prefix):
                            name = name[len(prefix):].strip()
                    if name.startswith("."):
                        name = name[1:].strip()
                break
        return name

    @staticmethod
    def get_network_type(ip):
        """根据IP段判断网络类型"""
        if ip.startswith("192.168."):
            return "LAN (私有)"
        elif ip.startswith("10."):
            return "LAN (私有)"
        elif ip.startswith("172."):
            second = int(ip.split(".")[1])
            if 16 <= second <= 31:
                return "LAN (私有)"
        elif ip.startswith("127."):
            return "Loopback"
        elif ip.startswith("255."):
            return "Broadcast"
        else:
            return "Public/WAN"
        return "LAN"

    @classmethod
    def get_local_ips(cls):
        ips = []
        hostname = socket.gethostname()

        try:
            # 方法1: 通过UDP连接获取出口IP（最可靠的外网出口IP）
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            wan_ip = s.getsockname()[0]
            s.close()
            if wan_ip and wan_ip != "127.0.0.1":
                ips.append({
                    "ip": wan_ip,
                    "type": "wan",
                    "name": f"{hostname} (出口)",
                    "adapter": "默认路由",
                    "network": cls.get_network_type(wan_ip)
                })
        except:
            pass

        try:
            import platform
            system = platform.system()

            if system == "Windows":
                try:
                    import subprocess
                    result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, timeout=10)
                    lines = result.stdout.split("\n")

                    # 同时收集IPv4和网卡名称
                    current_adapter = "Unknown"
                    adapter_lines = []

                    for line in lines:
                        # 检测网卡名称行
                        stripped = line.strip()
                        if "适配器" in stripped or "adapter" in stripped.lower():
                            # 保存上一个适配器的信息
                            if adapter_lines:
                                # 在adapter_lines中查找IPv4
                                for al in adapter_lines:
                                    if "IPv4" in al or "IPv4 地址" in al:
                                        parts = al.split(":")
                                        if len(parts) >= 2:
                                            ip = parts[1].strip()
                                            if ip and "." in ip and not ip.startswith("127."):
                                                # 检查是否已存在
                                                if not any(i["ip"] == ip for i in ips):
                                                    ips.append({
                                                        "ip": ip,
                                                        "type": "lan",
                                                        "name": current_adapter,
                                                        "adapter": current_adapter,
                                                        "network": cls.get_network_type(ip)
                                                    })
                                        break
                            # 开始新的适配器
                            current_adapter = IPManager.get_adapter_name_windows([stripped])
                            adapter_lines = []
                        elif adapter_lines is not None:
                            adapter_lines.append(stripped)

                    # 处理最后一个适配器
                    if adapter_lines:
                        for al in adapter_lines:
                            if "IPv4" in al or "IPv4 地址" in al:
                                parts = al.split(":")
                                if len(parts) >= 2:
                                    ip = parts[1].strip()
                                    if ip and "." in ip and not ip.startswith("127."):
                                        if not any(i["ip"] == ip for i in ips):
                                            ips.append({
                                                "ip": ip,
                                                "type": "lan",
                                                "name": current_adapter,
                                                "adapter": current_adapter,
                                                "network": cls.get_network_type(ip)
                                            })
                                break

                except Exception as e:
                    print(f"ipconfig error: {e}")

            elif system in ("Linux", "Darwin"):
                try:
                    import subprocess
                    result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5)
                    import re

                    # 按接口分割
                    interfaces = re.split(r'(^[a-zA-Z0-9]+:\s)', result.stdout, flags=re.MULTILINE)
                    current_iface = ""
                    iface_lines = []

                    for block in interfaces:
                        if re.match(r'^[a-zA-Z0-9]+:\s', block):
                            current_iface = re.match(r'^([a-zA-Z0-9]+):', block).group(1)
                            iface_lines = block.split('\n')
                        elif iface_lines:
                            for line in iface_lines:
                                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                                if match:
                                    ip = match.group(1)
                                    if ip and not ip.startswith("127."):
                                        if not any(i["ip"] == ip for i in ips):
                                            ips.append({
                                                "ip": ip,
                                                "type": "lan",
                                                "name": f"{current_iface}",
                                                "adapter": current_iface,
                                                "network": cls.get_network_type(ip)
                                            })
                                iface_lines = []

                except Exception as e:
                    print(f"ifconfig error: {e}")

        except Exception as e:
            print(f"Network detection error: {e}")

        # 去重并标记
        seen = set()
        unique_ips = []
        for ip in ips:
            if ip["ip"] not in seen:
                seen.add(ip["ip"])
                unique_ips.append(ip)

        if not unique_ips:
            unique_ips.append({
                "ip": "127.0.0.1",
                "type": "loopback",
                "name": "localhost",
                "adapter": "loopback",
                "network": "Loopback"
            })

        # 添加设备ID信息
        device_id = cls.get_device_id()
        for ip in unique_ips:
            ip["device_id"] = device_id

        return unique_ips

    @classmethod
    def scan_lan(cls, port=8080, timeout=0.5):
        found = []
        local_ips = cls.get_local_ips()
        if not local_ips:
            return found

        # 收集所有私有IP段
        prefixes = set()
        for ip_info in local_ips:
            ip = ip_info["ip"]
            if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                parts = ip.split(".")
                if len(parts) == 4:
                    prefixes.add(".".join(parts[:3]))

        if not prefixes:
            return found

        def check_ip(ip_str, prefix, port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip_str, port))
                sock.close()
                if result == 0:
                    # 获取设备ID
                    device_id = None
                    try:
                        import urllib.request
                        resp = urllib.request.urlopen(f"http://{ip_str}:{port}/api/ip/local", timeout=2)
                        data = json.loads(resp.read().decode())
                        if data.get("ips"):
                            device_id = data["ips"][0].get("device_id", device_id)
                    except:
                        pass

                    found.append({
                        "ip": ip_str,
                        "port": port,
                        "network": prefix,
                        "status": "online",
                        "device_id": device_id,
                        "is_self": ip_str in [i["ip"] for i in local_ips]
                    })
            except:
                pass

        threads = []
        for prefix in prefixes:
            for i in range(1, 255):
                ip_str = f"{prefix}.{i}"
                # 排除本机IP
                if not any(ip_str == ip_info["ip"] for ip_info in local_ips):
                    t = threading.Thread(target=check_ip, args=(ip_str, prefix, port))
                    threads.append(t)
                    t.start()

        for t in threads:
            t.join()

        return found


# ==========================================
# 推送管理器
# ==========================================
class PushManager:
    def __init__(self, config):
        self.targets = config.push_targets
        self.config = config
        self.push_history = []
        self.active_push = None

    def list_targets(self):
        return self.targets

    def add_target(self, name, ip, port=8080):
        for t in self.targets:
            if t["ip"] == ip and t["port"] == port:
                return False, "Target exists"
        self.targets.append({
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "ip": ip,
            "port": port,
            "status": "unknown"
        })
        self.config.push_targets = self.targets
        self.config.save()
        return True, "Added"

    def delete_target(self, target_id):
        self.targets = [t for t in self.targets if t.get("id") != target_id]
        self.config.push_targets = self.targets
        self.config.save()
        return True, "Deleted"

    def check_target(self, target_id):
        target = next((t for t in self.targets if t.get("id") == target_id), None)
        if not target:
            return False, "Target not found"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((target["ip"], target["port"]))
            sock.close()
            target["status"] = "online" if result == 0 else "offline"
            return True, target["status"]
        except Exception as e:
            target["status"] = "offline"
            return False, str(e)

    def push_folder(self, target_id, folder_path, progress_callback=None):
        target = next((t for t in self.targets if t.get("id") == target_id), None)
        if not target:
            return False, "Target not found"

        if not os.path.exists(folder_path):
            return False, "Folder not found"

        folder_path = os.path.abspath(folder_path)
        folder_name = os.path.basename(folder_path)

        all_files = []
        total_size = 0
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    size = os.path.getsize(fpath)
                    rel_path = os.path.relpath(fpath, folder_path)
                    all_files.append((rel_path, fpath, size))
                    total_size += size
                except:
                    pass

        push_id = str(uuid.uuid4())[:8]
        self.active_push = {
            "id": push_id,
            "target": target["name"],
            "folder": folder_name,
            "total_files": len(all_files),
            "total_size": total_size,
            "sent_files": 0,
            "sent_size": 0,
            "status": "pushing"
        }

        try:
            import urllib.request
            boundary = "----XiaosiNASPush" + str(uuid.uuid4().hex)

            for idx, (rel_path, fpath, size) in enumerate(all_files):
                try:
                    with open(fpath, "rb") as f:
                        file_data = f.read()

                    body = b""
                    body += f"--{boundary}\r\n".encode()
                    body += f'Content-Disposition: form-data; name="folder"\r\n\r\n'.encode()
                    body += f"{folder_name}\r\n".encode()
                    body += f"--{boundary}\r\n".encode()
                    body += f'Content-Disposition: form-data; name="filepath"\r\n\r\n'.encode()
                    body += f"{rel_path}\r\n".encode()
                    body += f"--{boundary}\r\n".encode()
                    body += f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(fpath)}"\r\n'.encode()
                    body += b"Content-Type: application/octet-stream\r\n\r\n"
                    body += file_data
                    body += b"\r\n"
                    body += f"--{boundary}--\r\n".encode()

                    url = f"http://{target['ip']}:{target['port']}/api/push/receive"
                    req = urllib.request.Request(url, data=body)
                    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
                    req.add_header("Content-Length", str(len(body)))

                    resp = urllib.request.urlopen(req, timeout=30)
                    resp.read()

                    self.active_push["sent_files"] = idx + 1
                    self.active_push["sent_size"] += size

                    if progress_callback:
                        progress_callback(idx + 1, len(all_files), rel_path)

                except Exception as e:
                    print(f"Failed to push {rel_path}: {e}")

            self.active_push["status"] = "success"
            self.push_history.append({
                **self.active_push,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            self.active_push = None
            return True, f"Push complete: {len(all_files)} files"

        except Exception as e:
            if self.active_push:
                self.active_push["status"] = "failed"
                self.active_push["error"] = str(e)
                self.push_history.append({
                    **self.active_push,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                self.active_push = None
            return False, str(e)

    def receive_file(self, folder_name, filepath, file_data):
        target_dir = os.path.join(self.config.receive_dir, folder_name)
        full_path = os.path.join(target_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(file_data)

        return True, os.path.getsize(full_path)

    def get_push_status(self):
        return {
            "active": self.active_push,
            "history": self.push_history[-20:] if len(self.push_history) > 20 else self.push_history
        }


# ==========================================
# 存储管理器
# ==========================================
class StorageManager:
    def __init__(self, config):
        self.volumes = config.volumes

    def list_volumes(self):
        return self.volumes

    def create_volume(self, name, path, quota_gb):
        for v in self.volumes:
            if v["name"] == name:
                return False, "Volume exists"
        self.volumes.append({"name": name, "path": path, "quota_gb": quota_gb})
        return True, "Created"

    def delete_volume(self, name):
        self.volumes = [v for v in self.volumes if v["name"] != name]
        return True, "Deleted"


# ==========================================
# 用户管理器
# ==========================================
class UserManager:
    def __init__(self, config):
        self.users = config.users
        if not any(u.get("username") == "admin" for u in self.users):
            self.users.append({
                "username": "admin",
                "password": self._hash_password("admin"),
                "is_admin": True,
                "home_dir": "/mnt/data/admin",
                "storage_quota_gb": 0
            })

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def list_users(self):
        return [{"username": u["username"], "is_admin": u.get("is_admin", False),
                 "home_dir": u.get("home_dir", ""), "storage_quota_gb": u.get("storage_quota_gb", 100)}
                for u in self.users]

    def create_user(self, username, password, is_admin=False):
        for u in self.users:
            if u["username"] == username:
                return False, "User exists"
        self.users.append({
            "username": username,
            "password": self._hash_password(password),
            "is_admin": is_admin,
            "home_dir": f"/mnt/data/{username}",
            "storage_quota_gb": 100
        })
        return True, "Created"

    def delete_user(self, username):
        if username == "admin":
            return False, "Cannot delete admin"
        self.users = [u for u in self.users if u["username"] != username]
        return True, "Deleted"


# ==========================================
# SMB管理器
# ==========================================
class SMBManager:
    def __init__(self, config):
        self.shares = config.shares
        self.running = True

    def list_shares(self):
        return self.shares

    def create_share(self, name, path):
        for s in self.shares:
            if s["name"] == name:
                return False, "Share exists"
        self.shares.append({
            "name": name, "path": path, "comment": "", "read_only": False,
            "browseable": True, "guest_access": False
        })
        return True, "Created"

    def delete_share(self, name):
        self.shares = [s for s in self.shares if s["name"] != name]
        return True, "Deleted"


# ==========================================
# 全局管理器
# ==========================================
config = Config()
storage_mgr = StorageManager(config)
user_mgr = UserManager(config)
smb_mgr = SMBManager(config)
ip_mgr = IPManager()
push_mgr = PushManager(config)


# ==========================================
# HTTP请求处理器
# ==========================================
class NASHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/i18n/":
            lang = query.get("lang", ["zh_CN"])[0]
            trans = TRANSLATIONS.get(lang, TRANSLATIONS.get("zh_CN", {}))
            self.send_json(trans)

        elif path == "/api/storage/volumes":
            self.send_json({"volumes": storage_mgr.list_volumes()})

        elif path == "/api/users":
            self.send_json({"users": user_mgr.list_users()})

        elif path == "/api/smb/shares":
            self.send_json({"shares": smb_mgr.list_shares()})

        elif path == "/api/smb/status":
            self.send_json({"running": smb_mgr.running, "port": 445, "workgroup": "WORKGROUP"})

        elif path == "/api/ip/local":
            self.send_json({"ips": ip_mgr.get_local_ips()})

        elif path == "/api/ip/scan":
            port = int(query.get("port", ["8080"])[0])
            found = ip_mgr.scan_lan(port=port)
            self.send_json({"devices": found})

        elif path == "/api/push/targets":
            self.send_json({"targets": push_mgr.list_targets()})

        elif path == "/api/push/status":
            self.send_json(push_mgr.get_push_status())

        elif path == "/" or path == "/index.html":
            self.send_html(INDEX_HTML)

        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_type = self.headers.get("Content-Type", "")

        if "multipart/form-data" in content_type:
            if path == "/api/push/receive":
                self._handle_receive()
                return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}

        if path == "/api/storage/volumes":
            name = data.get("name", "")
            path_v = data.get("path", "")
            quota = data.get("quota_gb", 100)
            ok, msg = storage_mgr.create_volume(name, path_v, quota)
            self.send_json({"message": msg}, 201 if ok else 400)

        elif path == "/api/storage/volumes/delete":
            name = data.get("name", "")
            ok, msg = storage_mgr.delete_volume(name)
            self.send_json({"message": msg})

        elif path == "/api/users":
            username = data.get("username", "")
            password = data.get("password", "")
            is_admin = data.get("is_admin", False)
            ok, msg = user_mgr.create_user(username, password, is_admin)
            self.send_json({"message": msg}, 201 if ok else 400)

        elif path == "/api/users/delete":
            username = data.get("username", "")
            ok, msg = user_mgr.delete_user(username)
            self.send_json({"message": msg})

        elif path == "/api/smb/shares":
            name = data.get("name", "")
            share_path = data.get("path", "")
            ok, msg = smb_mgr.create_share(name, share_path)
            self.send_json({"message": msg}, 201 if ok else 400)

        elif path == "/api/smb/shares/delete":
            name = data.get("name", "")
            ok, msg = smb_mgr.delete_share(name)
            self.send_json({"message": msg})

        elif path == "/api/push/targets":
            name = data.get("name", "")
            ip = data.get("ip", "")
            port = data.get("port", 8080)
            ok, msg = push_mgr.add_target(name, ip, port)
            self.send_json({"message": msg}, 201 if ok else 400)

        elif path == "/api/push/targets/delete":
            target_id = data.get("id", "")
            ok, msg = push_mgr.delete_target(target_id)
            self.send_json({"message": msg})

        elif path == "/api/push/targets/check":
            target_id = data.get("id", "")
            ok, msg = push_mgr.check_target(target_id)
            self.send_json({"status": msg, "success": ok})

        elif path == "/api/push/folder":
            target_id = data.get("target_id", "")
            folder_path = data.get("folder_path", "")
            t = threading.Thread(target=push_mgr.push_folder, args=(target_id, folder_path))
            t.daemon = True
            t.start()
            self.send_json({"message": "Push started"})

        else:
            self.send_error(404)

    def _handle_receive(self):
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            boundary = content_type.split("boundary=")[1].strip()
            parts = body.split(f"--{boundary}".encode())

            folder_name = "upload"
            filepath = "file"
            file_data = b""

            for part in parts:
                if not part.strip():
                    continue
                if b"name=\"folder\"" in part:
                    lines = part.split(b"\r\n")
                    if len(lines) >= 4:
                        folder_name = lines[3].decode().strip()
                elif b"name=\"filepath\"" in part:
                    lines = part.split(b"\r\n")
                    if len(lines) >= 4:
                        filepath = lines[3].decode().strip()
                elif b"name=\"file\"" in part:
                    idx = part.find(b"\r\n\r\n")
                    if idx >= 0:
                        file_data = part[idx+4:].rstrip(b"\r\n")

            if file_data:
                ok, size = push_mgr.receive_file(folder_name, filepath, file_data)
                self.send_json({"success": ok, "size": size})
            else:
                self.send_json({"success": True, "message": "No file data"})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[NAS] {args[0]}")


# ==========================================
# Web前端界面
# ==========================================
INDEX_HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小思超级NAS - 管理控制台</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 24px; }}
        .lang-select {{ padding: 8px 12px; border-radius: 6px; border: none; cursor: pointer; }}
        .container {{ display: flex; min-height: calc(100vh - 80px); }}
        .sidebar {{ width: 220px; background: white; padding: 20px 0; box-shadow: 2px 0 8px rgba(0,0,0,0.05); }}
        .nav-item {{ padding: 15px 25px; cursor: pointer; transition: all 0.3s; border-left: 4px solid transparent; }}
        .nav-item:hover, .nav-item.active {{ background: #f8f9ff; border-left-color: #667eea; color: #667eea; }}
        .main {{ flex: 1; padding: 30px; }}
        .card {{ background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }}
        .card-title {{ font-size: 18px; font-weight: 600; margin-bottom: 20px; color: #333; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; }}
        .stat-card h3 {{ font-size: 14px; opacity: 0.9; margin-bottom: 8px; }}
        .stat-card .value {{ font-size: 28px; font-weight: 600; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9ff; font-weight: 600; color: #555; }}
        tr:hover {{ background: #fafafa; }}
        .btn {{ padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: all 0.3s; }}
        .btn-primary {{ background: #667eea; color: white; }}
        .btn-primary:hover {{ background: #5568d3; }}
        .btn-danger {{ background: #f56565; color: white; }}
        .btn-danger:hover {{ background: #e53e3e; }}
        .btn-success {{ background: #48bb78; color: white; }}
        .btn-success:hover {{ background: #38a169; }}
        .btn-sm {{ padding: 6px 12px; font-size: 12px; }}
        .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000; }}
        .modal.show {{ display: flex; }}
        .modal-content {{ background: white; padding: 30px; border-radius: 12px; min-width: 400px; max-width: 600px; max-height: 80vh; overflow-y: auto; }}
        .modal-title {{ font-size: 20px; margin-bottom: 20px; }}
        .form-group {{ margin-bottom: 15px; }}
        .form-group label {{ display: block; margin-bottom: 6px; color: #666; font-size: 14px; }}
        .form-group input, .form-group select {{ width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }}
        .form-row {{ display: flex; gap: 12px; }}
        .form-row .form-group {{ flex: 1; }}
        .form-actions {{ display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }}
        .badge {{ padding: 4px 10px; border-radius: 20px; font-size: 12px; }}
        .badge-success {{ background: #c6f6d5; color: #276749; }}
        .badge-warning {{ background: #fefcbf; color: #975a16; }}
        .badge-danger {{ background: #fed7d7; color: #c53030; }}
        .page {{ display: none; }}
        .page.active {{ display: block; }}
        .ip-list {{ display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }}
        .ip-item {{ background: #f8faff; padding: 12px 16px; border-radius: 8px; border: 1px solid #e2e8f0; border-left: 4px solid #667eea; }}
        .ip-item .ip {{ font-family: 'Consolas', 'Monaco', monospace; font-weight: 600; color: #2d3748; font-size: 15px; }}
        .ip-item .type {{ font-size: 12px; color: #718096; }}
        .progress-bar {{ width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }}
        .progress-bar .fill {{ height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s; }}
        .file-input {{ display: none; }}
        .folder-path {{ font-family: monospace; background: #f7fafc; padding: 10px; border-radius: 6px; margin-bottom: 10px; word-break: break-all; }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 768px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1 id="app-title">小思超级NAS 管理控制台</h1>
        <div class="header-right">
            <select class="lang-select" id="langSelect"></select>
        </div>
    </div>
    <div class="container">
        <div class="sidebar">
            <div class="nav-item active" data-page="dashboard" data-i18n="dashboard">控制台</div>
            <div class="nav-item" data-page="storage" data-i18n="storage">存储管理</div>
            <div class="nav-item" data-page="users" data-i18n="users">用户管理</div>
            <div class="nav-item" data-page="shares" data-i18n="shares">共享管理</div>
            <div class="nav-item" data-page="push" data-i18n="push">推送管理</div>
        </div>
        <div class="main">

            <!-- 控制台 -->
            <div class="page active" id="page-dashboard">
                <div class="stats-grid">
                    <div class="stat-card"><h3 data-i18n="volumes">存储卷</h3><div class="value" id="stat-volumes">0</div></div>
                    <div class="stat-card"><h3 data-i18n="users">用户</h3><div class="value" id="stat-users">0</div></div>
                    <div class="stat-card"><h3 data-i18n="smb_shares">SMB共享</h3><div class="value" id="stat-shares">0</div></div>
                    <div class="stat-card"><h3 data-i18n="service_status">服务状态</h3><div class="value" id="stat-status">-</div></div>
                </div>
                <div class="card">
                    <div class="card-title" data-i18n="local_ips">本机IP地址</div>
                    <div class="ip-list" id="local-ips"></div>
                    <button class="btn btn-primary btn-sm" onclick="loadLocalIPs()" data-i18n="scan_ip">扫描IP</button>
                </div>
            </div>

            <!-- 存储管理 -->
            <div class="page" id="page-storage">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="volumes">存储卷</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('storage')" data-i18n="create">创建</button>
                    </div>
                    <table><thead><tr><th data-i18n="name">名称</th><th data-i18n="path">路径</th><th data-i18n="quota">配额(GB)</th><th data-i18n="operation">操作</th></tr></thead><tbody id="volumes-table"></tbody></table>
                </div>
            </div>

            <!-- 用户管理 -->
            <div class="page" id="page-users">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="users">用户</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('user')" data-i18n="create">创建</button>
                    </div>
                    <table><thead><tr><th data-i18n="username">用户名</th><th data-i18n="home_directory">主目录</th><th data-i18n="storage_quota">配额(GB)</th><th data-i18n="admin">管理员</th><th data-i18n="operation">操作</th></tr></thead><tbody id="users-table"></tbody></table>
                </div>
            </div>

            <!-- 共享管理 -->
            <div class="page" id="page-shares">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="shares">共享</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('share')" data-i18n="create">创建</button>
                    </div>
                    <table><thead><tr><th data-i18n="share_name">共享名称</th><th data-i18n="path">路径</th><th data-i18n="operation">操作</th></tr></thead><tbody id="shares-table"></tbody></table>
                </div>
            </div>

            <!-- 推送管理 -->
            <div class="page" id="page-push">
                <div class="two-col">
                    <div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                            <div class="card-title" style="margin-bottom:0;" data-i18n="push_targets">推送目标</div>
                            <button class="btn btn-primary btn-sm" onclick="showModal('target')" data-i18n="add_target">添加目标</button>
                        </div>
                        <table><thead><tr><th data-i18n="name">名称</th><th data-i18n="ip_address">IP</th><th data-i18n="operation">操作</th></tr></thead><tbody id="targets-table"></tbody></table>
                    </div>
                    <div class="card">
                        <div class="card-title" data-i18n="found_devices">发现设备</div>
                        <div id="scan-result" style="margin-bottom:15px;">
                            <span style="color:#999;">点击扫描按钮发现局域网内的设备</span>
                        </div>
                        <button class="btn btn-success btn-sm" onclick="scanLAN()" data-i18n="scan">扫描局域网</button>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title" data-i18n="push_folder">推送文件夹</div>
                    <div class="form-group">
                        <label data-i18n="target_device">目标设备</label>
                        <select id="push-target-select"><option value="">请选择目标设备</option></select>
                    </div>
                    <div class="form-group">
                        <label data-i18n="local_folder">本地文件夹路径</label>
                        <input type="text" id="push-folder-path" placeholder="例如: C:\\Users\\Documents">
                    </div>
                    <div class="form-group">
                        <label data-i18n="progress">进度</label>
                        <div class="progress-bar"><div class="fill" id="push-progress" style="width:0%"></div></div>
                        <div id="push-status-text" style="margin-top:8px;font-size:13px;color:#666;">等待推送</div>
                    </div>
                    <button class="btn btn-primary" onclick="startPush()" id="push-btn" data-i18n="push_now">立即推送</button>
                </div>

                <div class="card">
                    <div class="card-title" data-i18n="push_history">推送历史</div>
                    <table><thead><tr><th>时间</th><th>目标</th><th>文件夹</th><th>文件数</th><th>状态</th></tr></thead><tbody id="push-history"></tbody></table>
                </div>
            </div>
        </div>
    </div>

    <!-- 创建存储卷 -->
    <div class="modal" id="modal-storage"><div class="modal-content"><div class="modal-title" data-i18n="create_volume">创建存储卷</div>
        <div class="form-group"><label data-i18n="name">名称</label><input type="text" id="storage-name"></div>
        <div class="form-group"><label data-i18n="path">路径</label><input type="text" id="storage-path"></div>
        <div class="form-group"><label data-i18n="quota">配额(GB)</label><input type="number" id="storage-quota" value="100"></div>
        <div class="form-actions"><button class="btn" onclick="closeModal('storage')" data-i18n="cancel">取消</button><button class="btn btn-primary" onclick="createVolume()" data-i18n="save">保存</button></div></div></div>

    <!-- 创建用户 -->
    <div class="modal" id="modal-user"><div class="modal-content"><div class="modal-title" data-i18n="create_user">创建用户</div>
        <div class="form-group"><label data-i18n="username">用户名</label><input type="text" id="user-name"></div>
        <div class="form-group"><label data-i18n="password">密码</label><input type="password" id="user-password"></div>
        <div class="form-actions"><button class="btn" onclick="closeModal('user')" data-i18n="cancel">取消</button><button class="btn btn-primary" onclick="createUser()" data-i18n="save">保存</button></div></div></div>

    <!-- 创建共享 -->
    <div class="modal" id="modal-share"><div class="modal-content"><div class="modal-title" data-i18n="create_share">创建共享</div>
        <div class="form-group"><label data-i18n="share_name">共享名称</label><input type="text" id="share-name"></div>
        <div class="form-group"><label data-i18n="path">路径</label><input type="text" id="share-path"></div>
        <div class="form-actions"><button class="btn" onclick="closeModal('share')" data-i18n="cancel">取消</button><button class="btn btn-primary" onclick="createShare()" data-i18n="save">保存</button></div></div></div>

    <!-- 添加推送目标 -->
    <div class="modal" id="modal-target"><div class="modal-content"><div class="modal-title" data-i18n="add_target">添加推送目标</div>
        <div class="form-group"><label data-i18n="target_name">目标名称</label><input type="text" id="target-name"></div>
        <div class="form-row">
            <div class="form-group"><label data-i18n="target_ip">目标IP</label><input type="text" id="target-ip"></div>
            <div class="form-group"><label data-i18n="target_port">目标端口</label><input type="number" id="target-port" value="8080"></div>
        </div>
        <div class="form-actions"><button class="btn" onclick="closeModal('target')" data-i18n="cancel">取消</button><button class="btn btn-primary" onclick="addTarget()" data-i18n="save">保存</button></div></div></div>

<script>
const LANG_NAMES = {json.dumps(LANG_NAMES, ensure_ascii=False)};
let translations = {{}}, currentLang = 'zh_CN';

function initLangSelect() {{
    const sel = document.getElementById('langSelect');
    Object.entries(LANG_NAMES).forEach(([code, name]) => {{
        const opt = document.createElement('option');
        opt.value = code; opt.textContent = name;
        if (code === currentLang) opt.selected = true;
        sel.appendChild(opt);
    }});
    sel.addEventListener('change', () => loadTranslations(sel.value));
}}

async function loadTranslations(lang) {{
    currentLang = lang;
    try {{
        const res = await fetch('/api/i18n/?lang=' + lang);
        translations = await res.json();
        applyTranslations();
    }} catch (e) {{ console.error('Failed to load translations'); }}
}}

function applyTranslations() {{
    document.querySelectorAll('[data-i18n]').forEach(el => {{
        const key = el.dataset.i18n;
        if (translations[key]) el.textContent = translations[key];
    }});
    if (translations['app_name']) {{
        document.getElementById('app-title').textContent = translations['app_name'] + ' - ' + (translations['dashboard'] || '管理控制台');
    }}
}}

document.querySelectorAll('.nav-item').forEach(item => {{
    item.addEventListener('click', () => {{
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        item.classList.add('active');
        document.getElementById('page-' + item.dataset.page).classList.add('active');
        if (item.dataset.page === 'push') {{
            loadPushTargets();
            updatePushTargetSelect();
            loadPushHistory();
        }} else if (item.dataset.page === 'dashboard') {{
            loadLocalIPs();
        }} else if (item.dataset.page === 'storage') {{
            loadVolumes();
        }} else if (item.dataset.page === 'users') {{
            loadUsers();
        }} else if (item.dataset.page === 'shares') {{
            loadShares();
        }}
    }});
}});

async function loadDashboard() {{
    try {{
        const [v, u, s, smb] = await Promise.all([
            fetch('/api/storage/volumes').then(r => r.json()),
            fetch('/api/users').then(r => r.json()),
            fetch('/api/smb/shares').then(r => r.json()),
            fetch('/api/smb/status').then(r => r.json())
        ]);
        document.getElementById('stat-volumes').textContent = v.volumes ? v.volumes.length : 0;
        document.getElementById('stat-users').textContent = u.users ? u.users.length : 0;
        document.getElementById('stat-shares').textContent = s.shares ? s.shares.length : 0;
        document.getElementById('stat-status').textContent = smb.running ? (translations['running'] || '运行中') : (translations['stopped'] || '已停止');
    }} catch (e) {{ console.error(e); }}
}}

async function loadLocalIPs() {{
    try {{
        const res = await fetch('/api/ip/local');
        const data = await res.json();
        const container = document.getElementById('local-ips');
        container.innerHTML = '';
        if (data.ips && data.ips.length) {{
            data.ips.forEach(ip => {{
                const div = document.createElement('div');
                div.className = 'ip-item';
                const typeColor = ip.type === 'wan' ? '#48bb78' : (ip.type === 'lan' ? '#4299e1' : '#a0aec0');
                const typeLabel = ip.type === 'wan' ? '出口' : (ip.type === 'lan' ? '局域网' : '本地');
                div.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;width:100%;">' +
                    '<div><div class="ip" style="font-size:16px;">' + ip.ip + '</div>' +
                    '<div style="font-size:12px;color:#666;margin-top:2px;">' + (ip.name || ip.adapter) + ' | ' + (ip.network || '') + '</div></div>' +
                    '<div style="display:flex;align-items:center;gap:8px;">' +
                    '<span style="background:' + typeColor + ';color:white;padding:2px 8px;border-radius:10px;font-size:11px;">' + typeLabel + '</span>' +
                    '<span style="font-size:11px;color:#999;">ID:' + (ip.device_id || 'N/A') + '</span></div></div>';
                container.appendChild(div);
            }});
            // 显示设备ID
            if (data.ips[0] && data.ips[0].device_id) {{
                console.log('Device ID:', data.ips[0].device_id);
            }}
        }}
    }} catch (e) {{ console.error(e); }}
}}

async function scanLAN() {{
    const resultDiv = document.getElementById('scan-result');
    resultDiv.innerHTML = '<span style="color:#667eea;">正在扫描局域网设备...</span>';
    try {{
        const res = await fetch('/api/ip/scan?port=8080');
        const data = await res.json();
        if (data.devices && data.devices.length) {{
            let html = '<div style="margin-bottom:10px;font-weight:600;">发现 ' + data.devices.length + ' 台设备:</div>';
            data.devices.forEach(d => {{
                html += '<div class="ip-item" style="margin-bottom:8px;display:inline-flex;align-items:center;gap:10px;">' +
                    '<div><div class="ip">' + d.ip + ':' + d.port + '</div>' +
                    '<div class="type">' + (translations['online'] || '在线') + '</div></div>' +
                    '<button class="btn btn-primary btn-sm" onclick="quickAddTarget(\\'' + d.ip + '\\', ' + d.port + ')">' + (translations['add_target'] || '添加') + '</button></div>';
            }});
            resultDiv.innerHTML = html;
        }} else {{
            resultDiv.innerHTML = '<span style="color:#999;">未发现其他NAS设备</span>';
        }}
    }} catch (e) {{
        resultDiv.innerHTML = '<span style="color:#f56565;">扫描失败</span>';
    }}
}}

function quickAddTarget(ip, port) {{
    document.getElementById('target-name').value = 'NAS-' + ip.split('.')[3];
    document.getElementById('target-ip').value = ip;
    document.getElementById('target-port').value = port;
    showModal('target');
}}

async function loadVolumes() {{
    const t = translations;
    const res = await fetch('/api/storage/volumes');
    const data = await res.json();
    const tb = document.getElementById('volumes-table');
    tb.innerHTML = data.volumes && data.volumes.length ?
        data.volumes.map(v => '<tr><td>' + v.name + '</td><td>' + v.path + '</td><td>' + v.quota_gb + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteVolume(\\'' + v.name + '\\')">' + (t.delete || '删除') + '</button></td></tr>').join('') :
        '<tr><td colspan="4" style="text-align:center;color:#999;">' + (t.no_data || '暂无数据') + '</td></tr>';
}}

async function loadUsers() {{
    const t = translations;
    const res = await fetch('/api/users');
    const data = await res.json();
    const tb = document.getElementById('users-table');
    tb.innerHTML = data.users && data.users.length ?
        data.users.map(u => '<tr><td>' + u.username + '</td><td>' + u.home_dir + '</td><td>' + u.storage_quota_gb + '</td><td><span class="badge ' + (u.is_admin ? 'badge-success' : 'badge-warning') + '">' + (u.is_admin ? (t.yes || '是') : (t.no || '否')) + '</span></td><td><button class="btn btn-danger btn-sm" onclick="deleteUser(\\'' + u.username + '\\')">' + (t.delete || '删除') + '</button></td></tr>').join('') :
        '<tr><td colspan="5" style="text-align:center;color:#999;">' + (t.no_data || '暂无数据') + '</td></tr>';
}}

async function loadShares() {{
    const t = translations;
    const res = await fetch('/api/smb/shares');
    const data = await res.json();
    const tb = document.getElementById('shares-table');
    tb.innerHTML = data.shares && data.shares.length ?
        data.shares.map(s => '<tr><td>' + s.name + '</td><td>' + s.path + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteShare(\\'' + s.name + '\\')">' + (t.delete || '删除') + '</button></td></tr>').join('') :
        '<tr><td colspan="3" style="text-align:center;color:#999;">' + (t.no_data || '暂无数据') + '</td></tr>';
}}

async function loadPushTargets() {{
    const t = translations;
    const res = await fetch('/api/push/targets');
    const data = await res.json();
    const tb = document.getElementById('targets-table');
    tb.innerHTML = data.targets && data.targets.length ?
        data.targets.map(t => '<tr><td>' + t.name + '</td><td>' + t.ip + ':' + t.port + '</td><td><button class="btn btn-success btn-sm" onclick="checkTarget(\\'' + t.id + '\\')">' + (t2 => t2['scan'] || '检测')(translations) + '</button> <button class="btn btn-danger btn-sm" onclick="deleteTarget(\\'' + t.id + '\\')">' + (translations['delete'] || '删除') + '</button></td></tr>').join('') :
        '<tr><td colspan="3" style="text-align:center;color:#999;">' + (translations['no_data'] || '暂无数据') + '</td></tr>';
}}

async function updatePushTargetSelect() {{
    const res = await fetch('/api/push/targets');
    const data = await res.json();
    const sel = document.getElementById('push-target-select');
    sel.innerHTML = '<option value="">请选择目标设备</option>';
    if (data.targets) {{
        data.targets.forEach(t => {{
            sel.innerHTML += '<option value="' + t.id + '">' + t.name + ' (' + t.ip + ':' + t.port + ')</option>';
        }});
    }}
}}

async function checkTarget(id) {{
    const res = await fetch('/api/push/targets/check', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{id}})
    }});
    const data = await res.json();
    alert(data.status);
}}

async function addTarget() {{
    const name = document.getElementById('target-name').value;
    const ip = document.getElementById('target-ip').value;
    const port = parseInt(document.getElementById('target-port').value);
    if (!name || !ip) {{ alert('请填写名称和IP'); return; }}
    await fetch('/api/push/targets', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{name, ip, port}})
    }});
    closeModal('target');
    loadPushTargets();
    updatePushTargetSelect();
}}

async function deleteTarget(id) {{
    if (confirm('确认删除此目标?')) {{
        await fetch('/api/push/targets/delete', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{id}})
        }});
        loadPushTargets();
        updatePushTargetSelect();
    }}
}}

async function startPush() {{
    const targetId = document.getElementById('push-target-select').value;
    const folderPath = document.getElementById('push-folder-path').value;
    if (!targetId) {{ alert('请选择目标设备'); return; }}
    if (!folderPath) {{ alert('请输入文件夹路径'); return; }}

    const btn = document.getElementById('push-btn');
    btn.disabled = true;
    btn.textContent = translations['pushing'] || '推送中...';

    document.getElementById('push-progress').style.width = '5%';
    document.getElementById('push-status-text').textContent = '准备推送...';

    try {{
        await fetch('/api/push/folder', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{target_id: targetId, folder_path: folderPath}})
        }});
        pollPushStatus();
    }} catch (e) {{
        btn.disabled = false;
        btn.textContent = translations['push_now'] || '立即推送';
        alert('推送启动失败');
    }}
}}

function pollPushStatus() {{
    let count = 0;
    const interval = setInterval(async () => {{
        try {{
            const res = await fetch('/api/push/status');
            const data = await res.json();
            if (data.active) {{
                const pct = Math.round((data.active.sent_files / data.active.total_files) * 100);
                document.getElementById('push-progress').style.width = pct + '%';
                document.getElementById('push-status-text').textContent =
                    data.active.sent_files + ' / ' + data.active.total_files + ' 个文件';
            }} else {{
                clearInterval(interval);
                document.getElementById('push-progress').style.width = '100%';
                document.getElementById('push-status-text').textContent = translations['success'] || '推送完成';
                const btn = document.getElementById('push-btn');
                btn.disabled = false;
                btn.textContent = translations['push_now'] || '立即推送';
                loadPushHistory();
            }}
            count++;
            if (count > 600) clearInterval(interval);
        }} catch (e) {{
            clearInterval(interval);
        }}
    }}, 1000);
}}

async function loadPushHistory() {{
    const t = translations;
    const res = await fetch('/api/push/status');
    const data = await res.json();
    const tb = document.getElementById('push-history');
    if (data.history && data.history.length) {{
        tb.innerHTML = data.history.map(h => '<tr><td>' + (h.time || '') + '</td><td>' + h.target + '</td><td>' + h.folder + '</td><td>' + h.sent_files + ' / ' + h.total_files + '</td><td><span class="badge ' + (h.status === 'success' ? 'badge-success' : 'badge-danger') + '">' + (h.status === 'success' ? (t['success'] || '成功') : (t['failed'] || '失败')) + '</span></td></tr>').join('');
    }} else {{
        tb.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">' + (t['no_data'] || '暂无数据') + '</td></tr>';
    }}
}}

function showModal(type) {{ document.getElementById('modal-' + type).classList.add('show'); }}
function closeModal(type) {{ document.getElementById('modal-' + type).classList.remove('show'); }}

async function createVolume() {{
    const name = document.getElementById('storage-name').value;
    const path = document.getElementById('storage-path').value;
    const quota = parseInt(document.getElementById('storage-quota').value);
    await fetch('/api/storage/volumes', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{name, path, quota_gb: quota}}) }});
    closeModal('storage'); loadVolumes(); loadDashboard();
}}

async function createUser() {{
    const name = document.getElementById('user-name').value;
    const password = document.getElementById('user-password').value;
    await fetch('/api/users', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{username: name, password}}) }});
    closeModal('user'); loadUsers(); loadDashboard();
}}

async function createShare() {{
    const name = document.getElementById('share-name').value;
    const path = document.getElementById('share-path').value;
    await fetch('/api/smb/shares', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{name, path}}) }});
    closeModal('share'); loadShares(); loadDashboard();
}}

async function deleteVolume(name) {{
    if (confirm('确认删除 ' + name + '?')) {{
        await fetch('/api/storage/volumes/delete', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{name}}) }});
        loadVolumes(); loadDashboard();
    }}
}}

async function deleteUser(username) {{
    if (confirm('确认删除 ' + username + '?')) {{
        await fetch('/api/users/delete', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{username}}) }});
        loadUsers(); loadDashboard();
    }}
}}

async function deleteShare(name) {{
    if (confirm('确认删除 ' + name + '?')) {{
        await fetch('/api/smb/shares/delete', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{name}}) }});
        loadShares(); loadDashboard();
    }}
}}

initLangSelect();
loadTranslations('zh_CN');
loadDashboard();
loadLocalIPs();
</script>
</body>
</html>"""


# ==========================================
# 服务器启动
# ==========================================
def run_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), NASHandler)
    local_ips = ip_mgr.get_local_ips()
    print("=" * 50)
    print("  小思超级NAS服务启动")
    print("=" * 50)
    print(f"  本地访问: http://localhost:{port}")
    for ip_info in local_ips:
        if ip_info["type"] != "loopback":
            print(f"  网络访问: http://{ip_info['ip']}:{port}")
    print(f"  接收目录: {os.path.abspath(config.receive_dir)}")
    print("=" * 50)
    print("  按 Ctrl+C 停止服务")
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.shutdown()


if __name__ == "__main__":
    run_server()
