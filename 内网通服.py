import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import socket
import time
import os
import sys
import http.server
import socketserver
import ssl

# ==============================
# N - Network 网络层
# ==============================
class NetworkLayer:
    @staticmethod
    def get_local_ips():
        ips = []
        try:
            hostname = socket.gethostname()
            addrs = socket.gethostbyname_ex(hostname)[2]
            for ip in addrs:
                if not ip.startswith("127."):
                    ips.append(ip)
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 8))
            main_ip = s.getsockname()[0]
            s.close()
            if main_ip not in ips:
                ips.insert(0, main_ip)
        except Exception:
            pass
        return list(set(ips))

# ==============================
# E - Engine 引擎层
# ==============================
class VPNEngine:
    def __init__(self):
        self.local_ips = NetworkLayer.get_local_ips()
        self.logs = []

        self.p2p_server = None
        self.web_dir = os.getcwd()
        self.web_port = 8080
        self.http_server = None
        self.https_server = None
        self.ftp_dir = os.getcwd()
        self.ftp_port = 2121
        self.ftp_user = "user"
        self.ftp_pwd = "123456"
        self.ftp_server = None

    def refresh_ips(self):
        self.local_ips = NetworkLayer.get_local_ips()

    def log(self, msg):
        t = time.strftime("%H:%M:%S")
        self.logs.append(f"[{t}] {msg}")
        if len(self.logs) > 200:
            self.logs.pop(0)

# ==============================
# 静音 HTTP 处理器
# ==============================
class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_GET(self):
        try:
            if "favicon" in self.path:
                self.send_response(204)
                self.end_headers()
                return
            super().do_GET()
        except:
            return

