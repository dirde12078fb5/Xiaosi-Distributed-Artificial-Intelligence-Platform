#  Copyright (c) 2025. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
#  Morbi non lorem porttitor neque feugiat blandit. Ut vitae ipsum eget quam lacinia accumsan.
#  Etiam sed turpis ac ipsum condimentum fringilla. Maecenas magna.
#  Proin dapibus sapien vel ante. Aliquam erat volutpat. Pellentesque sagittis ligula eget metus.
#  Vestibulum commodo. Ut rhoncus gravida arcu.

import ctypes
import os
import platform
import queue
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog

import cpuinfo
import requests
from future.moves.tkinter import scrolledtext

# 隐藏终端窗口
if os.name == "nt":  # 仅在Windows系统上隐藏终端
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


def launch_main():
    """ 启动主程序 """
    try:
        subprocess.Popen("../../../config/Cherry-Studio-1.1.17-portable.exe")
    except Exception as e:
        messagebox.showerror("错误", f"启动失败: {str(e)}")


def open_nxshell():
    """ 启动Nxshell """
    exe_path = "../../../config/NxShell/NxShell.exe"
    try:
        subprocess.Popen(exe_path)
    except Exception as e:
        messagebox.showerror("错误", f"启动失败: {str(e)}")


class MainApplication(tk.Tk):
    WINDOW_SIZE = (500, 350)
    MAX_CHECK_FREQ = 5

    def __init__(self):
        super().__init__()
        self.report_issue = None
        self.stop_flag = False
        self.title("小思分布式人工智能 ™10S")
        icon_path = '../../../config/xiaosi.ico'
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        self.geometry("670x400")
        self.configure(bg="#878787")
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # 创建主容器
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=1, fill='both')

        # 初始化各功能模块
        self.setup_hardware_tab()
        self.setup_core_tab()
        self.setup_download_tab()

    def setup_hardware_tab(self):
        """ 硬件加速模块 """
        frame = ttk.Frame(self.notebook, style="Tab.TFrame")
        self.notebook.add(frame, text="硬件加速")

        # GPU 选择
        self.gpu_type = tk.StringVar(value="0")
        ttk.Radiobutton(frame, text="独立显卡", variable=self.gpu_type, value="0", style="Tab.TRadiobutton").grid(
            row=0, column=0, padx=10, pady=5)
        ttk.Radiobutton(frame, text="集成显卡", variable=self.gpu_type, value="1", style="Tab.TRadiobutton").grid(
            row=0, column=1, padx=10, pady=5)

        # 信息展示区
        self.info_text = tk.Text(frame, height=15, wrap=tk.WORD, bg="#FFFFFF", fg="#333333")
        self.info_text.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        # 检测按钮
        ttk.Button(frame, text="检测硬件", command=self.check_hardware, style="Tab.TButton").grid(
            row=2, column=0, columnspan=2, pady=10)

    def check_hardware(self):
        """ 硬件检测逻辑 """
        self.info_text.delete(1.0, tk.END)

        if self.gpu_type.get() == "0":
            gpu_info = self.get_gpu_info()
            if gpu_info:
                for info in gpu_info:
                    self.info_text.insert(tk.END,
                                          f"GPU 型号: {info['name']}\n"
                                          f"利用率: {info['utilization']}%\n"
                                          f"温度: {info['temperature']}°C\n\n")
        else:
            cpu_info = self.get_cpu_info()
            if cpu_info:
                logical_cores = os.cpu_count()
                self.info_text.insert(tk.END,
                                      f"CPU 品牌: {cpu_info['brand']}\n"
                                      f"物理核心数: {cpu_info['cores']}\n"
                                      f"逻辑核心数: {logical_cores}\n"
                                      f"频率: {cpu_info['frequency']}\n")

    def get_gpu_info(self):
        """ GPU信息获取 """
        try:
            cmd = 'nvidia-smi.exe' if platform.system() == 'Windows' else 'nvidia-smi'
            result = subprocess.run(
                [cmd, '--query-gpu=utilization.gpu,name,temperature.gpu', '--format=csv,noheader,nounits'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            return self.parse_gpu_info(result.stdout)
        except Exception as e:
            messagebox.showerror("错误", f"获取GPU信息失败: {str(e)}")
            return None

    def parse_gpu_info(self, output):
        """ 解析GPU信息 """
        gpu_info_list = []
        for line in output.strip().split('\n'):
            if line:
                utilization, name, temperature = line.split(', ')
                gpu_info_list.append({
                    'name': name.strip(),
                    'utilization': float(utilization.strip()),
                    'temperature': float(temperature.strip())
                })
        return gpu_info_list

    def get_cpu_info(self):
        """ CPU信息获取 """
        try:
            # 获取CPU信息
            info = cpuinfo.get_cpu_info()
            # 提取所需的CPU信息
            brand = info.get('brand_raw', 'Unknown')
            cores = info.get('count', 'Unknown')
            logical_cores = info.get('logical_cores', 'Unknown')
            frequency = info.get('hz_actual_friendly', 'Unknown')
            # 返回包含CPU信息的字典
            return {
                'brand': brand,
                'cores': cores,
                'logical_cores': logical_cores,
                'frequency': frequency
            }
        except Exception as e:
            # 若获取CPU信息失败，弹出错误提示框
            messagebox.showerror("错误", f"获取CPU信息失败: {str(e)}")
            return None

    def setup_core_tab(self):
        """ 核心功能模块选项卡配置 """
        # 创建选项卡框架并添加到笔记本容器
        frame = ttk.Frame(self.notebook, style="Tab.TFrame")
        self.notebook.add(frame, text="核心功能")

        # 配置框架的网格布局权重（关键修改）
        frame.grid_rowconfigure(0, weight=1)  # 设置行权重，使行可扩展
        frame.grid_columnconfigure(0, weight=1)  # 设置列权重，使列可扩展
        frame.grid_columnconfigure(1, weight=1)  # 第二列同样设置权重

        # 定义功能按钮列表（包含按钮文本和关联操作）
        function_buttons = [
            ("官方主页", self.open_official),  # 跳转至官方网站
            ("技术书籍", self.open_cloud),  # 打开云端技术文档库
            ("Nxshell", open_nxshell),  # 启动Nxshell工具
            ("网络通畅测试", self.open_network),  # 执行网络连通性检测
            ("快速下载", self.fasta),  # 打开快速下载通道
            ("GPU详细信息", self.fasta_gpu),  # 显示GPU详细参数
            ("软件更新", self.open_update),  # 检查并安装软件更新
            ("MC面板", self.open_MC),  # 打开MC管理面板
            ("PING测速", self.open_network_pulls),  # 执行PING网络测速
            ("AMD信息", self.open_AMD),  # 显示AMD硬件信息
            ("网络加速", self.open_openspeedy),
            ("开始使用向导", launch_main)  # 启动初始化向导
        ]

        # 批量创建按钮并布局（使用2列网格布局）
        for index, (button_text, command) in enumerate(function_buttons):
            # 创建带样式的按钮组件
            action_button = ttk.Button(
                frame,
                text=button_text,
                command=command,
                style="Tab.TButton"
            )
            # 网格布局配置（每行2个按钮，间距优化）
            action_button.grid(
                row=index // 2,
                column=index % 2,
                padx=10,
                pady=8,
                ipadx=6,
                ipady=4,
                sticky="nsew"  # 关键修改：按钮撑满单元格
            )

            # 2列网格布局算法：
            # - 行号 = 索引 // 2 （每2个按钮换行）
            # - 列号 = 索引 % 2 （奇偶索引分别在左右列）
            action_button.grid(
                row=index // 2,
                column=index % 2,
                padx=10,  # 水平外边距
                pady=8,  # 垂直外边距
                ipadx=6,  # 水平内边距
                ipady=4,  # 垂直内边距
                sticky="nsew"  # 按钮撑满单元格（东南西北方向扩展）
            )
    def open_openspeedy(self):
        """ 启动网络加速 """
        import os
        import sys

        def launch_lnk(lnk_path):
            # 确保路径存在
            if not os.path.exists(lnk_path):
                print(f"错误: 文件 {lnk_path} 不存在")
                return False

            try:
                # Windows 系统启动方式
                if sys.platform == 'win32':
                    os.startfile(lnk_path)
                    print(f"已启动: {lnk_path}")
                    return True
                else:
                    print("仅支持 Windows 系统")
                    return False
            except Exception as e:
                print(f"启动失败: {e}")
                return False

        # 示例：假设完整路径如下（请根据实际情况修改）
        lnk_path = r"../../../config/openspeedy/open.lnk"  # 使用原始字符串避免转义
        launch_lnk(lnk_path)
    def open_AMD(self):
        """ 检测AMD显卡 """
        import subprocess
        import tkinter as tk
        from tkinter import messagebox, ttk
        import platform

        def detect_amd_gpu():
            try:
                system = platform.system()
                if system == "Linux":
                    result = subprocess.run(['lspci'], capture_output=True, text=True)
                    output = result.stdout
                elif system == "Windows":
                    result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'Name'],
                                            capture_output=True,
                                            text=True)
                    output = result.stdout
                else:
                    return False

                return 'AMD' in output or 'Advanced Micro Devices' in output
            except Exception as e:
                print(f"检测时出现错误: {e}")
                return False

        def check_gpu():
            result = detect_amd_gpu()
            if result:
                messagebox.showinfo("检测结果", "检测到 AMD 显卡。")
                result_label.config(text="检测结果: 已检测到AMD显卡", foreground="green")
            else:
                messagebox.showinfo("检测结果", "未检测到 AMD 显卡。")
                result_label.config(text="检测结果: 未检测到AMD显卡", foreground="red")

        def get_system_info():
            return {
                "操作系统": f"{platform.system()} {platform.release()}",
                "处理器": self.get_cpu_info(),  # 保持对实例方法的调用
                "Python版本": platform.python_version()
            }

        def display_system_info():
            info = get_system_info()
            for i, (key, value) in enumerate(info.items()):
                ttk.Label(info_frame, text=f"{key}:", font=("Arial", 10)).grid(row=i, column=0, sticky="w", padx=10,
                                                                               pady=5)
                ttk.Label(info_frame, text=value, font=("Arial", 10)).grid(row=i, column=1, sticky="w", padx=10, pady=5)

        root = tk.Tk()
        root.title("AMD显卡检测工具")
        root.iconbitmap('config/xiaosi.ico')
        root.geometry("900x500")  # 窗口大小设置为600x400像素

        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="AMD显卡检测工具", font=("Arial", 16, "bold"))
        title_label.pack(pady=15)

        # 检测按钮
        check_button = ttk.Button(main_frame, text="检测AMD显卡", command=check_gpu, style='Accent.TButton')
        check_button.pack(pady=20)

        # 结果标签
        result_label = ttk.Label(main_frame, text="等待检测...", font=("Arial", 12))
        result_label.pack(pady=10)

        # 系统信息框架
        info_frame = ttk.LabelFrame(main_frame, text="系统信息", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # 显示系统信息
        display_system_info()

        # 底部状态栏
        status_bar = ttk.Label(root, text="准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 应用样式
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 12), padding=10)

        root.mainloop()
    def open_official(self):
        """ 打开官网 """
        webbrowser.open("http://xiao-si.icu")

    def fasta_gpu(self):
        """ GPU """
        import tkinter as tk
        from tkinter import messagebox
        import pynvml
        import os

        def print_nvidia_gpu_info():
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                info_text = ""
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    total_memory = memory_info.total / 1024 ** 2
                    used_memory = memory_info.used / 1024 ** 2
                    free_memory = memory_info.free / 1024 ** 2

                    info_text += f"GPU {i}:\n"
                    info_text += f"  名称: {name}\n"
                    info_text += f"  温度: {temperature} °C\n"
                    info_text += f"  使用率: {utilization}%\n"
                    info_text += f"  总显存: {total_memory:.2f} MB\n"
                    info_text += f"  已使用显存: {used_memory:.2f} MB\n"
                    info_text += f"  空闲显存: {free_memory:.2f} MB\n\n"

                pynvml.nvmlShutdown()
                return info_text
            except pynvml.NVMLError as e:
                messagebox.showerror("错误", f"NVML 错误: {e}")
                return None

        def show_gpu_info():
            info = print_nvidia_gpu_info()
            if info:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, info)

        def about():
            messagebox.showinfo("关于", "这是一个 GPU 检测的嵌入式 GUI 程序。")

        root = tk.Tk()
        root.title("嵌入式 GPU 信息检测程序")

        # 创建菜单栏
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=root.quit)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=about)

        # 创建主框架
        main_frame = tk.Frame(root)
        main_frame.pack(pady=20)

        # 添加图标
        icon_path = '../../../config/xiaosi.ico'
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)

        # 创建按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)

        button = tk.Button(button_frame, text="检测 GPU 信息", command=show_gpu_info)
        button.pack(side=tk.LEFT, padx=10)

        # 创建结果显示框架
        result_frame = tk.Frame(main_frame)
        result_frame.pack(pady=10)

        result_text = tk.Text(result_frame, height=20, width=50)
        result_text.pack()

        root.mainloop()

    def open_update(self):
        """ 更新软件 """
        webbrowser.open("https://xiao-si.icu:40069/apps/dashboard/")

    def open_network_pulls(self):
        webbrowser.open("https://www.speedtest.cn/")

    def fasta(self):
        """ 快速下载 """
        try:
            subprocess.Popen("../../../config/NM/NeatDM.exe")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")

    def open_cloud(self):
        """ 技术书籍 """
        webbrowser.open('http://xiao-si.icu')

    def open_MC(self):
        """ MC面板 """
        try:
            subprocess.Popen("../../../config/MC/X Minecraft Launcher.exe")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")

    def open_network(self):
        """ 网络ping工具 """
        PingGUI(tk.Toplevel(self))

    def setup_download_tab(self):
        """ 下载工具模块 """
        frame = ttk.Frame(self.notebook, style="Tab.TFrame")
        self.notebook.add(frame, text="下载工具")

        # URL输入
        ttk.Label(frame, text="下载URL:", style="Tab.TLabel").grid(row=0, column=0, padx=5, pady=5)
        self.url_entry = ttk.Entry(frame, width=50, style="Tab.TEntry")
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        # 路径选择
        ttk.Button(frame, text="选择路径", command=self.select_path, style="Tab.TButton").grid(row=1, column=0, padx=5, pady=5)
        self.path_label = ttk.Label(frame, text="<======  请选择保存路径", style="Tab.TLabel")
        self.path_label.grid(row=1, column=1, padx=5, pady=5)

        # 进度条
        self.progress = ttk.Progressbar(frame, orient='horizontal', length=300, mode='determinate',
                                        style="Tab.Horizontal.TProgressbar")
        self.progress.grid(row=2, columnspan=2, pady=10)

        # 下载速度显示
        self.speed_label = ttk.Label(frame, text="速度: 0.00 KB/s", style="Tab.TLabel")
        self.speed_label.grid(row=3, columnspan=2, pady=5)

        # 下载按钮
        self.download_button = ttk.Button(frame, text="开始下载", command=self.start_download, style="Tab.TButton")
        self.download_button.grid(row=4, columnspan=2, pady=5)
        # 停止下载
        self.stop_flag = False  # 添加停止标志
        ttk.Button(frame, text="停止下载", command=self.stop_download, style="Tab.TButton").grid(row=5, columnspan=2, pady=5)

    def stop_download(self):
        """ 停止下载 """
        self.stop_flag = True

    def download_file(self, url, save_path):
        """ 下载文件核心逻辑 """
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            file_name = os.path.basename(url)
            save_path = os.path.join(save_path, file_name)

            self.progress["value"] = 0
            self.progress["maximum"] = total_size

            start_time = time.time()
            downloaded_size = 0

            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_flag:
                        break
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed = downloaded_size / elapsed_time
                            speed_kb = speed / 1024
                            self.speed_label.config(text=f"速度: {speed_kb:.2f} KB/s")
                        self.update_progress(len(chunk))

                        if downloaded_size >= total_size:
                            break

            if self.stop_flag:
                messagebox.showinfo("停止", "下载已停止。")
                if os.path.exists(save_path):
                    os.remove(save_path)
            elif downloaded_size >= total_size:
                messagebox.showinfo("完成", f"文件已保存到: {save_path}")
            else:
                messagebox.showerror("错误", "下载未完成，请检查网络或文件链接。")
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            self.download_button.config(state=tk.NORMAL)
            self.stop_flag = False

    def select_path(self):
        """ 选择保存路径 """
        path = filedialog.askdirectory()
        if path:
            self.path_label.config(text=path)

    def start_download(self):
        """ 启动下载线程 """
        url = self.url_entry.get()
        save_path = self.path_label.cget("text")

        if not url.startswith('http'):
            messagebox.showerror("错误", "无效的URL地址")
            return

        # 禁用下载按钮
        self.download_button.config(state=tk.DISABLED)

        threading.Thread(
            target=self.download_file,
            args=(url, save_path),
            daemon=True
        ).start()

    def update_progress(self, chunk_size):
        """ 更新进度条 """
        current_value = self.progress["value"] + chunk_size
        total_value = self.progress["maximum"]
        if current_value < total_value * 0.3:
            color = "red"
        elif current_value < total_value * 0.7:
            color = "yellow"
        else:
            color = "green"

        style = ttk.Style()
        style.configure("Tab.Horizontal.TProgressbar", troughcolor="white", background=color)
        self.progress.step(chunk_size)

    def on_close(self):
        """
        关闭窗口事件
        当用户尝试关闭窗口时，弹出确认对话框询问用户是否确定退出程序。
        如果用户确认，则销毁窗口并退出程序。
        """
        if messagebox.askokcancel("退出", "确定要退出 小思分布式人工智能 ™  10 程序吗？"):
            self.destroy()
            sys.exit()


