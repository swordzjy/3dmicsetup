import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial
import serial.tools.list_ports
import cv2
from pyzbar.pyzbar import decode
from PIL import Image, ImageTk
import threading
import time
import os
import queue
import numpy as np
from screenshot_selector import start_screenshot  # 导入我们的截图模块
import pyaudio
import matplotlib
from matplotlib.font_manager import FontProperties
matplotlib.use("TkAgg")  # 设置matplotlib后端为TkAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm

# 程序依赖以下包:
# pip install pyserial opencv-python pyzbar pillow numpy pyaudio matplotlib

# Language dictionary
LANGUAGES = {
    "en": {
        "title": "Tradio 3D Microphone",
        "matplot_title": "Real-time Sound Wave",
        "left_channel": "Left Channel",
        "right_channel": "Right Channel",
        "status_not_connected": "Not Connected",
        "status_connected": "Connected to {}",
        "waveform": "",
        "qr_scan": "QR Code Scan",
        "open_camera": "Open Camera",
        "close_camera": "Close Camera",
        "select_image": "Select Image",
        "screenshot": "Screenshot",
        "qr_content": "QR Code Content",
        "send_command": "Setup Microphone",
        "device_response": "Device Response",
        "clear": "Clear",
        "send": "Send",
        "auto_connect_try": "Trying to automatically connect to microphone: {}",
        "auto_connect_fail": "Auto connection failed: {}",
        "mic_not_found": "3D Microphone not found",
        "log_connected": "Successfully connected to device {} (baud rate: 115200)",
        "connection_error": "Connection error: {}",
        "read_error": "Read error: {}",
        "send_fail": "Send failed: {}",
        "parsed_qr": "QR code parsed, contains {} commands",
        "no_commands": "No commands to send",
        "device_not_connected": "Error: Device not connected",
        "sending_commands": "Sending Commands...",
        "sending_complete": "Sending Complete",
        "of_total": "{}/{}",
        "screenshot_start": "Starting screenshot function...",
        "screenshot_fail": "Failed to start screenshot: {}",
        "qr_not_detected": "No QR code detected in screenshot",
        "qr_detected": "Successfully detected QR code from screenshot",
        "screenshot_error": "Error processing screenshot: {}",
        "waveform_started": "Waveform display started",
        "waveform_error": "Waveform startup error: {}",
        "waveform_update_error": "Waveform update error: {}",
        "found_3d_mic": "Found 3D microphone audio device: {}",
        "mic_not_found_default": "Specific 3D microphone audio device not found, will use default",
        "using_default_audio": "Using default audio device: {}",
        "audio_device_error": "Error finding audio device: {}",
        "waveform_stopped": "Waveform display stopped",
        "close_audio_error": "Error closing audio stream: {}",
        "language": "Language",
        "error_title":"Error",
        "qr_preview": "QR Preview"
    },
    "zh": {
        "title": "Tradio 3D麦克风",
        "matplot_title": "实时声音波形",
        "left_channel": "左声道",
        "right_channel": "右声道",
        "status_not_connected": "未连接",
        "status_connected": "已连接 {}",
        "waveform": "",
        "qr_scan": "二维码扫描",
        "open_camera": "打开摄像头",
        "close_camera": "关闭摄像头",
        "select_image": "选择图片",
        "screenshot": "屏幕截图",
        "qr_content": "二维码内容",
        "send_command": "配置麦克风",
        "device_response": "设备响应",
        "clear": "清除",
        "send": "发送",
        "auto_connect_try": "尝试自动连接麦克风设备: {}",
        "auto_connect_fail": "自动连接失败: {}",
        "mic_not_found": "未找到3D麦克风设备",
        "log_connected": "成功连接到设备 {} (波特率: 115200)",
        "connection_error": "连接错误: {}",
        "read_error": "读取错误: {}",
        "send_fail": "发送失败: {}",
        "parsed_qr": "已解析二维码，包含 {} 条指令",
        "no_commands": "没有可发送的指令",
        "device_not_connected": "错误: 设备未连接",
        "sending_commands": "正在发送指令...",
        "sending_complete": "发送完成",
        "of_total": "{}/{}",
        "screenshot_start": "正在启动屏幕截图功能...",
        "screenshot_fail": "启动截图功能失败: {}",
        "qr_not_detected": "未在截图中检测到二维码",
        "qr_detected": "成功从截图中检测到二维码",
        "screenshot_error": "处理截图时出错: {}",
        "waveform_started": "波形图显示已启动",
        "waveform_error": "启动波形图错误: {}",
        "waveform_update_error": "波形图更新错误: {}",
        "found_3d_mic": "找到3D麦克风音频设备: {}",
        "mic_not_found_default": "未找到特定的3D麦克风音频设备，将使用默认设备",
        "using_default_audio": "使用默认音频设备: {}",
        "audio_device_error": "查找音频设备错误: {}",
        "waveform_stopped": "波形图显示已关闭",
        "close_audio_error": "关闭音频流错误: {}",
        "language": "语言",
        "error_title":"错误",
        "qr_preview": "二维码预览"
    }
}

