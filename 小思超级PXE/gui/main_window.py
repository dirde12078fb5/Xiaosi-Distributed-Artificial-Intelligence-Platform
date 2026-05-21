#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE GUI主窗口 - 美化版
包含网卡选择功能和现代化界面设计
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
import json
from pathlib import Path

from pxe_server import SuperPXE
from pxe import BootManager
from utils import check_admin_privileges, get_local_ip, get_network_interfaces


class ModernGUI:
    """现代化GUI设计"""
    COLORS = {
        'primary': '#2196F3',      # 蓝色
        'success': '#4CAF50',      # 绿色
        'warning': '#FF9800',      # 橙色
        'danger': '#F44336',       # 红色
        'dark': '#212121',         # 深灰
        'light': '#FAFAFA',        # 浅灰
        'white': '#FFFFFF',
        'gray': '#757575',
        'bg_color': '#ECEFF1',     # 背景色
        'card_color': '#FFFFFF',   # 卡片色
    }
    
    FONTS = {
        'title': ('Microsoft YaHei UI', 20, 'bold'),
        'heading': ('Microsoft YaHei UI', 14, 'bold'),
        'body': ('Microsoft YaHei UI', 10),
        'small': ('Microsoft YaHei UI', 9),
    }


class TextHandler(logging.Handler):
    """日志处理器"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        msg = self.format(record) + '\n'
        self.text_widget.after(0, self._append_text, msg)
    
    def _append_text(self, msg):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, msg)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("小思超级PXE - 网络安装系统")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 700)
        
        self.pxe = None
        self.pxe_thread = None
        self.running = False
        self.boot_manager = BootManager()
        
        self._setup_style()
        self._setup_ui()
        self._setup_logging()
        self._load_config()
        self._refresh_interfaces()
    
    def _setup_style(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel',
                       font=ModernGUI.FONTS['title'],
                       foreground=ModernGUI.COLORS['dark'])
        
        style.configure('Heading.TLabel',
                       font=ModernGUI.FONTS['heading'],
                       foreground=ModernGUI.COLORS['dark'])
        
        style.configure('Card.TFrame', background=ModernGUI.COLORS['card_color'])
        
        style.configure('Success.TButton',
                       font=ModernGUI.FONTS['body'],
                       foreground=ModernGUI.COLORS['white'],
                       background=ModernGUI.COLORS['success'])
        
        style.configure('Danger.TButton',
                       font=ModernGUI.FONTS['body'],
                       foreground=ModernGUI.COLORS['white'],
                       background=ModernGUI.COLORS['danger'])
        
        style.configure('Info.TButton',
                       font=ModernGUI.FONTS['body'],
                       foreground=ModernGUI.COLORS['white'],
                       background=ModernGUI.COLORS['primary'])
    
    def _setup_ui(self):
        """设置UI"""
        self.root.configure(bg=ModernGUI.COLORS['bg_color'])
        
        main_frame = tk.Frame(self.root, bg=ModernGUI.COLORS['bg_color'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self._create_header(main_frame)
        self._create_control_panel(main_frame)
        self._create_notebook(main_frame)
        self._create_log_panel(main_frame)
    
    def _create_header(self, parent):
        """创建头部"""
        header_frame = tk.Frame(parent, bg=ModernGUI.COLORS['primary'], relief=tk.RAISED, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame,
            text="🚀 小思超级PXE - Python跨平台网络安装系统",
            font=ModernGUI.FONTS['title'],
            fg=ModernGUI.COLORS['white'],
            bg=ModernGUI.COLORS['primary'],
            pady=15
        )
        title_label.pack()
        
        self.ip_label = tk.Label(
            header_frame,
            text=f"服务器IP: {get_local_ip()}",
            font=ModernGUI.FONTS['body'],
            fg=ModernGUI.COLORS['white'],
            bg=ModernGUI.COLORS['primary']
        )
        self.ip_label.pack(pady=(0, 10))
    
    def _create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = tk.Frame(parent, bg=ModernGUI.COLORS['card_color'], relief=tk.RAISED, bd=1)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        inner_frame = tk.Frame(control_frame, bg=ModernGUI.COLORS['card_color'], padx=15, pady=15)
        inner_frame.pack(fill=tk.X)
        
        tk.Label(inner_frame, text="🎛️ 服务器控制", font=ModernGUI.FONTS['heading'],
                bg=ModernGUI.COLORS['card_color'], fg=ModernGUI.COLORS['dark']).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        self.start_button = tk.Button(
            inner_frame,
            text="▶️ 启动服务器",
            command=self._start_server,
            font=ModernGUI.FONTS['body'],
            bg=ModernGUI.COLORS['success'],
            fg=ModernGUI.COLORS['white'],
            relief=tk.RAISED,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        self.start_button.grid(row=1, column=0, padx=(0, 10), sticky=tk.W)
        
        self.stop_button = tk.Button(
            inner_frame,
            text="⏹️ 停止服务器",
            command=self._stop_server,
            font=ModernGUI.FONTS['body'],
            bg=ModernGUI.COLORS['danger'],
            fg=ModernGUI.COLORS['white'],
            state=tk.DISABLED,
            relief=tk.RAISED,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        self.stop_button.grid(row=1, column=1, padx=(0, 10), sticky=tk.W)
        
        self.status_label = tk.Label(
            inner_frame,
            text="⏸️ 状态: 未运行",
            font=ModernGUI.FONTS['body'],
            bg=ModernGUI.COLORS['card_color'],
            fg=ModernGUI.COLORS['gray']
        )
        self.status_label.grid(row=1, column=2, sticky=tk.W)
    
    def _create_notebook(self, parent):
        """创建标签页"""
        notebook_frame = tk.Frame(parent, bg=ModernGUI.COLORS['card_color'], relief=tk.RAISED, bd=1)
        notebook_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._create_network_tab()
        self._create_server_tab()
        self._create_boot_tab()
        self._create_about_tab()
    
    def _create_network_tab(self):
        """创建网络配置标签页"""
        network_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(network_frame, text="🌐 网络配置")
        
        ttk.Label(network_frame, text="选择网卡接口", font=ModernGUI.FONTS['heading']).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(network_frame, text="网卡:", font=ModernGUI.FONTS['body']).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.interface_var = tk.StringVar()
        self.interface_combo = ttk.Combobox(
            network_frame,
            textvariable=self.interface_var,
            state='readonly',
            width=50
        )
        self.interface_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Button(network_frame, text="🔄 刷新网卡列表", command=self._refresh_interfaces).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 20)
        )
        
        separator = ttk.Separator(network_frame, orient='horizontal')
        separator.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(network_frame, text="DHCP服务器配置", font=ModernGUI.FONTS['heading']).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        self.dhcp_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(network_frame, text="启用DHCP服务", variable=self.dhcp_enabled).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=2
        )
        
        ttk.Label(network_frame, text="服务器IP:", font=ModernGUI.FONTS['body']).grid(row=6, column=0, sticky=tk.W, pady=5)
        self.server_ip_entry = ttk.Entry(network_frame, width=40)
        self.server_ip_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(network_frame, text="DHCP起始IP:", font=ModernGUI.FONTS['body']).grid(row=7, column=0, sticky=tk.W, pady=5)
        self.dhcp_start_ip = ttk.Entry(network_frame, width=40)
        self.dhcp_start_ip.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(network_frame, text="DHCP结束IP:", font=ModernGUI.FONTS['body']).grid(row=8, column=0, sticky=tk.W, pady=5)
        self.dhcp_end_ip = ttk.Entry(network_frame, width=40)
        self.dhcp_end_ip.grid(row=8, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(network_frame, text="子网掩码:", font=ModernGUI.FONTS['body']).grid(row=9, column=0, sticky=tk.W, pady=5)
        self.subnet_mask = ttk.Entry(network_frame, width=40)
        self.subnet_mask.grid(row=9, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(network_frame, text="网关:", font=ModernGUI.FONTS['body']).grid(row=10, column=0, sticky=tk.W, pady=5)
        self.gateway_entry = ttk.Entry(network_frame, width=40)
        self.gateway_entry.grid(row=10, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        separator2 = ttk.Separator(network_frame, orient='horizontal')
        separator2.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        
        ttk.Label(network_frame, text="TFTP/HTTP配置", font=ModernGUI.FONTS['heading']).grid(
            row=12, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        self.tftp_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(network_frame, text="启用TFTP服务", variable=self.tftp_enabled).grid(
            row=13, column=0, sticky=tk.W, pady=2
        )
        
        self.http_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(network_frame, text="启用HTTP服务", variable=self.http_enabled).grid(
            row=13, column=1, sticky=tk.W, pady=2
        )
        
        ttk.Label(network_frame, text="HTTP端口:", font=ModernGUI.FONTS['body']).grid(row=14, column=0, sticky=tk.W, pady=5)
        self.http_port = ttk.Entry(network_frame, width=40)
        self.http_port.grid(row=14, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        button_frame = tk.Frame(network_frame, bg=ModernGUI.COLORS['bg_color'])
        button_frame.grid(row=15, column=0, columnspan=2, sticky=tk.E, pady=(20, 0))
        
        tk.Button(
            button_frame,
            text="💾 保存配置",
            command=self._save_config,
            font=ModernGUI.FONTS['body'],
            bg=ModernGUI.COLORS['primary'],
            fg=ModernGUI.COLORS['white'],
            relief=tk.RAISED,
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="🔄 重新加载",
            command=self._load_config,
            font=ModernGUI.FONTS['body'],
            bg=ModernGUI.COLORS['gray'],
            fg=ModernGUI.COLORS['white'],
            relief=tk.RAISED,
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.LEFT)
        
        network_frame.columnconfigure(1, weight=1)
    
    def _create_server_tab(self):
        """创建服务器状态标签页"""
        server_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(server_frame, text="📊 服务器状态")
        
        ttk.Label(server_frame, text="服务状态监控", font=ModernGUI.FONTS['heading']).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15)
        )
        
        services = [
            ("🌐 DHCP服务", "dhcp", "端口: 67"),
            ("📁 TFTP服务", "tftp", "端口: 69"),
            ("🌍 HTTP服务", "http", "端口: 8080")
        ]
        
        self.service_labels = {}
        self.service_indicators = {}
        
        for i, (name, key, port_info) in enumerate(services):
            row = i + 1
            
            indicator = tk.Label(
                server_frame,
                text="⚪",
                font=('Arial', 16),
                bg=ModernGUI.COLORS['bg_color']
            )
            indicator.grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=5)
            self.service_indicators[key] = indicator
            
            ttk.Label(server_frame, text=f"{name}\n{port_info}", font=ModernGUI.FONTS['body']).grid(
                row=row, column=1, sticky=tk.W, pady=5
            )
            
            status_label = tk.Label(
                server_frame,
                text="已禁用",
                font=ModernGUI.FONTS['body'],
                fg=ModernGUI.COLORS['gray']
            )
            status_label.grid(row=row, column=2, sticky=tk.W, padx=(20, 0), pady=5)
            self.service_labels[key] = status_label
        
        separator = ttk.Separator(server_frame, orient='horizontal')
        separator.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        
        ttk.Label(server_frame, text="连接统计", font=ModernGUI.FONTS['heading']).grid(
            row=5, column=0, columnspan=3, sticky=tk.W, pady=(0, 10)
        )
        
        self.stats_label = tk.Label(
            server_frame,
            text="已分配IP: 0\n活跃租约: 0",
            font=ModernGUI.FONTS['body'],
            justify=tk.LEFT
        )
        self.stats_label.grid(row=6, column=0, columnspan=3, sticky=tk.W)
    
    def _create_boot_tab(self):
        """创建启动菜单标签页"""
        boot_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(boot_frame, text="📋 启动菜单")
        
        ttk.Label(boot_frame, text="启动菜单管理", font=ModernGUI.FONTS['heading']).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10)
        )
        
        ttk.Label(boot_frame, text="当前菜单:", font=ModernGUI.FONTS['body']).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.menu_var = tk.StringVar()
        self.menu_combo = ttk.Combobox(boot_frame, textvariable=self.menu_var, state='readonly', width=30)
        self.menu_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 5))
        self.menu_combo.bind('<<ComboboxSelected>>', self._on_menu_changed)
        
        tk.Button(
            boot_frame,
            text="🔄 刷新",
            command=self._refresh_menus,
            font=ModernGUI.FONTS['small'],
            bg=ModernGUI.COLORS['gray'],
            fg=ModernGUI.COLORS['white'],
            relief=tk.RAISED,
            padx=10,
            pady=2,
            cursor='hand2'
        ).grid(row=1, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(boot_frame, text="启动项列表:", font=ModernGUI.FONTS['body']).grid(
            row=2, column=0, columnspan=3, sticky=tk.W, pady=(10, 5)
        )
        
        list_frame = tk.Frame(boot_frame, bg=ModernGUI.COLORS['white'], relief=tk.SUNKEN, bd=1)
        list_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        columns = ("name", "type")
        self.boot_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        self.boot_tree.heading("name", text="名称")
        self.boot_tree.heading("type", text="类型")
        self.boot_tree.column("name", width=350)
        self.boot_tree.column("type", width=150)
        self.boot_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.boot_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.boot_tree.configure(yscrollcommand=scrollbar.set)
        
        button_frame = tk.Frame(boot_frame, bg=ModernGUI.COLORS['bg_color'])
        button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.E, pady=(10, 0))
        
        tk.Button(
            button_frame,
            text="➕ 添加启动项",
            command=self._add_boot_entry,
            font=ModernGUI.FONTS['body'],
            bg=ModernGUI.COLORS['success'],
            fg=ModernGUI.COLORS['white'],
            relief=tk.RAISED,
            padx=15,
            pady=6,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="➖ 删除启动项",
            command=self._remove_boot_entry,
            font=ModernGUI.FONTS['body'],
            bg=ModernGUI.COLORS['danger'],
            fg=ModernGUI.COLORS['white'],
            relief=tk.RAISED,
            padx=15,
            pady=6,
            cursor='hand2'
        ).pack(side=tk.LEFT)
        
        boot_frame.columnconfigure(1, weight=1)
        boot_frame.rowconfigure(3, weight=1)
    
    def _create_about_tab(self):
        """创建关于标签页"""
        about_frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(about_frame, text="ℹ️ 关于")
        
        about_text = """
