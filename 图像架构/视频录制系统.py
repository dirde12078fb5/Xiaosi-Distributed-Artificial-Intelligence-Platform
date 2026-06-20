#  Copyright (c) 2025. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
#  Morbi non lorem porttitor neque feugiat blandit. Ut vitae ipsum eget quam lacinia accumsan.
#  Etiam sed turpis ac ipsum condimentum fringilla. Maecenas magna.
#  Proin dapibus sapien vel ante. Aliquam erat volutpat. Pellentesque sagittis ligula eget metus.
#  Vestibulum commodo. Ut rhoncus gravida arcu.
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, filedialog

import cv2
from PIL import Image, ImageTk


class MotionCaptureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("视频录制系统")
        self.root.geometry("1920x1080")
        self.root.configure(bg="#f0f0f0")

        self.root.iconbitmap('config/xiaosi.ico')

        # 设置中文字体
        self.font_config()

        # 初始化变量
        self.cap = None
        self.is_capturing = False
        self.is_recording = False
        self.frame_count = 0
        self.start_time = 0
        self.fps = 0
        self.recorder = None
        self.output_path = ""

        # 状态栏变量
        self.status_text = tk.StringVar(value="就绪")

        # 创建界面
        self.create_widgets()

    def font_config(self):
        """配置字体，确保中文显示正常"""
        self.default_font = ('SimHei', 10)
        self.title_font = ('SimHei', 16, 'bold')
        self.subtitle_font = ('SimHei', 12, 'bold')


    def create_widgets(self):
        """创建GUI组件"""
        # 顶部标题
        title_frame = tk.Frame(self.root, bg="#3498db", height=50)
        title_frame.pack(fill="x")

        title_label = tk.Label(title_frame, text="视频录制系统", font=self.title_font, fg="white", bg="#3498db")
        title_label.pack(pady=10)

        # 主内容区域
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左侧视频区域
        left_frame = tk.Frame(main_frame, bg="#e0e0e0", width=800, height=600)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # 视频显示区域
        self.video_frame = tk.Label(left_frame, bg="black")
        self.video_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 视频信息
        info_frame = tk.Frame(left_frame, bg="#e0e0e0")
        info_frame.pack(fill="x", padx=5, pady=5)

        self.fps_label = tk.Label(info_frame, text="FPS: 0", font=self.default_font, bg="#e0e0e0")
        self.fps_label.pack(side="left", padx=10)

        self.status_label = tk.Label(info_frame, text="状态: 就绪", font=self.default_font, bg="#e0e0e0")
        self.status_label.pack(side="left", padx=10)

        # 右侧控制面板
        right_frame = tk.Frame(main_frame, bg="#e0e0e0", width=350, height=600)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # 设备控制
        device_frame = tk.LabelFrame(right_frame, text="设备控制", font=self.subtitle_font, bg="#e0e0e0", padx=10,
                                     pady=10)
        device_frame.pack(fill="x", padx=5, pady=5)

        self.camera_var = tk.StringVar(value="0")
        camera_label = tk.Label(device_frame, text="摄像头:", font=self.default_font, bg="#e0e0e0")
        camera_label.grid(row=0, column=0, sticky="w", pady=5)

        camera_entry = tk.Entry(device_frame, textvariable=self.camera_var, width=5, font=self.default_font)
        camera_entry.grid(row=0, column=1, sticky="w", pady=5)

        browse_button = tk.Button(device_frame, text="浏览文件", command=self.browse_file, font=self.default_font,
                                  bg="#3498db", fg="white")
        browse_button.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        self.device_path = tk.StringVar(value="")
        device_path_label = tk.Label(device_frame, textvariable=self.device_path, font=self.default_font, bg="#e0e0e0",
                                     wraplength=250)
        device_path_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=5)

        # 保存按钮引用
        self.start_capture_btn = tk.Button(device_frame, text="开始捕获", command=self.start_capture,
                                           font=self.default_font, bg="#27ae60", fg="white")
        self.start_capture_btn.grid(row=2, column=0, pady=10)

        self.stop_capture_btn = tk.Button(device_frame, text="停止捕获", command=self.stop_capture,
                                          font=self.default_font, bg="#e74c3c", fg="white", state=tk.DISABLED)
        self.stop_capture_btn.grid(row=2, column=1, padx=5, pady=10)

        # 录制控制
        record_frame = tk.LabelFrame(right_frame, text="录制控制", font=self.subtitle_font, bg="#e0e0e0", padx=10,
                                     pady=10)
        record_frame.pack(fill="x", padx=5, pady=5)

        self.output_path_var = tk.StringVar(value="output.avi")
        output_label = tk.Label(record_frame, text="输出文件:", font=self.default_font, bg="#e0e0e0")
        output_label.grid(row=0, column=0, sticky="w", pady=5)

        output_entry = tk.Entry(record_frame, textvariable=self.output_path_var, width=15, font=self.default_font)
        output_entry.grid(row=0, column=1, sticky="w", pady=5)

        browse_output_button = tk.Button(record_frame, text="浏览", command=self.browse_output, font=self.default_font,
                                         bg="#3498db", fg="white")
        browse_output_button.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # 保存按钮引用
        self.start_record_btn = tk.Button(record_frame, text="开始录制", command=self.start_recording,
                                          font=self.default_font, bg="#f39c12", fg="white")
        self.start_record_btn.grid(row=1, column=0, pady=10)

        self.stop_record_btn = tk.Button(record_frame, text="停止录制", command=self.stop_recording,
                                         font=self.default_font, bg="#e74c3c", fg="white", state=tk.DISABLED)
        self.stop_record_btn.grid(row=1, column=1, padx=5, pady=10)

        # 底部状态栏
        status_frame = tk.Frame(self.root, bg="#34495e", height=30)
        status_frame.pack(fill="x", side="bottom")

        status_bar = tk.Label(status_frame, textvariable=self.status_text, font=self.default_font, fg="white",
                              bg="#34495e", anchor="w")
        status_bar.pack(fill="both", padx=10, pady=5)

    def browse_file(self):
        """浏览视频文件"""
        file_path = filedialog.askopenfilename(filetypes=[("视频文件", "*.mp4;*.avi;*.mov;*.mkv")])
        if file_path:
            self.device_path.set(file_path)
            self.camera_var.set("")

    def browse_output(self):
        """浏览输出文件位置"""
        file_path = filedialog.asksaveasfilename(defaultextension=".avi",
                                                 filetypes=[("AVI文件", "*.avi"), ("MP4文件", "*.mp4")])
        if file_path:
            self.output_path_var.set(file_path)

    def start_capture(self):
        """开始捕捉视频"""
        if self.is_capturing:
            return

        camera_id = self.camera_var.get()
        device_path = self.device_path.get()

        try:
            if device_path:
                # 从文件打开
                self.cap = cv2.VideoCapture(device_path)
            elif camera_id.isdigit():
                # 从摄像头打开
                self.cap = cv2.VideoCapture(int(camera_id))
            else:
                messagebox.showerror("错误", "请指定有效的摄像头ID或视频文件")
                return

            if not self.cap.isOpened():
                messagebox.showerror("错误", "无法打开视频设备或文件")
                return

            self.is_capturing = True
            self.frame_count = 0
            self.start_time = time.time()

            # 更新按钮状态
            self.start_capture_btn.config(state=tk.DISABLED)
            self.stop_capture_btn.config(state=tk.NORMAL)

            # 启动视频捕获线程
            self.capture_thread = threading.Thread(target=self.update_frame, daemon=True)
            self.capture_thread.start()

            self.update_status("正在捕获视频...")

        except Exception as e:
            messagebox.showerror("错误", f"启动捕获时出错: {str(e)}")
            self.is_capturing = False

    def stop_capture(self):
        """停止捕捉视频"""
        self.is_capturing = False

        # 更新按钮状态
        self.start_capture_btn.config(state=tk.NORMAL)
        self.stop_capture_btn.config(state=tk.DISABLED)

        # 停止录制
        if self.is_recording:
            self.stop_recording()

        # 释放资源
        if self.cap:
            self.cap.release()
            self.cap = None

        # 清空视频显示区域
        self.video_frame.config(image="")

        self.update_status("已停止捕获")

    def start_recording(self):
        """开始录制视频"""
        if not self.is_capturing:
            messagebox.showinfo("提示", "请先开始视频捕获")
            return

        if self.is_recording:
            return

        try:
            output_path = self.output_path_var.get()
            if not output_path:
                output_path = "output.avi"

            # 获取视频参数
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 设置视频编码器
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            if output_path.lower().endswith('.mp4'):
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            # 创建视频写入对象
            self.recorder = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            self.is_recording = True

            # 更新按钮状态
            self.start_record_btn.config(state=tk.DISABLED)
            self.stop_record_btn.config(state=tk.NORMAL)

            self.update_status(f"正在录制: {os.path.basename(output_path)}")

        except Exception as e:
            messagebox.showerror("错误", f"开始录制时出错: {str(e)}")
            self.is_recording = False

    def stop_recording(self):
        """停止录制视频"""
        self.is_recording = False

        # 更新按钮状态
        self.start_record_btn.config(state=tk.NORMAL)
        self.stop_record_btn.config(state=tk.DISABLED)

        # 释放录制资源
        if self.recorder:
            self.recorder.release()
            self.recorder = None

        self.update_status("已停止录制")

    def update_frame(self):
        """更新视频帧"""
        while self.is_capturing:
            ret, frame = self.cap.read()
            if not ret:
                self.update_status("无法获取视频帧")
                self.stop_capture()
                break

            # 计算FPS
            self.frame_count += 1
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 0:
                self.fps = self.frame_count / elapsed_time

            # 更新FPS显示
            self.fps_label.config(text=f"FPS: {self.fps:.2f}")

            # 如果正在录制
            if self.is_recording and self.recorder:
                self.recorder.write(frame)

            # 显示处理后的帧
            self.display_frame(frame)

    def display_frame(self, frame):
        """显示处理后的帧"""
        # 调整帧大小以适应显示区域
        frame_height, frame_width = frame.shape[:2]
        display_width = self.video_frame.winfo_width()
        display_height = self.video_frame.winfo_height()

        if display_width > 0 and display_height > 0:
            # 计算调整比例
            width_ratio = display_width / frame_width
            height_ratio = display_height / frame_height
            ratio = min(width_ratio, height_ratio)

            # 调整大小
            new_width = int(frame_width * ratio)
            new_height = int(frame_height * ratio)
            frame = cv2.resize(frame, (new_width, new_height))

        # 转换为RGB格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 转换为PhotoImage
        photo = ImageTk.PhotoImage(image=Image.fromarray(rgb_frame))

        # 更新显示
        self.video_frame.config(image=photo)
        self.video_frame.image = photo

    def update_status(self, message):
        """更新状态栏消息"""
        self.status_text.set(message)
        self.status_label.config(text=f"状态: {message}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MotionCaptureGUI(root)
    root.mainloop()