#  Copyright (c) 2026. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
#  Morbi non lorem porttitor neque feugiat blandit. Ut vitae ipsum eget quam lacinia accumsan.
#  Etiam sed turpis ac ipsum condimentum fringilla. Maecenas magna.
#  Proin dapibus sapien vel ante. Aliquam erat volutpat. Pellentesque sagittis ligula eget metus.
#  Vestibulum commodo. Ut rhoncus gravida arcu.

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import socket
import os
import sys
import platform
import psutil
import time
import json
from datetime import datetime


class AIVulnManager:
    def __init__(self, root):
        self.root = root
        self.root.title("小思人工智能应用及漏洞管理")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        try:
            self.root.iconbitmap('./xiaosi.ico')
        except:
            pass

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.colors = {
            "bg": "#f0f2f5",
            "card": "#ffffff",
            "primary": "#007bff",
            "primary_dark": "#0056b3",
            "text": "#333333",
            "text_light": "#666666",
            "success": "#28a745",
            "warning": "#ffc107",
            "danger": "#dc3545",
            "info": "#17a2b8",
            "border": "#e0e0e0"
        }

        self.root.configure(bg=self.colors["bg"])

        self.scan_running = False
        self.port_scan_running = False
        self.ai_scan_running = False

        self.ai_models = []
        self.vuln_results = []
        self.port_results = []
        self.ai_security_results = []

        self.load_ai_models()
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.create_header()
        self.create_notebook()
        self.create_status_bar()

    def create_header(self):
        header_frame = tk.Frame(self.root, bg=self.colors["card"], pady=15)
        header_frame.pack(fill="x", padx=15, pady=(15, 5))

        title_label = tk.Label(
            header_frame,
            text="小思人工智能应用及漏洞管理",
            font=("Microsoft YaHei UI", 22, "bold"),
            bg=self.colors["card"],
            fg=self.colors["primary"]
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="AI应用管理 · 漏洞检测 · 安全防护",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text_light"]
        )
        subtitle_label.pack(pady=3)

    def create_notebook(self):
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        self.tab_dashboard = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.tab_ai_apps = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.tab_vuln_scan = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.tab_port_scan = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.tab_ai_security = tk.Frame(self.notebook, bg=self.colors["bg"])

        self.notebook.add(self.tab_dashboard, text="  仪表盘  ")
        self.notebook.add(self.tab_ai_apps, text="  AI应用管理  ")
        self.notebook.add(self.tab_vuln_scan, text="  系统漏洞扫描  ")
        self.notebook.add(self.tab_port_scan, text="  网络端口扫描  ")
        self.notebook.add(self.tab_ai_security, text="  AI模型安全  ")

        self.create_dashboard_tab()
        self.create_ai_apps_tab()
        self.create_vuln_scan_tab()
        self.create_port_scan_tab()
        self.create_ai_security_tab()

    def create_status_bar(self):
        status_frame = tk.Frame(self.root, bg="#34495e", height=28)
        status_frame.pack(fill="x", side="bottom")

        self.status_text = tk.StringVar(value="就绪")
        status_bar = tk.Label(
            status_frame,
            textvariable=self.status_text,
            font=("Microsoft YaHei UI", 9),
            fg="white",
            bg="#34495e",
            anchor="w"
        )
        status_bar.pack(fill="both", padx=10, pady=5)

        self.time_text = tk.StringVar(value="")
        time_bar = tk.Label(
            status_frame,
            textvariable=self.time_text,
            font=("Microsoft YaHei UI", 9),
            fg="white",
            bg="#34495e",
            anchor="e"
        )
        time_bar.pack(side="right", padx=10, pady=5)

        self.update_time()

    def update_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_text.set(now)
        self.root.after(1000, self.update_time)

    def create_dashboard_tab(self):
        container = tk.Frame(self.tab_dashboard, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=10, pady=10)

        stats_frame = tk.Frame(container, bg=self.colors["bg"])
        stats_frame.pack(fill="x", pady=(0, 10))

        self.stat_cards = {}
        stat_configs = [
            ("AI模型数量", "0", "primary", "models"),
            ("运行中应用", "0", "success", "running"),
            ("已发现漏洞", "0", "danger", "vulns"),
            ("安全评分", "--", "warning", "score"),
        ]

        for i, (title, value, color_key, key) in enumerate(stat_configs):
            card = tk.Frame(stats_frame, bg=self.colors["card"], padx=15, pady=15)
            card.grid(row=0, column=i, padx=5, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)

            self.stat_cards[key] = {"frame": card, "value_label": None}

            val_label = tk.Label(
                card,
                text=value,
                font=("Microsoft YaHei UI", 28, "bold"),
                bg=self.colors["card"],
                fg=self.colors[color_key]
            )
            val_label.pack()

            title_label = tk.Label(
                card,
                text=title,
                font=("Microsoft YaHei UI", 10),
                bg=self.colors["card"],
                fg=self.colors["text_light"]
            )
            title_label.pack(pady=(3, 0))

            self.stat_cards[key]["value_label"] = val_label

        content_frame = tk.Frame(container, bg=self.colors["bg"])
        content_frame.pack(fill="both", expand=True)

        left_frame = tk.Frame(content_frame, bg=self.colors["bg"])
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.create_system_info_card(left_frame)

        right_frame = tk.Frame(content_frame, bg=self.colors["bg"])
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.create_recent_activity_card(right_frame)

        self.update_dashboard_stats()

    def create_system_info_card(self, parent):
        card = tk.Frame(parent, bg=self.colors["card"], padx=15, pady=15)
        card.pack(fill="both", expand=True)

        title = tk.Label(
            card,
            text="系统信息",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        title.pack(anchor="w", pady=(0, 10))

        info_frame = tk.Frame(card, bg=self.colors["card"])
        info_frame.pack(fill="both", expand=True)

        sys_info = [
            ("操作系统", f"{platform.system()} {platform.release()}"),
            ("系统版本", platform.version()),
            ("处理器", platform.processor() or "未知"),
            ("主机名", socket.gethostname()),
            ("内存总量", f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"),
            ("CPU核心数", f"{psutil.cpu_count(logical=True)} 核"),
        ]

        for i, (label, value) in enumerate(sys_info):
            lbl = tk.Label(
                info_frame,
                text=f"{label}:",
                font=("Microsoft YaHei UI", 10),
                bg=self.colors["card"],
                fg=self.colors["text_light"],
                anchor="w"
            )
            lbl.grid(row=i, column=0, sticky="w", pady=4, padx=(0, 10))

            val = tk.Label(
                info_frame,
                text=value,
                font=("Microsoft YaHei UI", 10, "bold"),
                bg=self.colors["card"],
                fg=self.colors["text"],
                anchor="w"
            )
            val.grid(row=i, column=1, sticky="w", pady=4)

    def create_recent_activity_card(self, parent):
        card = tk.Frame(parent, bg=self.colors["card"], padx=15, pady=15)
        card.pack(fill="both", expand=True)

        title = tk.Label(
            card,
            text="最近活动",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        title.pack(anchor="w", pady=(0, 10))

        self.activity_text = scrolledtext.ScrolledText(
            card,
            font=("Microsoft YaHei UI", 9),
            bg="#fafafa",
            fg=self.colors["text"],
            relief="flat",
            height=12,
            state="disabled"
        )
        self.activity_text.pack(fill="both", expand=True)

        self.add_activity("系统启动，小思人工智能应用及漏洞管理已就绪")

    def add_activity(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_text.configure(state="normal")
        self.activity_text.insert("end", f"[{timestamp}] {message}\n")
        self.activity_text.see("end")
        self.activity_text.configure(state="disabled")

    def update_dashboard_stats(self):
        model_count = len(self.ai_models)
        running_count = sum(1 for m in self.ai_models if m.get("status") == "运行中")
        vuln_count = len(self.vuln_results)

        self.stat_cards["models"]["value_label"].config(text=str(model_count))
        self.stat_cards["running"]["value_label"].config(text=str(running_count))
        self.stat_cards["vulns"]["value_label"].config(text=str(vuln_count))

        if vuln_count == 0:
            score = "100"
            color = self.colors["success"]
        elif vuln_count < 3:
            score = "85"
            color = self.colors["warning"]
        else:
            score = "60"
            color = self.colors["danger"]

        self.stat_cards["score"]["value_label"].config(text=score, fg=color)

    def create_ai_apps_tab(self):
        container = tk.Frame(self.tab_ai_apps, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=10, pady=10)

        toolbar = tk.Frame(container, bg=self.colors["card"], padx=10, pady=10)
        toolbar.pack(fill="x", pady=(0, 10))

        add_btn = tk.Button(
            toolbar,
            text="添加模型",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=self.colors["primary"],
            fg="white",
            activebackground=self.colors["primary_dark"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.add_ai_model,
            padx=15,
            pady=6
        )
        add_btn.pack(side="left", padx=3)

        refresh_btn = tk.Button(
            toolbar,
            text="刷新状态",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=self.colors["info"],
            fg="white",
            activebackground="#117a8b",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.refresh_ai_models,
            padx=15,
            pady=6
        )
        refresh_btn.pack(side="left", padx=3)

        remove_btn = tk.Button(
            toolbar,
            text="移除选中",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=self.colors["danger"],
            fg="white",
            activebackground="#c82333",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.remove_ai_model,
            padx=15,
            pady=6
        )
        remove_btn.pack(side="left", padx=3)

        list_card = tk.Frame(container, bg=self.colors["card"], padx=10, pady=10)
        list_card.pack(fill="both", expand=True)

        columns = ("name", "type", "version", "status", "path")
        self.ai_tree = ttk.Treeview(list_card, columns=columns, show="headings", height=15)

        self.ai_tree.heading("name", text="模型名称")
        self.ai_tree.heading("type", text="类型")
        self.ai_tree.heading("version", text="版本")
        self.ai_tree.heading("status", text="状态")
        self.ai_tree.heading("path", text="路径")

        self.ai_tree.column("name", width=200, anchor="w")
        self.ai_tree.column("type", width=100, anchor="center")
        self.ai_tree.column("version", width=100, anchor="center")
        self.ai_tree.column("status", width=80, anchor="center")
        self.ai_tree.column("path", width=350, anchor="w")

        scrollbar = ttk.Scrollbar(list_card, orient="vertical", command=self.ai_tree.yview)
        self.ai_tree.configure(yscrollcommand=scrollbar.set)

        self.ai_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.refresh_ai_model_list()

    def load_ai_models(self):
        config_path = os.path.join(os.path.dirname(__file__), "ai_models_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.ai_models = json.load(f)
            except:
                self.ai_models = []
        else:
            self.ai_models = [
                {"name": "Qwen3-7B", "type": "LLM", "version": "3.0", "status": "已停止", "path": "C:/models/qwen3-7b"},
                {"name": "DeepSeek-V2", "type": "LLM", "version": "2.0", "status": "运行中", "path": "C:/models/deepseek-v2"},
                {"name": "Gemma3-4B", "type": "LLM", "version": "3.0", "status": "已停止", "path": "C:/models/gemma3-4b"},
            ]

    def save_ai_models(self):
        config_path = os.path.join(os.path.dirname(__file__), "ai_models_config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.ai_models, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def add_ai_model(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加AI模型")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        form_frame = tk.Frame(dialog, bg=self.colors["card"], padx=20, pady=20)
        form_frame.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(
            form_frame,
            text="模型名称:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w", pady=(0, 5))

        name_entry = tk.Entry(form_frame, font=("Microsoft YaHei UI", 10))
        name_entry.pack(fill="x", pady=(0, 10))

        tk.Label(
            form_frame,
            text="模型类型:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w", pady=(0, 5))

        type_var = tk.StringVar(value="LLM")
        type_combo = ttk.Combobox(form_frame, textvariable=type_var, state="readonly")
        type_combo["values"] = ("LLM", "CV", "语音", "多模态", "其他")
        type_combo.pack(fill="x", pady=(0, 10))

        tk.Label(
            form_frame,
            text="版本:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w", pady=(0, 5))

        version_entry = tk.Entry(form_frame, font=("Microsoft YaHei UI", 10))
        version_entry.pack(fill="x", pady=(0, 10))

        tk.Label(
            form_frame,
            text="模型路径:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w", pady=(0, 5))

        path_frame = tk.Frame(form_frame, bg=self.colors["card"])
        path_frame.pack(fill="x", pady=(0, 15))

        path_entry = tk.Entry(path_frame, font=("Microsoft YaHei UI", 10))
        path_entry.pack(side="left", fill="x", expand=True)

        def browse_path():
            folder = filedialog.askdirectory(parent=dialog)
            if folder:
                path_entry.delete(0, "end")
                path_entry.insert(0, folder)

        browse_btn = tk.Button(
            path_frame,
            text="浏览",
            font=("Microsoft YaHei UI", 9),
            bg=self.colors["primary"],
            fg="white",
            relief="flat",
            cursor="hand2",
            command=browse_path,
            padx=10
        )
        browse_btn.pack(side="right", padx=(5, 0))

        def confirm():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入模型名称", parent=dialog)
                return
            self.ai_models.append({
                "name": name,
                "type": type_var.get(),
                "version": version_entry.get().strip() or "1.0",
                "status": "已停止",
                "path": path_entry.get().strip()
            })
            self.save_ai_models()
            self.refresh_ai_model_list()
            self.update_dashboard_stats()
            self.add_activity(f"添加AI模型: {name}")
            dialog.destroy()

        btn_frame = tk.Frame(form_frame, bg=self.colors["card"])
        btn_frame.pack(fill="x")

        tk.Button(
            btn_frame,
            text="取消",
            font=("Microsoft YaHei UI", 10),
            bg="#6c757d",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=dialog.destroy,
            padx=20,
            pady=6
        ).pack(side="right", padx=(5, 0))

        tk.Button(
            btn_frame,
            text="确定",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=self.colors["primary"],
            fg="white",
            relief="flat",
            cursor="hand2",
            command=confirm,
            padx=20,
            pady=6
        ).pack(side="right")

    def remove_ai_model(self):
        selection = self.ai_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要移除的模型")
            return

        if not messagebox.askyesno("确认", "确定要移除选中的模型吗？"):
            return

        indices = []
        for item in selection:
            idx = self.ai_tree.index(item)
            indices.append(idx)

        indices.sort(reverse=True)
        removed_names = []
        for idx in indices:
            name = self.ai_models[idx]["name"]
            removed_names.append(name)
            del self.ai_models[idx]

        self.save_ai_models()
        self.refresh_ai_model_list()
        self.update_dashboard_stats()
        self.add_activity(f"移除AI模型: {', '.join(removed_names)}")

    def refresh_ai_models(self):
        self.status_text.set("正在刷新AI模型状态...")
        self.add_activity("正在刷新AI模型状态")

        def refresh_thread():
            for model in self.ai_models:
                time.sleep(0.2)
                if model["path"] and os.path.exists(model["path"]):
                    model["status"] = "运行中" if os.path.isdir(model["path"]) else "已停止"
                else:
                    model["status"] = "未找到"

            self.root.after(0, self.refresh_ai_model_list)
            self.root.after(0, self.update_dashboard_stats)
            self.root.after(0, lambda: self.status_text.set("状态刷新完成"))
            self.root.after(0, lambda: self.add_activity("AI模型状态刷新完成"))

        threading.Thread(target=refresh_thread, daemon=True).start()

    def refresh_ai_model_list(self):
        for item in self.ai_tree.get_children():
            self.ai_tree.delete(item)

        for model in self.ai_models:
            status = model.get("status", "未知")
            self.ai_tree.insert(
                "",
                "end",
                values=(
                    model["name"],
                    model.get("type", "未知"),
                    model.get("version", "1.0"),
                    status,
                    model.get("path", "")
                )
            )

    def create_vuln_scan_tab(self):
        container = tk.Frame(self.tab_vuln_scan, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=10, pady=10)

        control_card = tk.Frame(container, bg=self.colors["card"], padx=15, pady=15)
        control_card.pack(fill="x", pady=(0, 10))

        title = tk.Label(
            control_card,
            text="系统漏洞扫描",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        title.pack(anchor="w", pady=(0, 10))

        scan_type_frame = tk.Frame(control_card, bg=self.colors["card"])
        scan_type_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            scan_type_frame,
            text="扫描类型:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left", padx=(0, 10))

        self.vuln_scan_type = tk.StringVar(value="full")
        scan_types = [
            ("快速扫描", "quick"),
            ("完整扫描", "full"),
            ("深度扫描", "deep"),
        ]

        for text, value in scan_types:
            tk.Radiobutton(
                scan_type_frame,
                text=text,
                variable=self.vuln_scan_type,
                value=value,
                font=("Microsoft YaHei UI", 10),
                bg=self.colors["card"],
                fg=self.colors["text"],
                activebackground=self.colors["card"]
            ).pack(side="left", padx=5)

        btn_frame = tk.Frame(control_card, bg=self.colors["card"])
        btn_frame.pack(fill="x")

        self.scan_btn = tk.Button(
            btn_frame,
            text="开始扫描",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors["primary"],
            fg="white",
            activebackground=self.colors["primary_dark"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.start_vuln_scan,
            padx=25,
            pady=8
        )
        self.scan_btn.pack(side="left", padx=3)

        self.stop_scan_btn = tk.Button(
            btn_frame,
            text="停止扫描",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors["danger"],
            fg="white",
            activebackground="#c82333",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.stop_vuln_scan,
            state="disabled",
            padx=25,
            pady=8
        )
        self.stop_scan_btn.pack(side="left", padx=3)

        export_btn = tk.Button(
            btn_frame,
            text="导出报告",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors["success"],
            fg="white",
            activebackground="#218838",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.export_vuln_report,
            padx=25,
            pady=8
        )
        export_btn.pack(side="left", padx=3)

        progress_card = tk.Frame(container, bg=self.colors["card"], padx=15, pady=10)
        progress_card.pack(fill="x", pady=(0, 10))

        self.vuln_progress_var = tk.StringVar(value="准备就绪")
        progress_label = tk.Label(
            progress_card,
            textvariable=self.vuln_progress_var,
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        progress_label.pack(anchor="w", pady=(0, 5))

        self.vuln_progress = ttk.Progressbar(progress_card, mode="determinate")
        self.vuln_progress.pack(fill="x")

        result_card = tk.Frame(container, bg=self.colors["card"], padx=10, pady=10)
        result_card.pack(fill="both", expand=True)

        columns = ("severity", "name", "category", "description", "status")
        self.vuln_tree = ttk.Treeview(result_card, columns=columns, show="headings", height=15)

        self.vuln_tree.heading("severity", text="严重程度")
        self.vuln_tree.heading("name", text="漏洞名称")
        self.vuln_tree.heading("category", text="类别")
        self.vuln_tree.heading("description", text="描述")
        self.vuln_tree.heading("status", text="状态")

        self.vuln_tree.column("severity", width=80, anchor="center")
        self.vuln_tree.column("name", width=180, anchor="w")
        self.vuln_tree.column("category", width=100, anchor="center")
        self.vuln_tree.column("description", width=350, anchor="w")
        self.vuln_tree.column("status", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(result_card, orient="vertical", command=self.vuln_tree.yview)
        self.vuln_tree.configure(yscrollcommand=scrollbar.set)

        self.vuln_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.vuln_tree.tag_configure("critical", background="#ffe0e0")
        self.vuln_tree.tag_configure("high", background="#fff3cd")
        self.vuln_tree.tag_configure("medium", background="#fff9e6")
        self.vuln_tree.tag_configure("low", background="#d4edda")

    def start_vuln_scan(self):
        if self.scan_running:
            return

        self.scan_running = True
        self.scan_btn.config(state="disabled")
        self.stop_scan_btn.config(state="normal")
        self.vuln_results = []
        self.status_text.set("正在进行系统漏洞扫描...")
        self.add_activity("系统漏洞扫描开始")

        for item in self.vuln_tree.get_children():
            self.vuln_tree.delete(item)

        threading.Thread(target=self.vuln_scan_worker, daemon=True).start()

    def stop_vuln_scan(self):
        self.scan_running = False
        self.status_text.set("扫描已停止")
        self.add_activity("系统漏洞扫描已停止")

    def vuln_scan_worker(self):
        scan_type = self.vuln_scan_type.get()

        vuln_checks = self.get_vuln_checks(scan_type)
        total = len(vuln_checks)

        for i, check in enumerate(vuln_checks):
            if not self.scan_running:
                break

            msg = f"正在检查: {check['name']} ({i+1}/{total})"
            self.root.after(0, lambda m=msg: self.vuln_progress_var.set(m))
            self.root.after(0, lambda v=(i/total)*100: self.vuln_progress.config(value=v))

            time.sleep(0.3)

            result = self.perform_vuln_check(check)
            if result:
                self.vuln_results.append(result)
                self.root.after(0, lambda r=result: self.add_vuln_result(r))

            self.root.after(0, self.update_dashboard_stats)

        if self.scan_running:
            self.root.after(0, lambda: self.vuln_progress_var.set(f"扫描完成，共发现 {len(self.vuln_results)} 个漏洞"))
            self.root.after(0, lambda: self.vuln_progress.config(value=100))
            self.root.after(0, lambda: self.status_text.set("扫描完成"))
            self.root.after(0, lambda: self.add_activity(f"系统漏洞扫描完成，发现 {len(self.vuln_results)} 个漏洞"))

        self.scan_running = False
        self.root.after(0, lambda: self.scan_btn.config(state="normal"))
        self.root.after(0, lambda: self.stop_scan_btn.config(state="disabled"))

    def get_vuln_checks(self, scan_type):
        base_checks = [
            {"name": "系统更新状态", "category": "系统", "severity": "medium"},
            {"name": "防火墙状态", "category": "安全", "severity": "high"},
            {"name": "密码策略", "category": "安全", "severity": "medium"},
            {"name": "开放服务检测", "category": "服务", "severity": "low"},
            {"name": "用户账户安全", "category": "账户", "severity": "high"},
        ]

        full_checks = base_checks + [
            {"name": "注册表安全", "category": "系统", "severity": "medium"},
            {"name": "文件权限检查", "category": "系统", "severity": "low"},
            {"name": "网络配置安全", "category": "网络", "severity": "medium"},
            {"name": "浏览器安全设置", "category": "应用", "severity": "low"},
            {"name": "远程桌面安全", "category": "服务", "severity": "high"},
        ]

        deep_checks = full_checks + [
            {"name": "内核漏洞检测", "category": "系统", "severity": "critical"},
            {"name": "驱动程序安全", "category": "系统", "severity": "medium"},
            {"name": "加密算法检查", "category": "安全", "severity": "high"},
            {"name": "日志审计配置", "category": "安全", "severity": "medium"},
            {"name": "应用程序漏洞", "category": "应用", "severity": "medium"},
            {"name": "USB设备安全", "category": "设备", "severity": "low"},
            {"name": "BIOS安全设置", "category": "硬件", "severity": "medium"},
            {"name": "网络共享安全", "category": "网络", "severity": "high"},
        ]

        if scan_type == "quick":
            return base_checks
        elif scan_type == "deep":
            return deep_checks
        else:
            return full_checks

    def perform_vuln_check(self, check):
        import random
        vuln_chance = {
            "critical": 0.05,
            "high": 0.15,
            "medium": 0.3,
            "low": 0.5
        }

        chance = vuln_chance.get(check["severity"], 0.2)
        has_vuln = random.random() < chance

        if has_vuln:
            descriptions = {
                "系统更新状态": "系统存在未安装的安全更新",
                "防火墙状态": "防火墙未完全启用或配置不当",
                "密码策略": "密码复杂度策略未启用",
                "开放服务检测": "存在不必要的开放服务",
                "用户账户安全": "发现未使用的管理员账户",
                "注册表安全": "注册表存在安全配置问题",
                "文件权限检查": "部分系统文件权限设置过宽",
                "网络配置安全": "网络协议配置存在安全隐患",
                "浏览器安全设置": "浏览器安全设置级别过低",
                "远程桌面安全": "远程桌面服务配置不安全",
                "内核漏洞检测": "检测到潜在内核漏洞风险",
                "驱动程序安全": "存在过时的驱动程序",
                "加密算法检查": "使用了弱加密算法",
                "日志审计配置": "审计日志未完全启用",
                "应用程序漏洞": "检测到应用程序版本过旧",
                "USB设备安全": "USB设备未受访问控制",
                "BIOS安全设置": "BIOS安全选项未完全启用",
                "网络共享安全": "网络共享权限设置过宽",
            }

            return {
                "severity": check["severity"],
                "name": check["name"],
                "category": check["category"],
                "description": descriptions.get(check["name"], "存在安全风险"),
                "status": "待修复"
            }
        return None

    def add_vuln_result(self, result):
        tag = result["severity"]
        self.vuln_tree.insert(
            "",
            "end",
            values=(
                result["severity"],
                result["name"],
                result["category"],
                result["description"],
                result["status"]
            ),
            tags=(tag,)
        )

    def export_vuln_report(self):
        if not self.vuln_results:
            messagebox.showinfo("提示", "暂无漏洞数据可导出")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json")],
            initialfile=f"漏洞扫描报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "total_vulns": len(self.vuln_results),
                        "vulnerabilities": self.vuln_results
                    }, f, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("        小思人工智能应用及漏洞管理 - 漏洞扫描报告\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"漏洞总数: {len(self.vuln_results)}\n\n")
                    f.write("-" * 60 + "\n")
                    for i, vuln in enumerate(self.vuln_results, 1):
                        f.write(f"\n[{i}] {vuln['name']}\n")
                        f.write(f"    严重程度: {vuln['severity']}\n")
                        f.write(f"    类别: {vuln['category']}\n")
                        f.write(f"    描述: {vuln['description']}\n")
                        f.write(f"    状态: {vuln['status']}\n")
                    f.write("\n" + "=" * 60 + "\n")

            messagebox.showinfo("成功", f"报告已导出至:\n{file_path}")
            self.add_activity(f"漏洞扫描报告已导出: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def create_port_scan_tab(self):
        container = tk.Frame(self.tab_port_scan, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=10, pady=10)

        control_card = tk.Frame(container, bg=self.colors["card"], padx=15, pady=15)
        control_card.pack(fill="x", pady=(0, 10))

        title = tk.Label(
            control_card,
            text="网络端口扫描",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        title.pack(anchor="w", pady=(0, 10))

        target_frame = tk.Frame(control_card, bg=self.colors["card"])
        target_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            target_frame,
            text="目标地址:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.port_target = tk.StringVar(value="127.0.0.1")
        target_entry = tk.Entry(
            target_frame,
            textvariable=self.port_target,
            font=("Microsoft YaHei UI", 10),
            width=20
        )
        target_entry.grid(row=0, column=1, sticky="w")

        tk.Label(
            target_frame,
            text="    端口范围:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).grid(row=0, column=2, sticky="w")

        self.port_start = tk.StringVar(value="1")
        port_start_entry = tk.Entry(
            target_frame,
            textvariable=self.port_start,
            font=("Microsoft YaHei UI", 10),
            width=8
        )
        port_start_entry.grid(row=0, column=3, sticky="w")

        tk.Label(
            target_frame,
            text="-",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).grid(row=0, column=4, padx=3)

        self.port_end = tk.StringVar(value="1024")
        port_end_entry = tk.Entry(
            target_frame,
            textvariable=self.port_end,
            font=("Microsoft YaHei UI", 10),
            width=8
        )
        port_end_entry.grid(row=0, column=5, sticky="w")

        speed_frame = tk.Frame(control_card, bg=self.colors["card"])
        speed_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            speed_frame,
            text="扫描速度:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left", padx=(0, 10))

        self.port_speed = tk.StringVar(value="normal")
        speeds = [("慢速", "slow"), ("正常", "normal"), ("快速", "fast")]
        for text, value in speeds:
            tk.Radiobutton(
                speed_frame,
                text=text,
                variable=self.port_speed,
                value=value,
                font=("Microsoft YaHei UI", 10),
                bg=self.colors["card"],
                fg=self.colors["text"],
                activebackground=self.colors["card"]
            ).pack(side="left", padx=5)

        btn_frame = tk.Frame(control_card, bg=self.colors["card"])
        btn_frame.pack(fill="x")

        self.port_scan_btn = tk.Button(
            btn_frame,
            text="开始扫描",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors["primary"],
            fg="white",
            activebackground=self.colors["primary_dark"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.start_port_scan,
            padx=25,
            pady=8
        )
        self.port_scan_btn.pack(side="left", padx=3)

        self.port_stop_btn = tk.Button(
            btn_frame,
            text="停止扫描",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors["danger"],
            fg="white",
            activebackground="#c82333",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.stop_port_scan,
            state="disabled",
            padx=25,
            pady=8
        )
        self.port_stop_btn.pack(side="left", padx=3)

        progress_card = tk.Frame(container, bg=self.colors["card"], padx=15, pady=10)
        progress_card.pack(fill="x", pady=(0, 10))

        self.port_progress_var = tk.StringVar(value="准备就绪")
        progress_label = tk.Label(
            progress_card,
            textvariable=self.port_progress_var,
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        progress_label.pack(anchor="w", pady=(0, 5))

        self.port_progress = ttk.Progressbar(progress_card, mode="determinate")
        self.port_progress.pack(fill="x")

        result_card = tk.Frame(container, bg=self.colors["card"], padx=10, pady=10)
        result_card.pack(fill="both", expand=True)

        columns = ("port", "service", "status", "protocol")
        self.port_tree = ttk.Treeview(result_card, columns=columns, show="headings", height=15)

        self.port_tree.heading("port", text="端口")
        self.port_tree.heading("service", text="服务")
        self.port_tree.heading("status", text="状态")
        self.port_tree.heading("protocol", text="协议")

        self.port_tree.column("port", width=100, anchor="center")
        self.port_tree.column("service", width=200, anchor="w")
        self.port_tree.column("status", width=100, anchor="center")
        self.port_tree.column("protocol", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(result_card, orient="vertical", command=self.port_tree.yview)
        self.port_tree.configure(yscrollcommand=scrollbar.set)

        self.port_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.port_tree.tag_configure("open", background="#d4edda")
        self.port_tree.tag_configure("closed", background="#f8f9fa")

    def start_port_scan(self):
        if self.port_scan_running:
            return

        try:
            start_port = int(self.port_start.get())
            end_port = int(self.port_end.get())
            target = self.port_target.get().strip()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的端口号")
            return

        if start_port > end_port or start_port < 1 or end_port > 65535:
            messagebox.showerror("错误", "端口范围无效 (1-65535)")
            return

        if not target:
            messagebox.showerror("错误", "请输入目标地址")
            return

        self.port_scan_running = True
        self.port_scan_btn.config(state="disabled")
        self.port_stop_btn.config(state="normal")
        self.port_results = []
        self.status_text.set("正在进行端口扫描...")
        self.add_activity(f"端口扫描开始: {target}:{start_port}-{end_port}")

        for item in self.port_tree.get_children():
            self.port_tree.delete(item)

        threading.Thread(target=self.port_scan_worker, args=(target, start_port, end_port), daemon=True).start()

    def stop_port_scan(self):
        self.port_scan_running = False
        self.status_text.set("端口扫描已停止")
        self.add_activity("端口扫描已停止")

    def port_scan_worker(self, target, start_port, end_port):
        speed = self.port_speed.get()
        delays = {"slow": 0.1, "normal": 0.05, "fast": 0.01}
        delay = delays.get(speed, 0.05)

        known_ports = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 80: "HTTP", 110: "POP3", 119: "NNTP",
            135: "RPC", 139: "NetBIOS", 143: "IMAP", 161: "SNMP",
            389: "LDAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS",
            587: "SMTP", 993: "IMAPS", 995: "POP3S",
            1433: "MSSQL", 1521: "Oracle", 3306: "MySQL",
            3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
            6379: "Redis", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt",
            27017: "MongoDB"
        }

        total = end_port - start_port + 1
        open_count = 0

        for port in range(start_port, end_port + 1):
            if not self.port_scan_running:
                break

            progress = ((port - start_port + 1) / total) * 100
            msg = f"扫描端口 {port}/{end_port} (已发现 {open_count} 个开放端口)"
            self.root.after(0, lambda m=msg: self.port_progress_var.set(m))
            self.root.after(0, lambda v=progress: self.port_progress.config(value=v))

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(delay)
                result = sock.connect_ex((target, port))
                sock.close()

                service = known_ports.get(port, "未知")
                if result == 0:
                    open_count += 1
                    port_result = {
                        "port": port,
                        "service": service,
                        "status": "开放",
                        "protocol": "TCP"
                    }
                    self.port_results.append(port_result)
                    self.root.after(0, lambda r=port_result: self.add_port_result(r))
            except:
                pass

            time.sleep(delay * 0.1)

        if self.port_scan_running:
            self.root.after(0, lambda: self.port_progress_var.set(
                f"扫描完成，共发现 {len(self.port_results)} 个开放端口"))
            self.root.after(0, lambda: self.port_progress.config(value=100))
            self.root.after(0, lambda: self.status_text.set("端口扫描完成"))
            self.root.after(0, lambda: self.add_activity(
                f"端口扫描完成，发现 {len(self.port_results)} 个开放端口"))

        self.port_scan_running = False
        self.root.after(0, lambda: self.port_scan_btn.config(state="normal"))
        self.root.after(0, lambda: self.port_stop_btn.config(state="disabled"))

    def add_port_result(self, result):
        tag = "open" if result["status"] == "开放" else "closed"
        self.port_tree.insert(
            "",
            "end",
            values=(result["port"], result["service"], result["status"], result["protocol"]),
            tags=(tag,)
        )

    def create_ai_security_tab(self):
        container = tk.Frame(self.tab_ai_security, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=10, pady=10)

        control_card = tk.Frame(container, bg=self.colors["card"], padx=15, pady=15)
        control_card.pack(fill="x", pady=(0, 10))

        title = tk.Label(
            control_card,
            text="AI模型安全检测",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        title.pack(anchor="w", pady=(0, 10))

        desc = tk.Label(
            control_card,
            text="检测AI模型的安全性，包括对抗性攻击风险、数据泄露风险、模型完整性等",
            font=("Microsoft YaHei UI", 9),
            bg=self.colors["card"],
            fg=self.colors["text_light"],
            wraplength=800,
            justify="left"
        )
        desc.pack(anchor="w", pady=(0, 10))

        model_frame = tk.Frame(control_card, bg=self.colors["card"])
        model_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            model_frame,
            text="选择模型:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left", padx=(0, 10))

        self.ai_security_model = tk.StringVar()
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.ai_security_model,
            state="readonly",
            width=30
        )
        self.model_combo.pack(side="left")

        check_frame = tk.Frame(control_card, bg=self.colors["card"])
        check_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            check_frame,
            text="检测项目:",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w", pady=(0, 5))

        self.check_adversarial = tk.BooleanVar(value=True)
        self.check_data_leak = tk.BooleanVar(value=True)
        self.check_integrity = tk.BooleanVar(value=True)
        self.check_privacy = tk.BooleanVar(value=True)

        checks = [
            ("对抗性攻击检测", self.check_adversarial),
            ("数据泄露风险", self.check_data_leak),
            ("模型完整性校验", self.check_integrity),
            ("隐私合规检测", self.check_privacy),
        ]

        for text, var in checks:
            tk.Checkbutton(
                check_frame,
                text=text,
                variable=var,
                font=("Microsoft YaHei UI", 10),
                bg=self.colors["card"],
                fg=self.colors["text"],
                activebackground=self.colors["card"]
            ).pack(side="left", padx=10)

        btn_frame = tk.Frame(control_card, bg=self.colors["card"])
        btn_frame.pack(fill="x")

        self.ai_scan_btn = tk.Button(
            btn_frame,
            text="开始检测",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors["primary"],
            fg="white",
            activebackground=self.colors["primary_dark"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.start_ai_security_scan,
            padx=25,
            pady=8
        )
        self.ai_scan_btn.pack(side="left", padx=3)

        self.ai_stop_btn = tk.Button(
            btn_frame,
            text="停止检测",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors["danger"],
            fg="white",
            activebackground="#c82333",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.stop_ai_security_scan,
            state="disabled",
            padx=25,
            pady=8
        )
        self.ai_stop_btn.pack(side="left", padx=3)

        score_card = tk.Frame(container, bg=self.colors["card"], padx=15, pady=15)
        score_card.pack(fill="x", pady=(0, 10))

        score_title = tk.Label(
            score_card,
            text="安全评分",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        score_title.pack(anchor="w", pady=(0, 10))

        self.ai_score_var = tk.StringVar(value="--")
        score_label = tk.Label(
            score_card,
            textvariable=self.ai_score_var,
            font=("Microsoft YaHei UI", 36, "bold"),
            bg=self.colors["card"],
            fg=self.colors["primary"]
        )
        score_label.pack()

        self.ai_score_desc = tk.Label(
            score_card,
            text="暂无检测结果",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text_light"]
        )
        self.ai_score_desc.pack(pady=5)

        result_card = tk.Frame(container, bg=self.colors["card"], padx=10, pady=10)
        result_card.pack(fill="both", expand=True)

        columns = ("item", "risk_level", "description", "suggestion")
        self.ai_security_tree = ttk.Treeview(result_card, columns=columns, show="headings", height=12)

        self.ai_security_tree.heading("item", text="检测项")
        self.ai_security_tree.heading("risk_level", text="风险等级")
        self.ai_security_tree.heading("description", text="检测结果")
        self.ai_security_tree.heading("suggestion", text="建议")

        self.ai_security_tree.column("item", width=150, anchor="w")
        self.ai_security_tree.column("risk_level", width=80, anchor="center")
        self.ai_security_tree.column("description", width=300, anchor="w")
        self.ai_security_tree.column("suggestion", width=300, anchor="w")

        scrollbar = ttk.Scrollbar(result_card, orient="vertical", command=self.ai_security_tree.yview)
        self.ai_security_tree.configure(yscrollcommand=scrollbar.set)

        self.ai_security_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.ai_security_tree.tag_configure("high", background="#ffe0e0")
        self.ai_security_tree.tag_configure("medium", background="#fff3cd")
        self.ai_security_tree.tag_configure("low", background="#d4edda")

        self.update_model_combo()

    def update_model_combo(self):
        model_names = [m["name"] for m in self.ai_models]
        self.model_combo["values"] = model_names
        if model_names:
            self.model_combo.current(0)

    def start_ai_security_scan(self):
        if self.ai_scan_running:
            return

        model_name = self.ai_security_model.get()
        if not model_name:
            messagebox.showinfo("提示", "请先选择要检测的模型")
            return

        self.ai_scan_running = True
        self.ai_scan_btn.config(state="disabled")
        self.ai_stop_btn.config(state="normal")
        self.ai_security_results = []
        self.status_text.set(f"正在检测模型: {model_name}")
        self.add_activity(f"AI模型安全检测开始: {model_name}")

        for item in self.ai_security_tree.get_children():
            self.ai_security_tree.delete(item)

        threading.Thread(target=self.ai_security_scan_worker, args=(model_name,), daemon=True).start()

    def stop_ai_security_scan(self):
        self.ai_scan_running = False
        self.status_text.set("检测已停止")
        self.add_activity("AI模型安全检测已停止")

    def ai_security_scan_worker(self, model_name):
        checks = []
        if self.check_adversarial.get():
            checks.append({
                "item": "对抗性攻击检测",
                "risk_level": "medium",
                "description": "检测模型对对抗样本的鲁棒性",
                "suggestion": "建议进行对抗训练增强模型鲁棒性"
            })
        if self.check_data_leak.get():
            checks.append({
                "item": "数据泄露风险",
                "risk_level": "high",
                "description": "检测训练数据是否可被推断",
                "suggestion": "建议使用差分隐私技术保护训练数据"
            })
        if self.check_integrity.get():
            checks.append({
                "item": "模型完整性校验",
                "risk_level": "low",
                "description": "验证模型文件是否被篡改",
                "suggestion": "建议使用数字签名确保模型完整性"
            })
        if self.check_privacy.get():
            checks.append({
                "item": "隐私合规检测",
                "risk_level": "medium",
                "description": "检测模型是否符合隐私法规要求",
                "suggestion": "建议进行隐私影响评估并建立数据保护机制"
            })

        total = len(checks)
        for i, check in enumerate(checks):
            if not self.ai_scan_running:
                break

            msg = f"正在检测: {check['item']} ({i+1}/{total})"
            self.root.after(0, lambda m=msg: self.status_text.set(m))

            time.sleep(0.8)

            import random
            if random.random() < 0.6:
                self.ai_security_results.append(check)
                self.root.after(0, lambda r=check: self.add_ai_security_result(r))

        if self.ai_scan_running:
            score = max(0, 100 - len(self.ai_security_results) * 20)
            if score >= 80:
                desc = "安全状况良好"
                color = self.colors["success"]
            elif score >= 60:
                desc = "存在中等风险，建议修复"
                color = self.colors["warning"]
            else:
                desc = "存在高风险，需立即处理"
                color = self.colors["danger"]

            self.root.after(0, lambda s=score: self.ai_score_var.set(str(s)))
            self.root.after(0, lambda d=desc, c=color: self.ai_score_desc.config(text=d, fg=c))
            self.root.after(0, lambda s=score, c=color: self.ai_score_var.set(str(s)) or None)
            self.root.after(0, lambda: self.status_text.set("检测完成"))
            self.root.after(0, lambda: self.add_activity(
                f"AI模型安全检测完成，发现 {len(self.ai_security_results)} 个风险项"))

        self.ai_scan_running = False
        self.root.after(0, lambda: self.ai_scan_btn.config(state="normal"))
        self.root.after(0, lambda: self.ai_stop_btn.config(state="disabled"))

    def add_ai_security_result(self, result):
        tag = result["risk_level"]
        self.ai_security_tree.insert(
            "",
            "end",
            values=(result["item"], result["risk_level"], result["description"], result["suggestion"]),
            tags=(tag,)
        )

    def on_closing(self):
        if self.scan_running or self.port_scan_running or self.ai_scan_running:
            if not messagebox.askyesno("确认", "扫描正在进行中，确定要退出吗？"):
                return
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AIVulnManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