🎯 小思超级PXE

一个纯Python实现的跨平台网络安装系统

✨ 功能特点:
  • DHCP服务器 - 自动分配IP地址
  • TFTP服务器 - 传输启动文件
  • HTTP服务器 - 传输大文件和ISO
  • 跨平台支持 - Windows/Linux/macOS
  • 图形界面 - 友好的操作界面

📋 版本: 1.0.0
👤 开发者: 小思AI助手

🔗 使用Python标准库，无需额外依赖

⚠️ 注意:
  • 需要管理员/root权限运行
  • 确保网络中没有其他DHCP服务器
  • 客户端需要支持PXE网络启动
"""
        
        ttk.Label(about_frame, text=about_text, font=ModernGUI.FONTS['body'], justify=tk.LEFT).pack(anchor=tk.W)
    
    def _create_log_panel(self, parent):
        """创建日志面板"""
        log_frame = tk.Frame(parent, bg=ModernGUI.COLORS['card_color'], relief=tk.RAISED, bd=1)
        log_frame.pack(fill=tk.X, pady=(0, 0))
        
        tk.Label(
            log_frame,
            text="📝 运行日志",
            font=ModernGUI.FONTS['heading'],
            bg=ModernGUI.COLORS['card_color'],
            fg=ModernGUI.COLORS['dark'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=15, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            state=tk.DISABLED,
            height=8,
            font=('Consolas', 9),
            bg=ModernGUI.COLORS['dark'],
            fg='#00FF00',
            insertbackground='white',
            relief=tk.SUNKEN,
            bd=1,
            padx=10,
            pady=5
        )
        self.log_text.pack(fill=tk.X, padx=15, pady=(0, 10))
    
    def _setup_logging(self):
        """设置日志"""
        logger = logging.getLogger('SuperPXE')
        logger.setLevel(logging.INFO)
        
        text_handler = TextHandler(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        text_handler.setFormatter(formatter)
        logger.addHandler(text_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _refresh_interfaces(self):
        """刷新网卡列表"""
        interfaces = get_network_interfaces()
        
        choices = []
        for iface in interfaces:
            name = iface['name']
            ips = ', '.join(iface['ip_addresses']) if iface['ip_addresses'] else '无IP'
            choices.append(f"{name} ({ips})")
        
        if choices:
            self.interface_combo['values'] = choices
            self.interface_combo.current(0)
        else:
            self.interface_combo['values'] = ['未检测到网卡']
            messagebox.showwarning("警告", "未检测到网络接口，请检查网络连接")
    
    def _load_config(self):
        """加载配置"""
        config_path = Path('config.json')
        if not config_path.exists():
            config_path = Path('config.example.json')
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                dhcp = config.get('dhcp', {})
                
                self.dhcp_enabled.set(dhcp.get('enabled', True))
                self.server_ip_entry.delete(0, tk.END)
                self.server_ip_entry.insert(0, dhcp.get('server_ip', '192.168.1.1'))
                self.dhcp_start_ip.delete(0, tk.END)
                self.dhcp_start_ip.insert(0, dhcp.get('start_ip', '192.168.1.100'))
                self.dhcp_end_ip.delete(0, tk.END)
                self.dhcp_end_ip.insert(0, dhcp.get('end_ip', '192.168.1.200'))
                self.subnet_mask.delete(0, tk.END)
                self.subnet_mask.insert(0, dhcp.get('subnet_mask', '255.255.255.0'))
                self.gateway_entry.delete(0, tk.END)
                self.gateway_entry.insert(0, dhcp.get('gateway', '192.168.1.1'))
                
                tftp = config.get('tftp', {})
                self.tftp_enabled.set(tftp.get('enabled', True))
                
                http = config.get('http', {})
                self.http_enabled.set(http.get('enabled', True))
                self.http_port.delete(0, tk.END)
                self.http_port.insert(0, str(http.get('port', 8080)))
                
                self._update_service_labels(config)
                
            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        config = {
            'dhcp': {
                'enabled': self.dhcp_enabled.get(),
                'interface': self.interface_var.get().split('(')[0].strip(),
                'port': 67,
                'server_ip': self.server_ip_entry.get(),
                'start_ip': self.dhcp_start_ip.get(),
                'end_ip': self.dhcp_end_ip.get(),
                'subnet_mask': self.subnet_mask.get(),
                'gateway': self.gateway_entry.get(),
                'dns_servers': ['8.8.8.8', '8.8.4.4'],
                'boot_file': 'pxelinux.0',
                'lease_time': 3600
            },
            'tftp': {
                'enabled': self.tftp_enabled.get(),
                'interface': '0.0.0.0',
                'port': 69,
                'root_dir': './tftpboot'
            },
            'http': {
                'enabled': self.http_enabled.get(),
                'interface': '0.0.0.0',
                'port': int(self.http_port.get()),
                'root_dir': './httpboot'
            },
            'log_level': 'INFO'
        }
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("成功", "✅ 配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def _start_server(self):
        """启动服务器"""
        if not check_admin_privileges():
            messagebox.showwarning(
                "权限警告",
                "⚠️ 建议以管理员/root权限运行，否则可能无法绑定低端口"
            )
        
        if self.running:
            return
        
        try:
            self._save_config()
            
            self.pxe = SuperPXE('config.json')
            self.running = True
            
            self.pxe_thread = threading.Thread(target=self._run_server, daemon=True)
            self.pxe_thread.start()
            
            self.start_button.config(state=tk.DISABLED, bg=ModernGUI.COLORS['gray'])
            self.stop_button.config(state=tk.NORMAL, bg=ModernGUI.COLORS['danger'])
            self.status_label.config(text="✅ 状态: 运行中", fg=ModernGUI.COLORS['success'])
            
            self._update_service_labels(self.pxe.config, running=True)
            
        except Exception as e:
            messagebox.showerror("错误", f"启动服务器失败: {e}")
            self.running = False
    
    def _run_server(self):
        """运行服务器"""
        try:
            self.pxe.start()
        except Exception as e:
            logging.getLogger('SuperPXE').error(f"服务器出错: {e}")
    
    def _stop_server(self):
        """停止服务器"""
        if not self.running:
            return
        
        try:
            if self.pxe:
                self.pxe.stop()
                self.pxe = None
            
            self.running = False
            self.start_button.config(state=tk.NORMAL, bg=ModernGUI.COLORS['success'])
            self.stop_button.config(state=tk.DISABLED, bg=ModernGUI.COLORS['gray'])
            self.status_label.config(text="⏸️ 状态: 已停止", fg=ModernGUI.COLORS['gray'])
            
            self._update_service_labels({}, running=False)
            
        except Exception as e:
            messagebox.showerror("错误", f"停止服务器失败: {e}")
    
    def _update_service_labels(self, config, running=False):
        """更新服务状态"""
        services = ['dhcp', 'tftp', 'http']
        service_colors = {
            'dhcp': ('🌐', ModernGUI.COLORS['primary']),
            'tftp': ('📁', '#FF5722'),
            'http': ('🌍', '#9C27B0')
        }
        
        for service in services:
            enabled = config.get(service, {}).get('enabled', False)
            indicator = self.service_indicators[service]
            label = self.service_labels[service]
            
            if enabled and running:
                indicator.config(text="🟢")
                label.config(text="运行中", fg=ModernGUI.COLORS['success'])
            elif enabled:
                indicator.config(text="🔵")
                label.config(text="已启用", fg=ModernGUI.COLORS['primary'])
            else:
                indicator.config(text="⚪")
                label.config(text="已禁用", fg=ModernGUI.COLORS['gray'])
    
    def _refresh_menus(self):
        """刷新菜单"""
        menus = self.boot_manager.list_menus()
        self.menu_combo['values'] = menus
        
        if menus:
            default_menu = self.boot_manager.config['default_menu']
            if default_menu in menus:
                self.menu_var.set(default_menu)
            else:
                self.menu_var.set(menus[0])
            self._refresh_boot_entries()
    
    def _on_menu_changed(self, event):
        """菜单改变"""
        self._refresh_boot_entries()
    
    def _refresh_boot_entries(self):
        """刷新启动项"""
        for item in self.boot_tree.get_children():
            self.boot_tree.delete(item)
        
        menu_name = self.menu_var.get()
        if not menu_name:
            return
        
        entries = self.boot_manager.list_entries(menu_name)
        for entry in entries:
            self.boot_tree.insert('', tk.END, values=(entry['name'], entry['type']))
    
    def _add_boot_entry(self):
        """添加启动项"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加启动项")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=ModernGUI.COLORS['bg_color'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="➕ 添加启动项", font=ModernGUI.FONTS['heading'],
                bg=ModernGUI.COLORS['bg_color']).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        tk.Label(frame, text="名称:", font=ModernGUI.FONTS['body'], bg=ModernGUI.COLORS['bg_color']).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(frame, width=35)
        name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        tk.Label(frame, text="类型:", font=ModernGUI.FONTS['body'], bg=ModernGUI.COLORS['bg_color']).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        type_var = tk.StringVar(value="local")
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=["local", "linux", "iso"], state='readonly', width=33)
        type_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        tk.Label(frame, text="内核文件:", font=ModernGUI.FONTS['body'], bg=ModernGUI.COLORS['bg_color']).grid(
            row=3, column=0, sticky=tk.W, pady=5)
        kernel_entry = ttk.Entry(frame, width=35)
        kernel_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        tk.Label(frame, text="Initrd文件:", font=ModernGUI.FONTS['body'], bg=ModernGUI.COLORS['bg_color']).grid(
            row=4, column=0, sticky=tk.W, pady=5)
        initrd_entry = ttk.Entry(frame, width=35)
        initrd_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        tk.Label(frame, text="内核参数:", font=ModernGUI.FONTS['body'], bg=ModernGUI.COLORS['bg_color']).grid(
            row=5, column=0, sticky=tk.W, pady=5)
        append_entry = ttk.Entry(frame, width=35)
        append_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        tk.Label(frame, text="ISO路径:", font=ModernGUI.FONTS['body'], bg=ModernGUI.COLORS['bg_color']).grid(
            row=6, column=0, sticky=tk.W, pady=5)
        iso_entry = ttk.Entry(frame, width=35)
        iso_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        def on_ok():
            name = name_entry.get().strip()
            type_ = type_var.get()
            if not name:
                messagebox.showwarning("警告", "请输入名称")
                return
            
            kwargs = {}
            if type_ == "linux":
                if kernel_entry.get():
                    kwargs['kernel'] = kernel_entry.get()
                if initrd_entry.get():
                    kwargs['initrd'] = initrd_entry.get()
                if append_entry.get():
                    kwargs['append'] = append_entry.get()
            elif type_ == "iso":
                if iso_entry.get():
                    kwargs['iso_path'] = iso_entry.get()
            
            menu_name = self.menu_var.get()
            if self.boot_manager.add_boot_entry(menu_name, name, type_, **kwargs):
                messagebox.showinfo("成功", "✅ 启动项已添加")
                self._refresh_boot_entries()
                dialog.destroy()
            else:
                messagebox.showerror("错误", "添加失败")
        
        button_frame = tk.Frame(frame, bg=ModernGUI.COLORS['bg_color'])
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="✅ 确定", command=on_ok, font=ModernGUI.FONTS['body'],
                 bg=ModernGUI.COLORS['success'], fg=ModernGUI.COLORS['white'],
                 relief=tk.RAISED, padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="❌ 取消", command=dialog.destroy, font=ModernGUI.FONTS['body'],
                 bg=ModernGUI.COLORS['gray'], fg=ModernGUI.COLORS['white'],
                 relief=tk.RAISED, padx=20, pady=6, cursor='hand2').pack(side=tk.LEFT)
        
        frame.columnconfigure(1, weight=1)
    
    def _remove_boot_entry(self):
        """删除启动项"""
        selected = self.boot_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的启动项")
            return
        
        item = self.boot_tree.item(selected[0])
        name = item['values'][0]
        
        if messagebox.askyesno("确认", f"确定要删除启动项 \"{name}\" 吗？"):
            menu_name = self.menu_var.get()
            if self.boot_manager.remove_boot_entry(menu_name, name):
                messagebox.showinfo("成功", "✅ 启动项已删除")
                self._refresh_boot_entries()
            else:
                messagebox.showerror("错误", "删除失败")


def main():
    """启动GUI"""
    root = tk.Tk()
    
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    app = MainWindow(root)
    root.mainloop()


if __name__ == '__main__':
    main()
