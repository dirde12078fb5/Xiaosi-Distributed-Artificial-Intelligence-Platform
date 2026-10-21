#  Copyright (c) 2026. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
#  Morbi non lorem porttitor neque feugiat blandit. Ut vitae ipsum eget quam lacinia accumsan.
#  Etiam sed turpis ac ipsum condimentum fringilla. Maecenas magna.
#  Proin dapibus sapien vel ante. Aliquam erat volutpat. Pellentesque sagittis ligula eget metus.
#  Vestibulum commodo. Ut rhoncus gravida arcu.

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import re
import os

class WiFiScannerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Xiao Si Artificial Intelligence WiFi Scanner")
        self.root.geometry("800x800")

        # 设置窗口图标（如果有的话）
        self.root.iconbitmap('./xiaosi.ico')

        # 设置现代化样式
        self.style = ttk.Style()
        self.style.theme_use('clam') # 使用更现代的主题

        # 定义颜色变量
        self.colors = {
            "bg": "#f0f2f5",       # 背景灰
            "card": "#ffffff",    # 卡片白
            "primary": "#007bff", # 主色调蓝
            "text": "#333333",    # 文字黑
            "success": "#28a745", # 成功绿
            "warning": "#ffc107", # 警告黄
            "danger": "#dc3545"   # 危险红
        }

        # 配置主窗口背景
        self.root.configure(bg=self.colors["bg"])

        # 初始化UI组件
        self.create_widgets()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # --- 顶部标题栏 ---
        header_frame = tk.Frame(self.root, bg=self.colors["card"], pady=20)
        header_frame.pack(fill="x", padx=20, pady=20)

        title_label = tk.Label(
            header_frame,
            text="Xiao Si Artificial Intelligence WiFi Scanner",
            font=("Microsoft YaHei UI", 24, "bold"),
            bg=self.colors["card"],
            fg=self.colors["primary"]
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="快速扫描并分析附近的无线网络信号",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg="#666666"
        )
        subtitle_label.pack(pady=5)

        # --- 控制区域 ---
        control_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=10)
        control_frame.pack(fill="x", padx=20)

        self.scan_button = tk.Button(
            control_frame,
            text="开始扫描",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.colors["primary"],
            fg="white",
            activebackground="#0056b3",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.start_scan_thread,
            padx=20,
            pady=10
        )
        self.scan_button.pack(side="left", padx=5)

        # --- 连接控制区域 ---
        connect_frame = tk.Frame(self.root, bg=self.colors["bg"], pady=10)
        connect_frame.pack(fill="x", padx=20)

        tk.Label(
            connect_frame,
            text="密码:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["bg"],
            fg=self.colors["text"]
        ).pack(side="left", padx=5)

        self.password_entry = tk.Entry(
            connect_frame,
            font=("Microsoft YaHei UI", 10),
            show="*",
            width=20
        )
        self.password_entry.pack(side="left", padx=5)

        self.connect_button = tk.Button(
            connect_frame,
            text="连接网络",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.colors["success"],
            fg="white",
            activebackground="#218838",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.start_connect_thread,
            padx=20,
            pady=10
        )
        self.connect_button.pack(side="left", padx=5)

        # --- 结果显示区域 ---
        result_frame = tk.Frame(self.root, bg=self.colors["card"], padx=10, pady=10)
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 使用 Treeview 显示表格数据
        columns = ("ssid", "signal", "type", "auth")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)

        # 定义列标题
        self.tree.heading("ssid", text="网络名称 (SSID)")
        self.tree.heading("signal", text="信号强度")
        self.tree.heading("type", text="网络类型")
        self.tree.heading("auth", text="加密方式")

        # 设置列宽和对齐
        self.tree.column("ssid", width=300, anchor="w")
        self.tree.column("signal", width=100, anchor="center")
        self.tree.column("type", width=100, anchor="center")
        self.tree.column("auth", width=150, anchor="center")

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- 底部状态栏 ---
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg=self.colors["bg"],
            fg="#666666",
            font=("Microsoft YaHei UI", 9)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def start_scan_thread(self):
        # 防止重复点击
        self.scan_button.config(state=tk.DISABLED, text="扫描中...")
        self.status_var.set("正在扫描附近的 WiFi 网络，请稍候...")

        # 使用线程避免界面卡顿
        threading.Thread(target=self.scan_networks, daemon=True).start()

    def scan_networks(self):
        try:
            # 清空旧数据
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 执行系统命令，使用UTF-8编码并忽略错误
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'  # 忽略编码错误
            )

            output_lines = result.stdout.split('\n')
            current_network = {}

            # 解析命令输出
            for line in output_lines:
                line = line.strip()
                if line.startswith("SSID"):
                    # 如果之前有数据，先插入
                    if current_network:
                        self.insert_network(current_network)
                        current_network = {}
                    # 提取 SSID 名称
                    match = re.search(r':\s*(.*)', line)
                    if match:
                        current_network['ssid'] = match.group(1).strip()
                elif "信号" in line or "Signal" in line:
                    match = re.search(r'[:\s]+(\d+)%', line)
                    if match:
                        signal = int(match.group(1))
                        current_network['signal'] = signal
                        # 根据信号强度设置标签颜色（这里仅存储数值，显示时处理）
                elif "类型" in line or "Type" in line:
                    match = re.search(r':\s*(.*)', line)
                    if match:
                        current_network['type'] = match.group(1).strip()
                elif "身份验证" in line or "Authentication" in line:
                    match = re.search(r':\s*(.*)', line)
                    if match:
                        current_network['auth'] = match.group(1).strip()

            # 插入最后一个网络
            if current_network:
                self.insert_network(current_network)

            self.status_var.set(f"扫描完成，共发现 {len(self.tree.get_children())} 个网络")

        except Exception as e:
            self.status_var.set("扫描过程中发生错误")
            messagebox.showerror("错误", f"无法完成扫描: {e}")
        finally:
            # 恢复按钮状态
            self.scan_button.config(state=tk.NORMAL, text="开始扫描")

    def insert_network(self, network):
        ssid = network.get('ssid', '未知')
        signal = network.get('signal', 0)
        net_type = network.get('type', '未知')
        auth = network.get('auth', '未知')

        # 简单的信号强度格式化
        signal_str = f"{signal}%"

        # 插入数据
        self.tree.insert("", "end", values=(ssid, signal_str, net_type, auth))

    def start_connect_thread(self):
        # 获取选中的网络
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一个网络")
            return

        # 获取网络SSID
        ssid = self.tree.item(selected_item[0], "values")[0]
        password = self.password_entry.get()

        if not password:
            messagebox.showwarning("警告", "请输入密码")
            return

        # 禁用按钮
        self.connect_button.config(state=tk.DISABLED, text="连接中...")
        self.status_var.set(f"正在连接到 {ssid}...")

        # 使用线程避免界面卡顿
        threading.Thread(
            target=self.connect_network,
            args=(ssid, password),
            daemon=True
        ).start()

    def connect_network(self, ssid, password):
        try:
            # 创建配置文件
            profile = f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""

            # 保存配置文件
            profile_path = os.path.join(os.path.expanduser("~"), f"{ssid}.xml")
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(profile)

            # 添加配置文件
            subprocess.run(
                ['netsh', 'wlan', 'add', 'profile', f'filename={profile_path}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 连接网络
            result = subprocess.run(
                ['netsh', 'wlan', 'connect', f'name={ssid}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 删除临时配置文件
            if os.path.exists(profile_path):
                os.remove(profile_path)

            if "成功" in result.stdout or "successfully" in result.stdout.lower():
                self.status_var.set(f"成功连接到 {ssid}")
                messagebox.showinfo("成功", f"已成功连接到 {ssid}")
            else:
                self.status_var.set(f"连接到 {ssid} 失败")
                messagebox.showerror("错误", f"无法连接到 {ssid}\n{result.stderr}")

        except Exception as e:
            self.status_var.set("连接过程中发生错误")
            messagebox.showerror("错误", f"无法完成连接: {e}")
        finally:
            # 恢复按钮状态
            self.connect_button.config(state=tk.NORMAL, text="连接网络")
            self.password_entry.delete(0, tk.END)

    def apply_filter(self, event=None):
        """应用信号强度过滤"""
        try:
            # 这里可以添加过滤逻辑
            # 例如根据信号强度过滤网络
            pass
        except Exception as e:
            self.status_var.set("应用过滤时发生错误")
            messagebox.showerror("错误", f"无法应用过滤: {e}")

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出 WiFi Scanner Pro Max 吗？"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WiFiScannerPro(root)
    root.mainloop()