class PingGUI:
    """增强版网络诊断工具"""
    MAX_LOG_LINES = 1500  # 日志最大行数
    UPDATE_INTERVAL = 0.1  # 界面更新间隔(秒)
    BATCH_SIZE = 15  # 批量更新条数

    def __init__(self, master):
        self.master = master
        master.title("Ping工具 V 3.0")
        self.update_queue = queue.Queue()
        self.is_running = False
        self.process = None
        self._icon_cache = {}

        # 初始化界面
        self.set_window_icon()
        self.create_widgets()
        self.configure_window()
        self.setup_platform_specific()
        master.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_platform_specific(self):
        """平台相关设置"""
        if os.name == 'nt':
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
            self.master.iconbitmap(default='config/xiaosi.ico')

    def configure_window(self):
        """窗口配置"""
        width, height = 720, 480
        self.master.geometry(f"{width}x{height}")
        self.center_window(width, height)
        self.master.minsize(600, 400)

    def center_window(self, width, height):
        """窗口居中"""
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.master.geometry(f"+{x}+{y}")

    def set_window_icon(self):
        """智能图标加载"""
        icon_paths = [
            'xiaosi.ico',
            'ping.png',
            '/usr/share/pixmaps/ping.xpm'
        ]

        for path in icon_paths:
            if os.path.exists(path):
                try:
                    if path not in self._icon_cache:
                        if platform.system() == 'Windows':
                            self._icon_cache[path] = path
                        else:
                            self._icon_cache[path] = tk.PhotoImage(file=path)

                    if platform.system() == 'Windows':
                        self.master.iconbitmap(self._icon_cache[path])
                    else:
                        self.master.tk.call('wm', 'iconphoto', self.master._w, self._icon_cache[path])
                    break
                except Exception as e:
                    print(f"Icon load warning: {str(e)}")

    def create_widgets(self):
        """构建界面组件"""
        main_frame = ttk.Frame(self.master)
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        # 输入控制区
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=5)

        ttk.Label(control_frame, text="目标地址:").pack(side='left')
        self.target_entry = ttk.Entry(control_frame, width=35)
        self.target_entry.pack(side='left', padx=5)

        ttk.Label(control_frame, text="次数:").pack(side='left', padx=5)
        self.count_var = tk.IntVar(value=4)
        ttk.Spinbox(control_frame, from_=1, to=999,
                    textvariable=self.count_var, width=5).pack(side='left')

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side='right')

        self.ping_button = ttk.Button(btn_frame, text="开始检测",
                                      command=self.start_ping_thread)
        self.ping_button.pack(side='left', padx=2)

        ttk.Button(btn_frame, text="清空日志",
                   command=self.clear_output).pack(side='left', padx=2)

        # 结果显示区
        self.result_area = scrolledtext.ScrolledText(main_frame,
                                                    wrap=tk.WORD,
                                                    font=('Consolas', 9),
                                                    tabs=('0.5c', '2c'),
                                                    spacing3=2)
        self.result_area.pack(expand=True, fill='both')

        # 状态栏
        self.status_bar = ttk.Label(main_frame,
                                    text="就绪",
                                    relief='sunken')
        self.status_bar.pack(fill='x', pady=(5, 0))

        # 快捷键绑定
        self.master.bind("<Control-l>", lambda e: self.clear_output())
        self.master.bind("<Return>", lambda e: self.start_ping_thread())

    def start_ping_thread(self):
        """启动检测线程"""
        if self.is_running:
            messagebox.showwarning("操作冲突", "当前有正在进行的检测任务")
            return

        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("输入错误", "请输入有效的检测地址")
            return

        # DNS预解析
        try:
            socket.gethostbyname(target)
        except socket.gaierror:
            messagebox.showerror("解析错误", "无法解析目标地址")
            return

        try:
            count = self.count_var.get()
            if not 1 <= count <= 999:
                raise ValueError
        except:
            messagebox.showerror("参数错误", "检测次数应为1-999之间的整数")
            return

        self.ping_button.config(state='disabled')
        self.is_running = True
        threading.Thread(
            target=self.do_ping,
            args=(target, count),
            daemon=True
        ).start()
        threading.Thread(
            target=self.output_handler,
            daemon=True
        ).start()

    def do_ping(self, target, count):
        try:
            timeout = 5
            # 根据系统类型选择编码
            encoding = 'gbk' if platform.system() == 'Windows' else 'utf-8'

            if platform.system().lower() == 'windows':
                command = ['ping', '-n', str(count), '-w', str(timeout * 1000), target]
            else:
                command = ['ping', '-c', str(count), '-W', str(timeout), target]

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=encoding,
                errors='replace',
                bufsize=1
            )

            with self.process:
                for line in iter(self.process.stdout.readline, ''):
                    if not self.is_running:
                        break
                    cleaned_line = line.replace('?', ' ').replace('?', '>')
                    self.update_queue.put(cleaned_line.strip())

            self.update_queue.put(None)
            self.update_status("检测完成")

        except subprocess.CalledProcessError as e:
            self.update_queue.put(f"命令执行失败: {e.stderr}")
        except PermissionError:
            self.update_queue.put("权限不足，请以管理员身份运行")
        except Exception as e:
            self.update_queue.put(f"未捕获异常: {str(e)}")
        finally:
            self.is_running = False
            self.process = None
            self.master.after(100, lambda: self.ping_button.config(state='normal'))

    def output_handler(self):
        """异步输出处理器"""
        buffer = []
        last_update = time.time()
        while self.is_running or not self.update_queue.empty():
            try:
                item = self.update_queue.get_nowait()
                if item is None:
                    break
                buffer.append(item)

                if (time.time() - last_update > self.UPDATE_INTERVAL or
                        len(buffer) >= self.BATCH_SIZE):
                    self._update_display('\n'.join(buffer))
                    buffer = []
                    last_update = time.time()

            except queue.Empty:
                time.sleep(0.01)

        if buffer:
            self._update_display('\n'.join(buffer))

    def _update_display(self, text):
        """安全更新界面"""
        self.master.after(0, self._safe_display_update, text)

    def _safe_display_update(self, text):
        """带性能优化的显示更新"""
        self.result_area.config(state='normal')

        current_lines = int(self.result_area.index('end-1c').split('.')[0])
        if current_lines > self.MAX_LOG_LINES:
            delete_count = current_lines - self.MAX_LOG_LINES
            self.result_area.delete(1.0, f"{delete_count + 1}.0")

        self.result_area.insert(tk.END, text + '\n')
        self.result_area.see(tk.END)
        self.result_area.config(state='disabled')

    def update_status(self, message):
        """更新状态栏"""
        self.master.after(0, lambda: self.status_bar.config(
            text=f"{time.strftime('%H:%M:%S')} | {message}"))

    def clear_output(self):
        """清空日志"""
        try:
            self.result_area.config(state='normal')
            self.result_area.delete(1.0, tk.END)
            self.result_area.insert(tk.END, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 日志已重置\n")
            self.result_area.see(tk.END)
            self.update_status("日志已清空")
        except Exception as e:
            messagebox.showerror("操作异常", f"清空失败: {str(e)}")
        finally:
            self.result_area.config(state='disabled')

    def on_close(self):
        """安全关闭"""
        if self.is_running:
            if messagebox.askyesno("强制退出", "检测正在进行中，确定要终止吗？"):
                self.is_running = False
                if self.process:
                    self.process.terminate()
                self.master.destroy()
        else:
            self.master.destroy()


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()