# Configure matplotlib to use a CJK-compatible font
matplotlib.rcParams['font.family'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'sans-serif']

# Fall back to a specific font file if necessary
try:
    # Check if a suitable font is available
    font_path = fm.findfont(fm.FontProperties(family=['SimHei', 'Microsoft YaHei']))
    if 'DejaVu' in font_path:  # No CJK font found
        # Try to find any font that supports Chinese
        fallback_font = None
        for font in fm.findSystemFonts():
            if any(name in font.lower() for name in ['simhei', 'yahei', 'simsun', 'noto', 'cjk']):
                fallback_font = font
                break
        if fallback_font:
            matplotlib.rcParams['font.family'] = 'sans-serif'
            matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
            matplotlib.rcParams['axes.unicode_minus'] = False
except:
    print("Warning: Could not configure CJK font for matplotlib")

class SerialQRCodeApp:
    def __init__(self, root):
        self.root = root
        
        # Set default language
        self.current_language = "en"
        self.texts = LANGUAGES[self.current_language]
        
        self.root.title(self.texts["title"])
        
        # 避免多次调整窗口大小
        window_width = 1600
        window_height = 1200
       
        self.root.minsize(1024, 768)
        # 获取屏幕尺寸
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 一次性设置窗口大小和位置
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 强制更新
        root.update_idletasks()
        
        # 设备变量
        self.serial_port = None
        self.is_connected = False
        self.default_port = None  # 默认麦克风设备
        self.command_queue = queue.Queue()
        self.response_buffer = "Welcome to Tradio 3D Mic"
        
        # 创建界面
        self.create_ui()
         
        # 直接在控制台输出，确保能看到
        print("界面创建完成，即将嵌入波形图...")
        
        # 音频处理相关参数
        self.audio_setup()
        
        print("Audio setup completed, arranged to embed waveform")
        
        # 自动启动波形图 - 确保在嵌入后才启动
        self.root.after(2000, self.start_waveform)
        
        # 启动线程
        self.running = True
        self.read_thread = threading.Thread(target=self.read_from_serial, daemon=True)
        self.read_thread.start()
        self.command_thread = threading.Thread(target=self.process_command_queue, daemon=True)
        self.command_thread.start()
        
        # 自动连接麦克风设备
        self.root.after(1000, self.auto_connect_mic)
        
        # 预先填充文本部件以确保它获得正确的大小
        self.response_text.config(state=tk.NORMAL)
        self.response_text.insert(tk.END, "\n" * 8)  # 预填充8行
        self.response_text.delete(1.0, tk.END)       # 然后清空
        self.response_text.config(state=tk.DISABLED)
        
    def create_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置主框架中的行列权重 - 调整权重使关键区域获得足够空间
        main_frame.columnconfigure(0, weight=1)  # 列可以扩展
        main_frame.rowconfigure(0, weight=0)  # 第一行 - 顶部操作栏（固定高度）
        main_frame.rowconfigure(1, weight=4)  # 第二行 - 波形图（较大权重）
        main_frame.rowconfigure(2, weight=2)  # 第三行 - 二维码相关区域（适当权重）
        main_frame.rowconfigure(3, weight=2)  # 第四行 - 设备响应（适当权重）
        main_frame.rowconfigure(4, weight=0)  # 第五行 - 命令输入（固定高度）
        
        # 顶部操作栏 - 只包含状态标签和操作按钮
        top_frame = ttk.Frame(main_frame, padding="5")
        top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # 配置top_frame内部布局
        top_frame.columnconfigure(0, weight=0)  # 状态标签 - 固定宽度
        top_frame.columnconfigure(1, weight=0)  # 摄像头按钮 - 固定宽度
        top_frame.columnconfigure(2, weight=0)  # 选择图片按钮 - 固定宽度
        top_frame.columnconfigure(3, weight=0)  # 屏幕截图按钮 - 固定宽度
        top_frame.columnconfigure(4, weight=1)  # 空白填充区域 - 可扩展
        top_frame.columnconfigure(5, weight=0)  # 语言选择 - 固定宽度
        
        # 状态标签
        self.status_label = ttk.Label(top_frame, text=self.texts["status_not_connected"])
        self.status_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        # 二维码按钮
        self.camera_button = ttk.Button(top_frame, text=self.texts["open_camera"], command=self.toggle_camera)
        self.camera_button.grid(row=0, column=1, padx=5)
        
        self.file_button = ttk.Button(top_frame, text=self.texts["select_image"], command=self.select_image)
        self.file_button.grid(row=0, column=2, padx=5)
        
        self.screenshot_button = ttk.Button(top_frame, text=self.texts["screenshot"], command=self.capture_screenshot)
        self.screenshot_button.grid(row=0, column=3, padx=5)
        
        # 语言选择器（最右侧）
        lang_frame = ttk.Frame(top_frame)
        lang_frame.grid(row=0, column=5, sticky="e")
        
        self.lang_label = ttk.Label(lang_frame, text=self.texts["language"]+":")
        self.lang_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.lang_var = tk.StringVar(value=self.current_language)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, 
                                  values=list(LANGUAGES.keys()), width=5, state="readonly")
        lang_combo.pack(side=tk.LEFT)
        lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        
        # 波形图容器框架
        
        self.waveform_frame = ttk.LabelFrame(main_frame, text="", padding="10")
        self.waveform_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        # 设置最小高度
        self.waveform_frame.config(height=300, width=400)
        self.waveform_frame.pack_propagate(False)  # 确保高度固定，不会被子组件影响
        
        # 防止自动调整大小
        self.waveform_frame.grid_propagate(False)
        
        # 二维码区域 - 第三行，包含预览和内容两个部分
        qr_area_frame = ttk.Frame(main_frame)
        qr_area_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        qr_area_frame.columnconfigure(0, weight=2)  # 预览区域占比3
        qr_area_frame.columnconfigure(1, weight=8)  # 内容区域占比7
        qr_area_frame.rowconfigure(0, weight=1)  # 确保行可以扩展
        
        # 预览区域
        self.preview_frame = ttk.LabelFrame(qr_area_frame, text=self.texts["qr_preview"], padding="5")
        self.preview_frame.grid_configure(sticky="w")  # 设置为靠左对齐
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.preview_frame.config(height=50, width=50)
        
        # 防止自动调整大小
        self.preview_frame.grid_propagate(False)
        
        # 创建一个固定大小的Label来显示图像
        # 设置白色背景以便于区分图像边界
        self.preview_label = tk.Label(self.preview_frame, bg='white')
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初始化photo属性，避免图像被垃圾回收
        self.photo = None
        
        # 二维码内容区域
        self.result_frame = ttk.LabelFrame(qr_area_frame, text=self.texts["qr_content"], padding="10")
        self.result_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # 配置result_frame内部布局
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)
        self.result_frame.rowconfigure(1, weight=0)
        self.result_frame.grid_propagate(False)
        # 修改文本框高度为适当值，并添加滚动条
        self.result_text = tk.Text(self.result_frame, height=3, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, sticky="nsew")
        
        # 添加滚动条使内容过多时可滚动查看
        result_scrollbar = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        result_scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_text.config(yscrollcommand=result_scrollbar.set)
        
        # 添加按钮框架，放在文本框下方
        button_frame = ttk.Frame(self.result_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.send_button = ttk.Button(button_frame, text=self.texts["send_command"], 
                                    command=self.send_qr_commands)
        self.send_button.pack(pady=5, padx=5, ipadx=10, ipady=5)
        self.send_button.config(state=tk.DISABLED)  # Disable after placement
        
        # 响应显示区域 - 第四行
        self.response_frame = ttk.LabelFrame(main_frame, text=self.texts["device_response"], padding="10")
        self.response_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        
        # 配置response_frame内部布局
        self.response_frame.columnconfigure(0, weight=1)
        self.response_frame.rowconfigure(0, weight=1)
        self.response_frame.rowconfigure(1, weight=0)
        self.response_frame.grid_propagate(False)
        # 修改文本框高度为适当值
        self.response_text = tk.Text(self.response_frame, height=8, wrap=tk.WORD)
        self.response_text.grid(row=0, column=0, sticky="nsew")
        self.response_text.config(state=tk.DISABLED)
        
        # 滚动条
        response_scrollbar = ttk.Scrollbar(self.response_text, orient=tk.VERTICAL, command=self.response_text.yview)
        response_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.response_text.config(yscrollcommand=response_scrollbar.set)
        
        self.clear_button = ttk.Button(self.response_frame, text=self.texts["clear"], command=self.clear_response)
        self.clear_button.grid(row=1, column=0, pady=5)
        
        # 手动命令输入 - 第五行
        cmd_frame = ttk.Frame(main_frame, padding="5")
        cmd_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        
        # 配置cmd_frame内部布局
        cmd_frame.columnconfigure(0, weight=1)
        cmd_frame.columnconfigure(1, weight=0)
        
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.grid(row=0, column=0, sticky="ew")
        
        self.cmd_button = ttk.Button(cmd_frame, text=self.texts["send"], command=self.send_manual_command, state=tk.DISABLED)
        self.cmd_button.grid(row=0, column=1, padx=5)
        
        self.cmd_entry.bind("<Return>", lambda e: self.send_manual_command())
        
        # 摄像头变量
        self.cap = None
        self.camera_active = False
        
        # 解析到的二维码命令
        self.qr_commands = []
        
        # 最后一次性强制所有组件更新
        for child in self.root.winfo_children():
            child.update_idletasks()
        
    def change_language(self, event=None):
        """Change the application language"""
        lang = self.lang_var.get()
        if lang in LANGUAGES and lang != self.current_language:
            self.current_language = lang
            self.texts = LANGUAGES[lang]
            self.update_ui_texts()
    
    def update_ui_texts(self):
        """Update all UI texts to the current language"""
        # Update window title
        self.root.title(self.texts["title"])
        
        # Update status
        if self.is_connected and self.serial_port:
            self.status_label.config(text=self.texts["status_connected"].format(self.serial_port.port))
        else:
            self.status_label.config(text=self.texts["status_not_connected"])
        
        # Update frame titles
        self.waveform_frame.config(text=self.texts["waveform"])
        
        # # Update QR frames
        # self.preview_frame.config(text=self.texts["qr_preview"])
        # self.result_frame.config(text=self.texts["qr_content"])
        
        # Update all LabelFrames
        for child in self.root.winfo_children()[0].winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "preview" in child.cget("text").lower() or "二维码预览" in child.cget("text"):
                    child.config(text=self.texts["qr_preview"])
                elif "content" in child.cget("text").lower() or "内容" in child.cget("text"):
                    child.config(text=self.texts["qr_content"])
                elif "response" in child.cget("text").lower() or "响应" in child.cget("text"):
                    child.config(text=self.texts["device_response"])
        
        # Update button texts
        self.camera_button.config(text=self.texts["open_camera"] if not self.camera_active 
                                  else self.texts["close_camera"])
        self.file_button.config(text=self.texts["select_image"])
        self.screenshot_button.config(text=self.texts["screenshot"])
        self.send_button.config(text=self.texts["send_command"])
        self.clear_button.config(text=self.texts["clear"])
        self.cmd_button.config(text=self.texts["send"])
        
        # Update language selector label
        for child in self.root.winfo_children()[0].winfo_children():
            if isinstance(child, ttk.Frame):  # This is our language frame
                for langchild in child.winfo_children():
                    if isinstance(langchild, ttk.Label):
                        langchild.config(text=self.texts["language"]+":")
    
    def audio_setup(self):
        """设置音频参数和Matplotlib波形图"""
        # 音频处理参数
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        
        # 创建Matplotlib图表
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(self.texts["matplot_title"])
        self.ax.set_ylim(-10000, 10000)
        self.ax.set_xlim(0, self.CHUNK)
        self.ax.grid(True)
        
        # 初始化线条
        self.lines = []
        self.lines.append(self.ax.plot([], [], 'g-', label=self.texts["left_channel"])[0])
        self.lines.append(self.ax.plot([], [], 'r-', label=self.texts["right_channel"])[0])
        self.ax.legend()
        
        # 嵌入到Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.waveform_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # PyAudio对象
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.waveform_active = False
        self.update_timer_id = None
    
    def start_waveform(self):
        """启动波形图显示"""
        try:
            # 如果已有流，先关闭
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
                self.stream = None
            
            # 查找3D麦克风的音频设备
            input_device_index = self.find_3d_mic_audio_device()
            if input_device_index is None:
                # 如果找不到特定的3D麦克风，使用默认设备
                input_device_index = self.p.get_default_input_device_info().get('index', 0)
                self.log_response(self.texts["using_default_audio"].format(self.p.get_device_info_by_index(input_device_index).get('name')))
            
            # 打开音频流
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=self.CHUNK
            )
            
            self.waveform_active = True
            
            # 确保PyQtGraph小部件可见
            if hasattr(self, 'canvas'):
                self.canvas.draw()
            
            # 更新按钮文本
            # 使用tkinter的after方法进行波形更新
            self.update_waveform_tk()
            
            self.log_response(self.texts["waveform_started"])
        except Exception as e:
            self.log_response(f"{self.texts['waveform_error']} {str(e)}")
            # 确保状态一致
            self.waveform_active = False
            if self.stream:
                try:
                    self.stream.close()
                except:
                    pass
                self.stream = None
    
    def find_3d_mic_audio_device(self):
        """尝试查找3D麦克风的音频设备"""
        try:
            device_count = self.p.get_device_count()
            
            # 查找名称中包含特定关键字的设备
            keywords = ["3d", "mic", "麦克风", "USB"]
            
            for i in range(device_count):
                device_info = self.p.get_device_info_by_index(i)
                device_name = device_info.get('name', '').lower()
                
                # 检查设备名称中是否包含关键字
                if device_info.get('maxInputChannels') > 0 and any(k.lower() in device_name for k in keywords):
                    self.log_response(self.texts["found_3d_mic"].format(device_info.get('name')))
                    return i
            
            # 如果找不到特定设备，返回None
            self.log_response(self.texts["mic_not_found_default"])
            return None
        except Exception as e:
            self.log_response(f"{self.texts['audio_device_error']} {str(e)}")
            return None
    
    def stop_waveform(self):
        """停止波形图显示"""
        self.waveform_active = False
        
        # 取消定时器
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)
            self.update_timer_id = None
        
        # 关闭音频流
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                self.log_response(f"{self.texts['close_audio_error']} {str(e)}")
        self.stream = None
    
        # 更新按钮文本
        
        self.log_response(self.texts["waveform_stopped"])
    
    def refresh_ports(self):
        """刷新可用设备列表"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        
        # 尝试找到麦克风设备设备
        mic_port = self.find_specific_mic()
        if mic_port:
            self.default_port = mic_port
            try:
                index = ports.index(mic_port)
                self.port_combo.current(index)
            except (ValueError, tk.TclError):
                if ports:
                    self.port_combo.current(0)
        elif ports:
            self.port_combo.current(0)
            
        return ports
    
    def find_specific_mic(self):
        """查找特定VID/PID的麦克风设备"""
        target_vid = "0x1FC9"  # 3dmic的VID
        target_pid = "0x009E"  # 3dmic的PID
        
        print(f"正在查找3d麦克风...")
        
        for port in serial.tools.list_ports.comports():
            vid = f"0x{port.vid:04x}" if port.vid else None
            pid = f"0x{port.pid:04x}" if port.pid else None
            
            if vid and pid and vid.lower() == target_vid.lower() and pid.lower() == target_pid.lower():
                print(f"找到目标设备: {port.device} (VID:{vid}, PID:{pid})")
                return port.device
        
        print("未找到3d麦克风")
        return None
    
    def auto_connect_mic(self):
        """自动连接麦克风设备设备"""
        self.default_port = self.find_specific_mic()
        
        if not self.is_connected and self.default_port:
            self.log_response(f"{self.texts['auto_connect_try']} {self.default_port}")
            try:
                self.connect_to_specific_port(self.default_port)
            except Exception as e:
                self.log_response(self.texts["auto_connect_fail"].format(str(e)))
        else:
            self.log_response(self.texts["mic_not_found"])
    
    def connect_to_specific_port(self, port):
        """连接到指定的端口"""
        try:
            baudrate = 115200  # 使用固定的波特率
            
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            
            # 设置DTR信号
            self.serial_port.setDTR(True)
            
            self.is_connected = True
            self.status_label.config(text=f"{self.texts['status_connected']} {port}")
            self.cmd_button.config(state=tk.NORMAL)
            self.update_send_button_state()
            
            self.log_response(f"{self.texts['log_connected']} {port}")
            
        except Exception as e:
            raise Exception(f"{self.texts['connection_error']} {str(e)}")
    
    def read_from_serial(self):
        """从设备读取数据的线程"""
        while self.running:
            if self.is_connected and self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        text = data.decode('utf-8', errors='replace')
                        self.response_buffer += text
                        
                        # 检查是否有完整的行
                        if '\n' in self.response_buffer or '\r' in self.response_buffer:
                            self.log_response(self.response_buffer.strip())
                            self.response_buffer = ""
                            
                except Exception as e:
                    self.log_response(f"{self.texts['read_error']} {str(e)}")
                    if "device disconnected" in str(e) or "port is closed" in str(e):
                        self.root.after(0, self.handle_disconnect)
            
            # 短暂休眠，避免高CPU使用率
            time.sleep(0.01)
    
    def handle_disconnect(self):
        """处理意外断开连接"""
        self.disconnect_serial()
    
    def send_manual_command(self):
        """发送手动输入的命令"""
        if not self.is_connected:
            messagebox.showerror(self.texts["error_title"], self.texts["device_not_connected"])
            return
        
        command = self.cmd_entry.get().strip()
        if not command:
            return
        
        self.send_command(command)
        self.cmd_entry.delete(0, tk.END)
    
    def send_command(self, command):
        """发送命令到设备"""
        self.command_queue.put(command)
        
    def process_command_queue(self):
        """处理命令队列的线程"""
        while self.running:
            try:
                if not self.command_queue.empty() and self.is_connected:
                    command = self.command_queue.get()
                    
                    try:
                        # 添加回车换行符
                        self.serial_port.write((command + '\r\n').encode('utf-8'))
                        self.log_response(f"{self.texts['sending_commands']} {command}", is_sent=True)
                        
                        # 等待一段时间，给设备处理时间
                        time.sleep(0.5)
                        
                    except Exception as e:
                        self.log_response(f"{self.texts['send_fail']} {str(e)}")
                        if "device disconnected" in str(e) or "port is closed" in str(e):
                            self.root.after(0, self.handle_disconnect)
                    
                    finally:
                        self.command_queue.task_done()
            except Exception as e:
                print(f"command error: {str(e)}")
            
            # 短暂休眠
            time.sleep(0.01)
    
    def log_response(self, message, is_sent=False):
        """Log message in response area"""
        def _update():
            self.response_text.config(state=tk.NORMAL)
            timestamp = time.strftime("%H:%M:%S")
            
            if is_sent:
                self.response_text.insert(tk.END, f"[{timestamp}] {message}\n", "sent")
            else:
                self.response_text.insert(tk.END, f"[{timestamp}] {message}\n", "received")
            
            # self.response_text.see(tk.END)
            # self.response_text.config(state=tk.DISABLED)
        
        self.root.after(0, _update)
    
    def clear_response(self):
        """清除响应区域"""
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete(1.0, tk.END)
        self.response_text.config(state=tk.DISABLED)
    
    def toggle_camera(self):
        """切换摄像头状态"""
        if self.camera_active:
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        """启动摄像头"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("错误", "无法打开摄像头")
                return
            
            self.camera_active = True
            self.camera_button.config(text="关闭摄像头")
            self.update_camera_feed()
            
        except Exception as e:
            messagebox.showerror("摄像头错误", str(e))
    
    def stop_camera(self):
        """停止摄像头"""
        self.camera_active = False
        self.camera_button.config(text="打开摄像头")
        
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def update_camera_feed(self):
        """更新摄像头画面并检测二维码"""
        if self.camera_active and self.cap:
            ret, frame = self.cap.read()
            if ret:
                # 检测二维码
                qr_codes = decode(frame)
                for qr in qr_codes:
                    # 绘制二维码边框
                    points = qr.polygon
                    if len(points) == 4:
                        pts = [(p.x, p.y) for p in points]
                        pts = [pts[0], pts[1], pts[2], pts[3]]
                        pts = np.array(pts, dtype=np.int32)
                        cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
                    
                    # 解析二维码内容
                    data = qr.data.decode('utf-8')
                    self.process_qr_data(data)
                    
                    # 检测到二维码后停止摄像头
                    self.stop_camera()
                    return
                
                # 转换格式显示到UI
                cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(cv_image)
                self.display_image(pil_image)
                
                # 继续更新
                self.root.after(10, self.update_camera_feed)
            else:
                self.stop_camera()
                messagebox.showerror("错误", "无法从摄像头读取图像")
    
    def select_image(self):
        """从文件选择图片"""
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if file_path:
            try:
                # 读取图片
                image = cv2.imread(file_path)
                if image is None:
                    messagebox.showerror("错误", "无法读取所选图片")
                    return
                
                # 检测二维码
                qr_codes = decode(image)
                if not qr_codes:
                    messagebox.showwarning("提示", "未在图片中检测到二维码")
                    
                    # 显示图片
                    cv_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(cv_image)
                    self.display_image(pil_image)
                    return
                
                # 处理第一个二维码
                data = qr_codes[0].data.decode('utf-8')
                self.process_qr_data(data)
                
                # 在图片上标记二维码
                for qr in qr_codes:
                    points = qr.polygon
                    if len(points) == 4:
                        pts = [(p.x, p.y) for p in points]
                        pts = np.array(pts, dtype=np.int32)
                        cv2.polylines(image, [pts], True, (0, 255, 0), 2)
                
                # 显示图片
                cv_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(cv_image)
                self.display_image(pil_image)
                
            except Exception as e:
                messagebox.showerror("处理错误", str(e))
    
    def display_image(self, pil_image):
        """显示图片到预览区域"""
        # 调整图片大小以适应预览区域
        w, h = pil_image.size
        preview_w = self.preview_frame.winfo_width() or 400
        preview_h = self.preview_frame.winfo_height() or 400
        # 检查图片是否需要缩放
        # 如果图片太大，需要缩小以适应预览区域
        # 如果图片太小，保持原始大小以保持清晰度
        if w > preview_w or h > preview_h:
            # 图片需要缩小
            print(f"调整图片大小从 {w}x{h} 到适合预览区域 {preview_w}x{preview_h}")
        else:
            # 图片足够小，保持原始大小
            preview_w = w
            preview_h = h
            print(f"图片大小 {w}x{h} 适合预览区域，保持原始大小")
        # 计算缩放比例
        scale = min(preview_w / w, preview_h / h)
        new_size = (int(w * scale), int(h * scale))
        
        # 缩放图片
        pil_image = pil_image.resize(new_size, Image.LANCZOS)
        
        # 显示到UI
        self.photo = ImageTk.PhotoImage(pil_image)
        self.preview_label.config(image=self.photo)
    
    def process_qr_data(self, data):
        """处理二维码数据"""
        if data:
            self.log_response(f"QR content length: {len(data)}, line count: {data.count('\n')+1}")
            # Log first 50 chars to check encoding
            self.log_response(f"Content start: {data[:50]}")
            # 清空现有内容
            self.result_text.delete(1.0, tk.END)
            
            # 确保完整插入所有内容
            self.result_text.insert(tk.END, data)
            
            # 滚动到顶部
            self.result_text.see("1.0")
            
            # 将二维码内容按行分割
            commands = [cmd.strip() for cmd in data.split('\n') if cmd.strip()]
            self.qr_commands = commands
            
            # 更新按钮状态
            self.update_send_button_state()
            
            self.log_response(self.texts['parsed_qr'] + str(len(commands)))
    
    def update_send_button_state(self):
        """更新发送按钮状态"""
        if self.is_connected and self.qr_commands:
            self.send_button.config(state=tk.NORMAL)
        else:
            self.send_button.config(state=tk.DISABLED)
    
    def send_qr_commands(self):
        """发送二维码解析出的指令"""
        if not self.is_connected:
            messagebox.showerror(self.texts["error_title"], self.texts["device_not_connected"])
            return
        
        if not self.qr_commands:
            messagebox.showinfo(self.texts["提示"], self.texts["no_commands"])
            return
        
        # 显示发送进度对话框
        progress_window = tk.Toplevel(self.root)
        progress_window.title("发送进度")
        progress_window.geometry("300x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text=self.texts["sending_commands"]).pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=len(self.qr_commands))
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_label = ttk.Label(progress_window, text="0/" + str(len(self.qr_commands)))
        status_label.pack(pady=5)
        
        cancel_button = ttk.Button(progress_window, text="取消", command=lambda: progress_window.destroy())
        cancel_button.pack(pady=10)
        
        # 禁用发送按钮
        self.send_button.config(state=tk.DISABLED)
        
        # 启动发送线程
        def send_thread():
            total = len(self.qr_commands)
            for i, cmd in enumerate(self.qr_commands):
                if not progress_window.winfo_exists() or not self.is_connected:
                    break
                
                # 更新进度
                progress_var.set(i+1)
                progress_window.after(0, lambda idx=i+1, tot=total: status_label.config(text=f"{idx}/{tot}"))
                
                # 发送命令
                self.send_command(cmd)
                
                # 等待发送和响应完成
                time.sleep(1)
            
            # 发送完成
            if progress_window.winfo_exists():
                progress_window.after(0, lambda: status_label.config(text=self.texts["sending_complete"]))
                progress_window.after(1000, progress_window.destroy)
            
            # 重新启用发送按钮
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
        
        threading.Thread(target=send_thread, daemon=True).start()
    
    def capture_screenshot(self):
        """Start screenshot function"""
        try:
            self.log_response(self.texts["screenshot_start"])
            
            # Minimize current window to view screen
            self.root.iconify()
            
            # Give user time to prepare
            time.sleep(0.5)
            
            # Start screenshot with current language texts
            screenshot_texts = {
                "select_area": self.texts["select_area"],
                "screenshot_error": self.texts["screenshot_error"]
            }
            start_screenshot(self.process_screenshot, texts=screenshot_texts)
        except Exception as e:
            self.log_response(self.texts["screenshot_fail"].format(str(e)))
            # Ensure window is restored
            self.root.deiconify()
    
    def process_screenshot(self, image):
        """处理截图中的二维码"""
        # 确保主窗口被恢复
        self.root.deiconify()
        
        # 检查图像是否有效
        if image is None:
            self.log_response(self.texts["screenshot_error"].format("截图失败或被取消"), "error")
            return
        
        try:
            # 将PIL图像转换为OpenCV格式
            cv_image = np.array(image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            # 显示预览
            self.display_image(image)
            
            # 检测二维码
            qr_codes = decode(cv_image)
            
            if not qr_codes:
                self.log_response(self.texts["qr_not_detected"], "error")
                return
            
            # 处理第一个二维码
            data = qr_codes[0].data.decode('utf-8')
            self.process_qr_data(data)
            
            # 在图像上标记二维码
            img_with_qr = cv_image.copy()
            for qr in qr_codes:
                # 获取二维码边界点
                points = qr.polygon
                if len(points) == 4:
                    pts = [(p.x, p.y) for p in points]
                    pts = np.array(pts, dtype=np.int32)
                    cv2.polylines(img_with_qr, [pts], True, (0, 255, 0), 2)
            
            # 转换回PIL格式并显示带标记的图像
            marked_image = Image.fromarray(cv2.cvtColor(img_with_qr, cv2.COLOR_BGR2RGB))
            self.display_image(marked_image)
            
            self.log_response(self.texts["qr_detected"], "success")
        except Exception as e:
            self.log_response(self.texts["screenshot_error"].format(str(e)), "error")
    
    def on_closing(self):
        """关闭应用程序"""
        self.running = False
        self.waveform_active = False
        
        # 停止所有计时器
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)
            self.update_timer_id = None
            
        # 关闭波形图
        self.stop_waveform()  # 确保音频流被正确关闭
        
        # 关闭摄像头
        if self.cap:
            self.cap.release()
            self.cap = None
            
        # 关闭串口
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
            
        # 释放PyAudio资源
        if hasattr(self, 'p') and self.p:
            self.p.terminate()
            self.p = None
            
        # 销毁窗口
        self.root.destroy()

    def update_waveform_tk(self):
        """使用tkinter的after方法更新波形图"""
        if not self.waveform_active:
            return
        
        try:
            if self.stream and self.stream.is_active():
                # 读取音频数据
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                # 将二进制数据转换为整数
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                if self.CHANNELS == 2:  # 双声道处理
                    # 分离左右声道
                    left_channel = audio_data[0::2]  # 偶数索引为左声道
                    right_channel = audio_data[1::2]  # 奇数索引为右声道
                    
                    # 更新绘图数据
                    self.lines[0].set_data(range(len(left_channel)), left_channel)
                    self.lines[1].set_data(range(len(right_channel)), right_channel)
                else:  # 单声道处理
                    self.lines[0].set_data(range(len(audio_data)), audio_data)
                
                # 刷新canvas
                self.canvas.draw_idle()
            
            # 再次安排更新 - 使用较短的时间间隔，但不要太短
            self.update_timer_id = self.root.after(20, self.update_waveform_tk)
        
        except Exception as e:
            self.log_response(f"{self.texts['waveform_update_error']} {str(e)}")
            # 如果出错，短暂暂停后重试
            if self.waveform_active:
                self.update_timer_id = self.root.after(100, self.update_waveform_tk)

if __name__ == "__main__":
    # 设置高DPI支持
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # 创建应用
    root = tk.Tk()
    app = SerialQRCodeApp(root)
    
    # 配置响应文本的标签
    app.response_text.tag_configure("sent", foreground="blue")
    app.response_text.tag_configure("received", foreground="green")
    
    # 设置关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 运行应用
    root.mainloop()
