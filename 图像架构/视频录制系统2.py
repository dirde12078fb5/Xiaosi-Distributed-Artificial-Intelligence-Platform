#  Copyright (c) 2025. 视频录制系统 - 带表情识别功能
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, filedialog

import cv2
import numpy as np
from PIL import Image, ImageTk


class MotionCaptureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("视频录制系统 - 带表情识别")
        self.root.geometry("1920x1080")
        self.root.configure(bg="#f0f0f0")

        # 尝试设置窗口图标
        try:
            self.root.iconbitmap('config/xiaosi.ico')
        except:
            pass

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
        self.expression = "未检测到"  # 表情状态

        # 加载人脸和表情识别模型
        self.face_cascade = self.load_face_cascade()
        self.emotion_labels = ['生气', '厌恶', '恐惧', '开心', '难过', '惊讶', '中性']
        self.emotion_classifier = self.load_emotion_model()

        # 状态栏变量
        self.status_text = tk.StringVar(value="就绪")

        # 创建界面
        self.create_widgets()

    def font_config(self):
        """配置字体，确保中文显示正常"""
        self.default_font = ('SimHei', 10)
        self.title_font = ('SimHei', 16, 'bold')
        self.subtitle_font = ('SimHei', 12, 'bold')

    def load_face_cascade(self):
        """加载人脸检测模型"""
        try:
            # 尝试加载本地模型
            return cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        except:
            # 如果本地没有，使用OpenCV默认路径
            try:
                return cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception as e:
                messagebox.showerror("模型加载错误", f"无法加载人脸检测模型: {str(e)}")
                return None

    def load_emotion_model(self):
        """加载表情识别模型"""
        try:
            # 这里使用预训练的表情识别模型
            # 实际应用中可能需要下载模型文件: https://github.com/opencv/opencv/blob/master/data/haarcascades/
            return cv2.dnn.readNetFromCaffe(
                "deploy.prototxt.txt",
                "emotion_net.caffemodel"
            )
        except Exception as e:
            messagebox.showwarning("模型加载警告", f"无法加载表情识别模型: {str(e)}\n将使用基础表情识别")
            return None

    def create_widgets(self):
        """创建GUI组件"""
        # 顶部标题
        title_frame = tk.Frame(self.root, bg="#3498db", height=50)
        title_frame.pack(fill="x")

        title_label = tk.Label(title_frame, text="视频录制系统 - 带表情识别", font=self.title_font, fg="white",
                               bg="#3498db")
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

        # 表情信息
        self.emotion_label = tk.Label(info_frame, text="表情: 未检测到", font=self.default_font, bg="#e0e0e0")
        self.emotion_label.pack(side="left", padx=10)

        # 右侧控制面板 (保持不变)
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
        self.emotion_label.config(text="表情: 未检测到")

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

    def detect_faces(self, frame):
        """检测人脸"""
        if not self.face_cascade:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return faces, gray

    def recognize_emotion(self, face_roi):
        """识别表情"""
        # 简单的表情识别实现
        # 实际应用中可以使用更复杂的模型提高准确率
        try:
            # 转换为灰度图并调整大小
            face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            face_resized = cv2.resize(face_gray, (48, 48)) / 255.0

            if self.emotion_classifier:
                # 使用深度学习模型进行表情识别
                blob = cv2.dnn.blobFromImage(face_resized, 1.0, (48, 48), (0, 0, 0), swapRB=True, crop=False)
                self.emotion_classifier.setInput(blob)
                predictions = self.emotion_classifier.forward()
                emotion_idx = np.argmax(predictions[0])
                return self.emotion_labels[emotion_idx]
            else:
                # 基础的表情识别（基于简单特征）
                # 这只是一个示例，实际准确率有限
                edges = cv2.Canny(face_gray, 50, 150)
                mouth_region = edges[int(face_gray.shape[0] * 0.6):, :]
                mouth_pixels = np.sum(mouth_region)

                if mouth_pixels > 3000:  # 假设嘴巴张开较大是开心
                    return "开心"
                elif mouth_pixels < 1000:  # 嘴巴紧闭可能是生气或中性
                    eye_region = edges[:int(face_gray.shape[0] * 0.4), :]
                    eye_pixels = np.sum(eye_region)
                    if eye_pixels > 2000:  # 眼睛区域变化大可能是惊讶
                        return "惊讶"
                    else:
                        return "中性"
                else:
                    return "中性"

        except Exception as e:
            print(f"表情识别错误: {e}")
            return "识别中"

    def update_frame(self):
        """更新视频帧并进行表情识别"""
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

            # 检测人脸和识别表情
            faces, gray = self.detect_faces(frame)
            emotion = "未检测到"

            # 处理每个人脸
            for (x, y, w, h) in faces:
                # 绘制人脸框
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # 提取人脸区域
                face_roi = frame[y:y + h, x:x + w]

                # 识别表情
                emotion = self.recognize_emotion(face_roi)
                self.expression = emotion

                # 在人脸框上方显示表情
                cv2.putText(frame, emotion, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # 更新表情显示
            self.emotion_label.config(text=f"表情: {emotion}")

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