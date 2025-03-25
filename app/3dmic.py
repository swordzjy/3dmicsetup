import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
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
import traceback
from datetime import datetime

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
        "screenshot_instruction": "Click and drag to select area, release to capture, ESC to cancel",
         "screenshot_error": "Error during screenshot process: {}",
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
        "qr_preview": "QR Preview",
        "operations_menu": "Operations",
        "language_name": "English"
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
        "screenshot_instruction": "点击并拖动选择区域, 松开完成截图, ESC取消",
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
        "qr_preview": "二维码预览",
        "operations_menu": "操作",
        "language_name": "中文"
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
         #创建了一个线程锁，可以在需要串口访问的地方使用
        self.serial_lock = threading.Lock()
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
        self.response_buffer = "Recieveing..."
        
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
           
    def create_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建菜单栏
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # 创建操作菜单
        operation_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.texts["operations_menu"], menu=operation_menu)
        
        # 添加菜单项
        operation_menu.add_command(label=self.texts["select_image"], command=self.select_image)
        operation_menu.add_command(label=self.texts["screenshot"], command=self.capture_screenshot)
        operation_menu.add_command(label=self.texts["open_camera"], command=self.toggle_camera)
        
        # 创建语言菜单
        language_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.texts["language"], menu=language_menu)
        
        # 为每种语言添加单选按钮
        self.lang_var = tk.StringVar(value=self.current_language)
        for lang_code, lang_data in LANGUAGES.items():
            language_menu.add_radiobutton(
                label=lang_data["language_name"],
                variable=self.lang_var,
                value=lang_code,
                command=self.change_language
            )
        
        # 配置主框架中的行列权重 - 调整权重使关键区域获得足够空间
        main_frame.columnconfigure(0, weight=1)  # 列可以扩展
        main_frame.rowconfigure(0, weight=0)  # 第一行 - 顶部操作栏（固定高度）
        main_frame.rowconfigure(1, weight=5)  # 第二行 - 波形图（较大权重）
        main_frame.rowconfigure(2, weight=5)  # 第三行 - 设备响应（较大权重，原本是二维码区域的位置）
        main_frame.rowconfigure(3, weight=0)  # 第四行 - 命令输入（固定高度）
        
        # 顶部操作栏 - 只保留状态标签和恢复按钮区域
        top_frame = ttk.Frame(main_frame, padding="5")
        top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # 配置top_frame内部布局
        top_frame.columnconfigure(0, weight=1)  # 状态标签 - 可以扩展
        top_frame.columnconfigure(1, weight=0)  # 恢复按钮 - 固定宽度
        
        # 状态标签
        self.status_label = ttk.Label(top_frame, text=self.texts["status_not_connected"])
        self.status_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        # 恢复按钮框架 (初始隐藏)
        self.restore_frame = ttk.Frame(top_frame)
        self.restore_frame.grid(row=0, column=1, sticky="e")
        self.restore_frame.grid_remove()  # 初始隐藏
        
        self.restore_button = ttk.Button(
            self.restore_frame, 
            text="恢复原始配置", 
            command=self.restore_original_config
        )
        self.restore_button.pack(side=tk.RIGHT, padx=5)
        
        # 波形图容器框架
        self.waveform_frame = ttk.LabelFrame(main_frame, text="", padding="1")
        self.waveform_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        # 设置最小高度
        self.waveform_frame.config(height=400, width=400)
        self.waveform_frame.pack_propagate(False)  # 确保高度固定，不会被子组件影响
        self.waveform_frame.grid_propagate(False)
        
        # 响应显示区域 - 直接放在第二行 (原第三行)
        self.response_frame = ttk.LabelFrame(main_frame, text=self.texts["device_response"], padding="10")
        self.response_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # 配置response_frame内部布局
        self.response_frame.columnconfigure(0, weight=1)
        self.response_frame.rowconfigure(0, weight=1)
        self.response_frame.rowconfigure(1, weight=0)
        self.response_frame.grid_propagate(False)
        
        # 修改文本框高度为更大的值
        self.response_text = tk.Text(self.response_frame, height=15, wrap=tk.WORD)
        self.response_text.grid(row=0, column=0, sticky="nsew")
        self.response_text.config(state=tk.DISABLED)
          # 创建响应文本框和滚动条
        self.response_text = scrolledtext.ScrolledText(
        self.response_frame, 
        height=10,  # 增加高度以显示更多内容
        wrap=tk.WORD
         )
        self.response_text.pack(fill='both', expand=True)
        # # 滚动条
        # response_scrollbar = ttk.Scrollbar(self.response_text, orient=tk.VERTICAL, command=self.response_text.yview)
        # response_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # self.response_text.config(yscrollcommand=response_scrollbar.set)
        
        self.clear_button = ttk.Button(self.response_frame, text=self.texts["clear"], command=self.clear_response)
        self.clear_button.grid(row=1, column=0, pady=5)
        
        # 手动命令输入 - 移到第三行 (原第四行)
        cmd_frame = ttk.Frame(main_frame, padding="5")
        cmd_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
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
        
        # 创建二维码相关组件，但不显示它们
        self.create_hidden_qr_components(main_frame)
        
        # 最后一次性强制所有组件更新
        for child in self.root.winfo_children():
            child.update_idletasks()
        
    def create_hidden_qr_components(self, main_frame):
        """创建但不显示二维码相关组件"""
        # 创建二维码区域，但不添加到网格
        self.qr_area_frame = ttk.Frame(main_frame)
        
        # 配置qr_area_frame内部布局
        self.qr_area_frame.columnconfigure(0, weight=2)
        self.qr_area_frame.columnconfigure(1, weight=8)
        self.qr_area_frame.rowconfigure(0, weight=1)
        
        # 预览区域
        self.preview_frame = ttk.LabelFrame(self.qr_area_frame, text=self.texts["qr_preview"], padding="5")
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.preview_frame.config(height=50, width=50)
        self.preview_frame.grid_propagate(False)
        
        # 创建一个固定大小的Label来显示图像
        self.preview_label = tk.Label(self.preview_frame, bg='white')
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初始化photo属性，避免图像被垃圾回收
        self.photo = None
        
        # 二维码内容区域
        self.result_frame = ttk.LabelFrame(self.qr_area_frame, text=self.texts["qr_content"], padding="10")
        self.result_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.result_frame.grid_propagate(False)
        
        # 配置result_frame内部布局
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)
        self.result_frame.rowconfigure(1, weight=0)
        
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
        self.send_button.config(state=tk.DISABLED)
    
    def change_language(self, event=None):
        """Change the application language"""
        lang = self.lang_var.get()
        print(f"切换语言到: {lang}")
        if lang in LANGUAGES and lang != self.current_language:
            print(f"当前语言: {self.current_language} -> 新语言: {lang}")
            self.current_language = lang
            self.texts = LANGUAGES[lang]
            self.update_ui_texts()
    
    def update_ui_texts(self):
        """Update all UI texts to the current language"""
        # Update window title
        self.root.title(self.texts["title"])
        
        try:
            # 重新创建整个菜单
            self.menubar.delete(0, tk.END)  # 清除现有菜单
            
            # 重新创建操作菜单
            operation_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label=self.texts["operations_menu"], menu=operation_menu)
            
            # 添加操作菜单项
            operation_menu.add_command(label=self.texts["select_image"], command=self.select_image)
            operation_menu.add_command(label=self.texts["screenshot"], command=self.capture_screenshot)
            operation_menu.add_command(
                label=self.texts["close_camera"] if self.camera_active else self.texts["open_camera"],
                command=self.toggle_camera
            )
            
            # 重新创建语言菜单
            language_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label=self.texts["language"], menu=language_menu)
            
            # 添加语言选项
            for lang_code, lang_data in LANGUAGES.items():
                language_menu.add_radiobutton(
                    label=lang_data["language_name"],
                    variable=self.lang_var,
                    value=lang_code,
                    command=self.change_language
                )
            
        except Exception as e:
            print(f"菜单更新错误: {str(e)}")
        
        # 更新其他UI元素...
        # 状态标签
        if self.is_connected and self.serial_port:
            self.status_label.config(text=self.texts["status_connected"].format(self.serial_port.port))
        else:
            self.status_label.config(text=self.texts["status_not_connected"])
        
        # 更新框架标题
        self.response_frame.config(text=self.texts["device_response"])
           # Update frame titles
        self.waveform_frame.config(text=self.texts["waveform"]) 
        # 更新按钮文本
        self.send_button.config(text=self.texts["send_command"])
        self.clear_button.config(text=self.texts["clear"])
        self.cmd_button.config(text=self.texts["send"])
    
    def audio_setup(self):
        """设置音频参数和Matplotlib波形图"""
        # 音频处理参数
        # 音频处理参数
        # CHUNK: 每次读取的音频帧大小，可选值如512, 1024, 2048, 4096等，值越大延迟越高但CPU占用更低
        self.CHUNK = 1024
        # FORMAT: 音频采样格式，可选值:
        # - pyaudio.paFloat32: 32位浮点
        # - pyaudio.paInt32: 32位整数
        # - pyaudio.paInt24: 24位整数
        # - pyaudio.paInt16: 16位整数(CD质量)
        # - pyaudio.paInt8: 8位整数
        # - pyaudio.paUInt8: 8位无符号整数
        self.FORMAT = pyaudio.paInt16
        # CHANNELS: 声道数，1=单声道，2=立体声
        self.CHANNELS = 2
        # RATE: 采样率(Hz)，常用值: 8000, 16000, 22050, 44100(CD质量), 48000, 96000
        self.RATE = 44100
        
        # 创建Matplotlib图表 - 使用两个子图
        self.fig = Figure(figsize=(5, 6), dpi=100)
        
        # 左声道子图
        self.ax_left = self.fig.add_subplot(211)  # 2行1列的第1个图
        self.ax_left.set_title(self.texts["left_channel"], loc='left')
        self.ax_left.set_ylim(-10000, 10000)
        self.ax_left.set_xlim(0, self.CHUNK)
        self.ax_left.grid(True)
        
        # 右声道子图
        self.ax_right = self.fig.add_subplot(212)  # 2行1列的第2个图
        self.ax_right.set_title(self.texts["right_channel"], loc='left')
        self.ax_right.set_ylim(-10000, 10000)
        self.ax_right.set_xlim(0, self.CHUNK)
        self.ax_right.grid(True)
        
        # 初始化线条
        self.line_left = self.ax_left.plot([], [], 'g-')[0]
        self.line_right = self.ax_right.plot([], [], 'r-')[0]
        
        # 调整子图间距
        self.fig.tight_layout(pad=3.0)
        
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
                            response = self.response_buffer.strip()
                            
                            # 检查是否正在等待备份数据
                            if hasattr(self, 'backup_complete') and not self.backup_complete.is_set():
                                print(f"收到响应数据: {response[:50]}...")  # 打印前50个字符用于调试
                                
                                # 如果是备份数据（包含配置信息）
                                if "ret:" in response and "OK" in response:
                                    print("检测到完整的备份数据")
                                    self.backup_data = response
                                    self.backup_complete.set()
                                else:
                                    print("不是备份数据，继续等待...")
                            else:
                                # 常规响应处理
                                self.log_response(response)
                            
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
                        time.sleep(0.05)
                        
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
    
    def log_response(self, text, is_sent=False):
        """记录响应到UI"""
        try:
            if not hasattr(self, 'response_text'):
                print("警告: response_text 未创建")
                return
            
            # 在UI线程中更新文本
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
            message = f"{timestamp}{text}\n"
            
            self.root.after(0, lambda: self._update_response_text(message))
        except Exception as e:
            print(f"记录响应出错: {str(e)}")

    def _update_response_text(self, message):
        """在UI线程中安全地更新响应文本"""
        try:
            self.response_text.insert(tk.END, message)
            self.response_text.see(tk.END)  # 滚动到最新内容
        except Exception as e:
            print(f"更新响应文本出错: {str(e)}")
    
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
        
        # 更新菜单项文本
        operation_menu = self.menubar.winfo_children()[0]  # 获取第一个子菜单
        if self.camera_active:
            operation_menu.entryconfig(2, label=self.texts["close_camera"])
        else:
            operation_menu.entryconfig(2, label=self.texts["open_camera"])
    
    def start_camera(self):
        """启动摄像头"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("错误", "无法打开摄像头")
                return
            
            self.camera_active = True
            
            # self.camera_button.config(text="关闭摄像头")
            self.update_camera_feed()
            
        except Exception as e:
            messagebox.showerror("摄像头错误", str(e))
    
    def stop_camera(self):
        """停止摄像头"""
        self.camera_active = False
        # self.camera_button.config(text="打开摄像头")
        
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
                    qr_valid = self.process_qr_data(data)
                    
                    # 只有当二维码格式有效时才停止摄像头
                    if qr_valid:
                        # 显示最后一帧（带有二维码标记）
                        cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(cv_image)
                        self.display_image(pil_image)
                        # 检测到有效二维码后停止摄像头
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
                    messagebox.showerror(self.texts["error_title"], "无法读取所选图片")
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
                qr_valid = self.process_qr_data(data)
                
                # 只有在二维码格式有效时才标记并显示
                if qr_valid:
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
        return  
         # 后续开发者模式下再显示图片和qr_content
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
            
            # 验证二维码格式是否正确
            # if not data.startswith("[3DMIC_PARAMETER]"):
            #     messagebox.showerror(self.texts["error_title"], "错误的二维码格式，二维码内容必须以[3DMIC_PARAMETER]开头")
            #     return False
            
            # 清空现有内容并保存二维码内容
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, data)
            
            # 将二维码内容按行分割
            commands = [cmd.strip() for cmd in data.split('\n') if cmd.strip()]
            self.qr_commands = commands
            print("got qr_commands:",self.qr_commands)
            
            # 备份当前配置并自动发送新配置
            if self.is_connected:
                if self.backup_mic_config():
                    # 添加恢复按钮到界面
                    self.show_restore_button()
                    
                    # 自动发送配置
                    self.log_response("检测到有效的麦克风配置，正在自动应用...")
                    self.send_qr_commands(auto_send=True)
                    
                    # 隐藏二维码相关区域，只显示响应区域
                    self.hide_qr_area()
                    
                    # # 扩大response区域
                    # self.expand_response_area()
                else:
                    messagebox.showwarning("警告", "无法备份当前配置，请手动点击发送按钮应用新配置")
                    # 保持原有界面布局
                    self.update_send_button_state()
            else:
                messagebox.showwarning("警告", "设备未连接，无法应用配置")
                self.update_send_button_state()
            
            return True
        
        return False
    
    def update_send_button_state(self):
        """更新发送按钮状态"""
        if self.is_connected and self.qr_commands:
            self.send_button.config(state=tk.NORMAL)
        else:
            self.send_button.config(state=tk.DISABLED)
    
    def send_qr_commands(self, auto_send=False):
        """发送二维码解析出的指令"""
        if not self.is_connected:
            messagebox.showerror(self.texts["error_title"], self.texts["device_not_connected"])
            return
        
        if not self.qr_commands:
            messagebox.showinfo("提示", self.texts["no_commands"])
            return
        
        # 自动发送模式下不显示进度窗口
        if not auto_send:
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
        
        # 发送命令函数
        def send_thread():
            total = len(self.qr_commands)
            for i, cmd in enumerate(self.qr_commands):
                if (not auto_send and not progress_window.winfo_exists()) or not self.is_connected:
                    break
                
                # 更新进度
                if not auto_send:
                    progress_var.set(i+1)
                    progress_window.after(0, lambda idx=i+1, tot=total: status_label.config(text=f"{idx}/{tot}"))
                
                # 发送命令
                self.send_command(cmd)
                
                # 等待发送和响应完成
                time.sleep(0.5)
            
            # 发送完成
            if not auto_send and progress_window.winfo_exists():
                progress_window.after(0, lambda: status_label.config(text=self.texts["sending_complete"]))
                progress_window.after(1000, progress_window.destroy)
            
                # 重新启用发送按钮
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
        
        # 启动发送线程
        threading.Thread(target=send_thread, daemon=True).start()
    
    def capture_screenshot(self):
        """Start screenshot function"""
        try:
            self.log_response(self.texts["screenshot_start"])
            
            # Minimize current window to view screen
            self.root.iconify()
            
            # Give user time to prepare
            time.sleep(0.5)
            
            self.root.after(100, lambda: start_screenshot(self.process_screenshot, instruction_text=self.texts["screenshot_instruction"]))
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
            self.log_response(self.texts["screenshot_error"].format("截图失败或被取消"))
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
                self.log_response(self.texts["qr_not_detected"])
                return
            
            # 处理第一个二维码
            data = qr_codes[0].data.decode('utf-8')
            qr_valid = self.process_qr_data(data)
            
            # 只有在二维码格式有效时才标记并显示
            if qr_valid:
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
            
                self.log_response(self.texts["qr_detected"])
        except Exception as e:
            self.log_response(self.texts["screenshot_error"].format(str(e)))
    
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
                    
                    # 更新左右声道的绘图数据
                    x_data = np.arange(len(left_channel))
                    self.line_left.set_data(x_data, left_channel)
                    self.line_right.set_data(x_data, right_channel)
                    
                    # 动态调整Y轴范围以适应数据
                    if len(left_channel) > 0:
                        max_val = max(np.max(np.abs(left_channel)), np.max(np.abs(right_channel)))
                        y_limit = max(10000, min(32000, max_val * 1.2))  # 给视觉上留一些余量
                        self.ax_left.set_ylim(-y_limit, y_limit)
                        self.ax_right.set_ylim(-y_limit, y_limit)
                else:  # 单声道处理
                    x_data = np.arange(len(audio_data))
                    self.line_left.set_data(x_data, audio_data)
                    self.line_right.set_data(x_data, np.zeros_like(audio_data))  # 右声道显示为0
                
                # 刷新canvas
                self.canvas.draw_idle()
            
            # 再次安排更新 - 使用较短的时间间隔
            self.update_timer_id = self.root.after(20, self.update_waveform_tk)
        
        except Exception as e:
            self.log_response(f"波形图更新错误: {str(e)}")
            # 如果出错，短暂暂停后重试
            if self.waveform_active:
                self.update_timer_id = self.root.after(100, self.update_waveform_tk)

    def backup_mic_config(self):
        """备份麦克风当前配置"""
        try:
            # 创建事件来等待响应完成
            self.backup_complete = threading.Event()
            self.backup_data = None
            
            print("开始备份配置...")
            
            # 使用现有的命令队列发送命令
            self.send_command("readallcfg")
            
            # 等待响应
            print("等待备份响应...")
            if not self.backup_complete.wait(10.0):
                print("警告: 备份操作超时")
                return False
            # 保存备份数据到backup_config
            if self.backup_data:
                self.backup_config = self.backup_data
                print(f"成功保存备份配置，长度: {len(self.backup_config)}")
            else:
                print("警告: 未能获取有效的备份数据")
                return False
            print(f"备份完成，数据长度: {len(self.backup_data) if self.backup_data else 0}")
            
        
            return True
        
        except Exception as e:
            print(f"备份配置出错: {str(e)}")
            # 确保恢复原始处理函数
            return False
        finally:
            # 清理事件对象
            if hasattr(self, 'backup_complete'):
                delattr(self, 'backup_complete')
    def hide_qr_area(self):
        """隐藏二维码区域"""
        if hasattr(self, 'qr_area_frame'):
            self.qr_area_frame.grid_remove()  # 不是destroy，而是从布局中移除，保留实例

    def expand_response_area(self):
        """扩大响应区域"""
        # 修改行权重，让响应区域占用原本二维码区域的空间
        main_frame = self.root.winfo_children()[0]  # 获取主框架
        main_frame.rowconfigure(2, weight=0)  # 二维码区域权重设为0
        main_frame.rowconfigure(3, weight=3)  # 增加响应区域的权重

    def show_restore_button(self):
        """显示恢复配置按钮"""
        # 创建一个框架来容纳恢复按钮
        if not hasattr(self, 'restore_frame'):
            main_frame = self.root.winfo_children()[0]
            self.restore_frame = ttk.Frame(main_frame, padding="5")
            self.restore_frame.grid(row=0, column=0, sticky="e", padx=5, pady=5)
            
            self.restore_button = ttk.Button(
                self.restore_frame, 
                text="恢复原始配置", 
                command=self.restore_original_config
            )
            self.restore_button.pack(side=tk.RIGHT, padx=5)
        else:
            # 如果已存在，只需要显示它
            self.restore_frame.grid()

    def restore_original_config(self):
        """恢复麦克风原始配置"""
        if not hasattr(self, 'backup_config') or not self.backup_config:
            messagebox.showwarning("警告", "没有可用的备份配置")
            return
        
        if not self.is_connected:
            messagebox.showerror(self.texts["error_title"], "设备未连接，无法恢复配置")
            return
        
        # 询问用户是否确定要恢复
        if messagebox.askyesno("确认", "确定要恢复麦克风原始配置吗？"):
            self.log_response("正在恢复麦克风原始配置...")
            
            # 发送备份的配置命令
 
            # 从备份数据中提取ret:后面的内容作为命令
            if "ret:" in self.backup_config:
                command = self.backup_config.split("ret:", 1)[1].strip()
                self.send_command(command)
                print(f"发送命令: {command}")
            else:
                self.send_command("readallcfg")
                print(f"发送命令: readallcfg")

            time.sleep(0.1)  # 短暂延迟确保命令被处理
            
            self.log_response("麦克风原始配置已恢复")
            
            # 可选：隐藏恢复按钮
            if hasattr(self, 'restore_frame'):
                self.restore_frame.grid_remove()

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