# ==============================
# G - GUI 界面层
# ==============================
class VPNGui:
    def __init__(self, engine):
        self.root = tk.Tk()
        self.engine = engine
        self.root.title("内网通服")

        icon_path = './config/xiaosi.ico'
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass

        self.root.geometry("780x900")
        self.root.resizable(False, False)

        # 退出确认绑定
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)

        self.var_target_ip = tk.StringVar()
        self.var_p2p_port = tk.StringVar(value="20250")
        self.var_web_port = tk.StringVar(value="8080")
        self.var_https_port = tk.StringVar(value="4433")
        self.var_ftp_port = tk.StringVar(value="2121")
        self.var_ftp_user = tk.StringVar(value="user")
        self.var_ftp_pwd = tk.StringVar(value="123456")

        self.selected_nic_ip = tk.StringVar()
        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="内网通服", font=("微软雅黑", 18, "bold")).pack(pady=10)

        # 网卡选择
        frame_nic = ttk.LabelFrame(self.root, text="选择网卡")
        frame_nic.pack(fill="x", padx=20, pady=5)
        ttk.Label(frame_nic, text="本机IP:").grid(row=0, column=0, padx=5, pady=5)
        self.nic_combobox = ttk.Combobox(frame_nic, textvariable=self.selected_nic_ip, state="readonly", width=20)
        self.nic_combobox.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame_nic, text="刷新网卡", command=self.refresh_nic).grid(row=0, column=2, padx=5, pady=5)

        # IP 列表
        frame_ip = ttk.LabelFrame(self.root, text="本机IP地址")
        frame_ip.pack(fill="x", padx=20, pady=5)
        self.ip_list = tk.Listbox(frame_ip, height=3, font=("Consolas", 10))
        self.ip_list.pack(fill="x", padx=5, pady=5)

        # 组网
        frame_p2p = ttk.LabelFrame(self.root, text="异地组网服务")
        frame_p2p.pack(fill="x", padx=20, pady=5)
        ttk.Label(frame_p2p, text="目标IP：").grid(row=0,column=0,padx=5,pady=5)
        ttk.Entry(frame_p2p, textvariable=self.var_target_ip,width=16).grid(row=0,column=1,padx=5)
        ttk.Label(frame_p2p, text="端口：").grid(row=0,column=2,padx=5)
        ttk.Entry(frame_p2p, textvariable=self.var_p2p_port,width=8).grid(row=0,column=3,padx=5)
        ttk.Button(frame_p2p, text="启动组网", command=self.start_p2p).grid(row=1,column=0,padx=5,pady=5)
        ttk.Button(frame_p2p, text="停止组网", command=self.stop_p2p).grid(row=1,column=1,padx=5,pady=5)
        ttk.Button(frame_p2p, text="连接组网", command=self.connect_p2p).grid(row=1,column=2,padx=5,pady=5)

        # HTTP
        frame_http = ttk.LabelFrame(self.root, text="HTTP 网站服务")
        frame_http.pack(fill="x", padx=20, pady=5)
        ttk.Label(frame_http, text="端口：").grid(row=0,column=0,padx=5,pady=5)
        ttk.Entry(frame_http, textvariable=self.var_web_port,width=8).grid(row=0,column=1,padx=5)
        self.lbl_http_dir = ttk.Label(frame_http, text=f"目录：{self.engine.web_dir}")
        self.lbl_http_dir.grid(row=1,column=0,columnspan=2,sticky="w",padx=5,pady=3)
        ttk.Button(frame_http, text="选择网站文件夹", command=self.choose_http_dir).grid(row=2,column=0,padx=5,pady=4)
        ttk.Button(frame_http, text="启动HTTP", command=self.start_http).grid(row=2,column=1,padx=5,pady=4)
        ttk.Button(frame_http, text="停止HTTP", command=self.stop_http).grid(row=2,column=2,padx=5,pady=4)

        # HTTPS
        frame_https = ttk.LabelFrame(self.root, text="HTTPS 加密服务")
        frame_https.pack(fill="x", padx=20, pady=5)
        ttk.Label(frame_https, text="HTTPS端口：").grid(row=0,column=0,padx=5,pady=5)
        ttk.Entry(frame_https, textvariable=self.var_https_port,width=8).grid(row=0,column=1,padx=5)
        ttk.Button(frame_https, text="启动HTTPS", command=self.start_https).grid(row=1,column=0,padx=5,pady=4)
        ttk.Button(frame_https, text="停止HTTPS", command=self.stop_https).grid(row=1,column=1,padx=5,pady=4)

        # FTP
        frame_ftp = ttk.LabelFrame(self.root, text="FTP 文件服务")
        frame_ftp.pack(fill="x", padx=20, pady=8)
        ttk.Label(frame_ftp, text="端口：").grid(row=0,column=0,padx=5,pady=4)
        ttk.Entry(frame_ftp, textvariable=self.var_ftp_port,width=8).grid(row=0,column=1,padx=5)
        ttk.Label(frame_ftp, text="用户：").grid(row=1,column=0,padx=5,pady=4)
        ttk.Entry(frame_ftp, textvariable=self.var_ftp_user,width=10).grid(row=1,column=1,padx=5)
        ttk.Label(frame_ftp, text="密码：").grid(row=2,column=0,padx=5,pady=4)
        ttk.Entry(frame_ftp, textvariable=self.var_ftp_pwd,width=10,show="*").grid(row=2,column=1,padx=5)
        self.lbl_ftp_dir = ttk.Label(frame_ftp, text=f"FTP目录：{self.engine.ftp_dir}")
        self.lbl_ftp_dir.grid(row=3,column=0,columnspan=2,sticky="w",padx=5,pady=3)
        ttk.Button(frame_ftp, text="选择FTP文件夹", command=self.choose_ftp_dir).grid(row=4,column=0,padx=5,pady=4)
        ttk.Button(frame_ftp, text="启动FTP", command=self.start_ftp).grid(row=4,column=1,padx=5,pady=4)
        ttk.Button(frame_ftp, text="停止FTP", command=self.stop_ftp).grid(row=4,column=2,padx=5,pady=4)

        # 日志
        frame_log = ttk.LabelFrame(self.root, text="运行日志")
        frame_log.pack(fill="both", expand=True, padx=20, pady=8)
        self.log_box = scrolledtext.ScrolledText(frame_log, state="disabled", height=18)
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)

        self.refresh_nic()

    # ========== 退出确认 ==========
    def confirm_exit(self):
        if messagebox.askokcancel("确认退出", "确定要关闭内网通服吗？\n所有服务将停止运行。"):
            self.stop_all_services()
            self.root.destroy()

    def stop_all_services(self):
        try:
            if self.engine.p2p_server:
                self.engine.p2p_server.close()
            if self.engine.http_server:
                self.engine.http_server.shutdown()
            if self.engine.https_server:
                self.engine.https_server.shutdown()
            if self.engine.ftp_server:
                self.engine.ftp_server.close_all()
        except:
            pass

    # ========== 工具方法 ==========
    def log(self, msg):
        self.engine.log(msg)
        self.log_box.config(state="normal")
        self.log_box.insert("end", self.engine.logs[-1] + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def refresh_nic(self):
        ips = self.engine.local_ips
        self.nic_combobox['values'] = ips
        self.ip_list.delete(0, tk.END)
        for ip in ips:
            self.ip_list.insert(tk.END, ip)
        if ips:
            self.selected_nic_ip.set(ips[0])
            self.log(f"已加载网卡: {len(ips)} 个")

    def get_selected_ip(self):
        ip = self.selected_nic_ip.get().strip()
        return ip if ip else "0.0.0.0"

    # ========== 组网 ==========
    def start_p2p(self):
        ip = self.get_selected_ip()
        port = int(self.var_p2p_port.get())
        def run():
            try:
                s = socket.socket()
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((ip, port))
                s.listen(5)
                self.engine.p2p_server = s
                self.log(f"组网服务已启动 {ip}:{port}")
                while True:
                    if not self.engine.p2p_server: break
                    c,a = s.accept()
                    self.log(f"客户端接入 {a}")
                    c.close()
            except Exception as e:
                self.log(f"组网异常: {e}")
        threading.Thread(target=run,daemon=True).start()

    def stop_p2p(self):
        if self.engine.p2p_server:
            self.engine.p2p_server.close()
            self.engine.p2p_server = None
            self.log("组网服务已停止")

    def connect_p2p(self):
        ip = self.var_target_ip.get().strip()
        port = int(self.var_p2p_port.get())
        def run():
            try:
                s = socket.socket()
                s.settimeout(5)
                s.connect((ip,port))
                self.log(f"已连接 {ip}:{port}")
                s.close()
            except Exception as e:
                self.log(f"连接失败: {e}")
        threading.Thread(target=run,daemon=True).start()

    # ========== HTTP ==========
    def choose_http_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.engine.web_dir = d
            self.lbl_http_dir.config(text=f"目录：{d}")
            self.log(f"HTTP目录: {d}")

    def start_http(self):
        ip = self.get_selected_ip()
        port = int(self.var_web_port.get())
        web_dir = self.engine.web_dir
        def run():
            try:
                os.chdir(web_dir)
                self.engine.http_server = socketserver.TCPServer((ip, port), QuietHTTPHandler)
                self.log(f"HTTP服务启动 {ip}:{port}")
                self.log(f"→ http://{ip}:{port}")
                self.engine.http_server.serve_forever()
            except Exception as e:
                self.log(f"HTTP异常: {e}")
        threading.Thread(target=run,daemon=True).start()

    def stop_http(self):
        if self.engine.http_server:
            self.engine.http_server.shutdown()
            self.engine.http_server = None
            self.log("HTTP服务已停止")

    # ========== HTTPS ==========
    def start_https(self):
        ip = self.get_selected_ip()
        port = int(self.var_https_port.get())
        web_dir = self.engine.web_dir

        def run():
            try:
                os.chdir(web_dir)
                httpd = socketserver.TCPServer((ip, port), QuietHTTPHandler)
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
                self.engine.https_server = httpd
                self.log(f"HTTPS服务启动 {ip}:{port}")
                self.log(f"→ https://{ip}:{port}")
                httpd.serve_forever()
            except Exception as e:
                self.log(f"HTTPS异常: {e}")
        threading.Thread(target=run, daemon=True).start()

    def stop_https(self):
        if self.engine.https_server:
            self.engine.https_server.shutdown()
            self.engine.https_server = None
            self.log("HTTPS服务已停止")

    # ========== FTP ==========
    def choose_ftp_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.engine.ftp_dir = d
            self.lbl_ftp_dir.config(text=f"FTP目录：{d}")
            self.log(f"FTP目录: {d}")

    def start_ftp(self):
        ip = self.get_selected_ip()
        try:
            from pyftpdlib.authorizers import DummyAuthorizer
            from pyftpdlib.handlers import FTPHandler
            from pyftpdlib.servers import FTPServer
        except:
            self.log("正在安装FTP依赖...")
            os.system(f'"{sys.executable}" -m pip install pyftpdlib -i https://pypi.tuna.tsinghua.edu.cn/simple')
            from pyftpdlib.authorizers import DummyAuthorizer
            from pyftpdlib.handlers import FTPHandler
            from pyftpdlib.servers import FTPServer

        port = int(self.var_ftp_port.get())
        user = self.var_ftp_user.get().strip()
        pwd = self.var_ftp_pwd.get().strip()
        path = self.engine.ftp_dir

        def run():
            try:
                auth = DummyAuthorizer()
                auth.add_user(user,pwd,path,perm="elradfmw")
                handler = FTPHandler
                handler.authorizer = auth
                self.engine.ftp_server = FTPServer((ip,port),handler)
                self.log(f"FTP启动 {ip}:{port}")
                self.log(f"ftp://{user}:{pwd}@{ip}:{port}")
                self.engine.ftp_server.serve_forever()
            except Exception as e:
                self.log(f"FTP异常: {e}")
        threading.Thread(target=run,daemon=True).start()

    def stop_ftp(self):
        if self.engine.ftp_server:
            self.engine.ftp_server.close_all()
            self.engine.ftp_server = None
            self.log("FTP服务已停止")

    def run(self):
        self.root.mainloop()

# ==============================
# 程序入口
# ==============================
if __name__ == "__main__":
    engine = VPNEngine()
    app = VPNGui(engine)
    app.run()