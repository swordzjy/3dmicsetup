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

class SerialQRCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tradio 3D麦克风")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 设备变量
        self.serial_port = None
        self.is_connected = False
        self.default_port = None  # 默认麦克风设备
        self.command_queue = queue.Queue()
        self.response_buffer = ""
        
        # 创建界面
        self.create_ui()
        
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
        
        # 状态栏
        self.status_frame = ttk.Frame(main_frame, padding="5")
        self.status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(self.status_frame, text="未连接")
        self.status_label.pack(side=tk.LEFT)
        
        self.port_combo = ttk.Combobox(self.status_frame, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        
        self.baudrate_combo = ttk.Combobox(self.status_frame, width=10)
        self.baudrate_combo.pack(side=tk.LEFT, padx=5)
        self.baudrate_combo['values'] = [9600, 19200, 38400, 57600, 115200]
        self.baudrate_combo.current(4)
        
        self.dtr_var = tk.BooleanVar(value=True)
        self.dtr_check = ttk.Checkbutton(self.status_frame, text="DTR", variable=self.dtr_var)
        self.dtr_check.pack(side=tk.LEFT, padx=5)
        
        self.connect_button = ttk.Button(self.status_frame, text="连接", command=self.toggle_connection)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(self.status_frame, text="刷新端口", command=self.refresh_ports)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 二维码扫描区域
        qr_frame = ttk.LabelFrame(main_frame, text="二维码扫描", padding="10")
        qr_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        qr_buttons_frame = ttk.Frame(qr_frame)
        qr_buttons_frame.pack(fill=tk.X)
        
        self.camera_button = ttk.Button(qr_buttons_frame, text="打开摄像头", command=self.toggle_camera)
        self.camera_button.pack(side=tk.LEFT, padx=5)
        
        self.file_button = ttk.Button(qr_buttons_frame, text="选择图片", command=self.select_image)
        self.file_button.pack(side=tk.LEFT, padx=5)
        
        # 添加截图按钮
        self.screenshot_button = ttk.Button(
            qr_buttons_frame,  # 确保这个frame已经在您的代码中定义
            text="屏幕截图", 
            command=self.capture_screenshot
        )
        self.screenshot_button.pack(side=tk.LEFT, padx=5)
        
        # 预览区域
        self.preview_frame = ttk.Frame(qr_frame, height=300)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # 二维码解析结果
        result_frame = ttk.LabelFrame(main_frame, text="二维码内容", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.result_text = tk.Text(result_frame, height=5, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        self.send_button = ttk.Button(result_frame, text="发送指令到设备", command=self.send_qr_commands, state=tk.DISABLED)
        self.send_button.pack(pady=5)
        
        # 响应显示区域
        response_frame = ttk.LabelFrame(main_frame, text="设备响应", padding="10")
        response_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.response_text = tk.Text(response_frame, height=10, wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True)
        self.response_text.config(state=tk.DISABLED)
        
        response_scrollbar = ttk.Scrollbar(self.response_text, orient=tk.VERTICAL, command=self.response_text.yview)
        response_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.response_text.config(yscrollcommand=response_scrollbar.set)
        
        self.clear_button = ttk.Button(response_frame, text="清除", command=self.clear_response)
        self.clear_button.pack(pady=5)
        
        # 手动命令输入
        cmd_frame = ttk.Frame(main_frame, padding="10")
        cmd_frame.pack(fill=tk.X, pady=5)
        
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.cmd_button = ttk.Button(cmd_frame, text="发送", command=self.send_manual_command, state=tk.DISABLED)
        self.cmd_button.pack(side=tk.LEFT, padx=5)
        
        self.cmd_entry.bind("<Return>", lambda e: self.send_manual_command())
        
        # 初始化端口列表
        self.refresh_ports()
        
        # 摄像头变量
        self.cap = None
        self.camera_active = False
        
        # 解析到的二维码命令
        self.qr_commands = []
        
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
        if not self.is_connected and self.default_port:
            self.log_response(f"尝试自动连接麦克风设备: {self.default_port}")
            try:
                self.connect_serial()
            except Exception as e:
                self.log_response(f"自动连接失败: {str(e)}")
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.is_connected:
            self.disconnect_serial()
        else:
            self.connect_serial()
    
    def connect_serial(self):
        """连接设备"""
        port = self.port_combo.get()
        baudrate = int(self.baudrate_combo.get())
        
        if not port:
            messagebox.showerror("错误", "请选择设备")
            return
        
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            
            # 设置DTR信号
            if self.dtr_var.get():
                self.serial_port.setDTR(True)
            
            self.is_connected = True
            self.connect_button.config(text="断开")
            self.status_label.config(text=f"已连接 {port}")
            self.cmd_button.config(state=tk.NORMAL)
            self.update_send_button_state()
            
            self.log_response(f"成功连接到设备 {port} (波特率: {baudrate})")
            
        except Exception as e:
            messagebox.showerror("连接错误", str(e))
            self.log_response(f"连接错误: {str(e)}")
    
    def disconnect_serial(self):
        """断开设备连接"""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception as e:
                self.log_response(f"断开连接错误: {str(e)}")
        
        self.is_connected = False
        self.connect_button.config(text="连接")
        self.status_label.config(text="未连接")
        self.cmd_button.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.log_response("设备连接已断开")
    
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
                    self.log_response(f"读取错误: {str(e)}")
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
            messagebox.showerror("错误", "设备未连接")
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
                        self.log_response(f"发送: {command}", is_sent=True)
                        
                        # 等待一段时间，给设备处理时间
                        time.sleep(0.5)
                        
                    except Exception as e:
                        self.log_response(f"发送失败: {str(e)}")
                        if "device disconnected" in str(e) or "port is closed" in str(e):
                            self.root.after(0, self.handle_disconnect)
                    
                    finally:
                        self.command_queue.task_done()
            except Exception as e:
                print(f"命令处理错误: {str(e)}")
            
            # 短暂休眠
            time.sleep(0.01)
    
    def log_response(self, message, is_sent=False):
        """在响应区域记录消息"""
        def _update():
            self.response_text.config(state=tk.NORMAL)
            timestamp = time.strftime("%H:%M:%S")
            
            if is_sent:
                self.response_text.insert(tk.END, f"[{timestamp}] {message}\n", "sent")
            else:
                self.response_text.insert(tk.END, f"[{timestamp}] {message}\n", "received")
            
            self.response_text.see(tk.END)
            self.response_text.config(state=tk.DISABLED)
        
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
        preview_h = self.preview_frame.winfo_height() or 300
        
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
            # 将二维码内容按行分割
            commands = [cmd.strip() for cmd in data.split('\n') if cmd.strip()]
            self.qr_commands = commands
            
            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, data)
            
            # 更新按钮状态
            self.update_send_button_state()
            
            self.log_response(f"已解析二维码，包含 {len(commands)} 条指令")
    
    def update_send_button_state(self):
        """更新发送按钮状态"""
        if self.is_connected and self.qr_commands:
            self.send_button.config(state=tk.NORMAL)
        else:
            self.send_button.config(state=tk.DISABLED)
    
    def send_qr_commands(self):
        """发送二维码解析出的指令"""
        if not self.is_connected:
            messagebox.showerror("错误", "设备未连接")
            return
        
        if not self.qr_commands:
            messagebox.showinfo("提示", "没有可发送的指令")
            return
        
        # 显示发送进度对话框
        progress_window = tk.Toplevel(self.root)
        progress_window.title("发送进度")
        progress_window.geometry("300x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="正在发送指令...").pack(pady=10)
        
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
                progress_window.after(0, lambda: status_label.config(text="发送完成"))
                progress_window.after(1000, progress_window.destroy)
            
            # 重新启用发送按钮
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
        
        threading.Thread(target=send_thread, daemon=True).start()
    
    def capture_screenshot(self):
        """启动截图功能"""
        try:
            self.log_response("正在启动屏幕截图功能...")
            
            # 最小化当前窗口以便查看屏幕
            self.root.iconify()
            
            # 给用户一点时间准备
            time.sleep(0.5)
            
            # 启动截图
            start_screenshot(self.process_screenshot)
        except Exception as e:
            self.log_response(f"启动截图功能失败: {str(e)}", "error")
            # 确保窗口被恢复
            self.root.deiconify()
    
    def process_screenshot(self, image):
        """处理截图中的二维码"""
        # 确保主窗口被恢复
        self.root.deiconify()
        
        # 检查图像是否有效
        if image is None:
            self.log_response("截图失败或被取消", "error")
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
                self.log_response("未在截图中检测到二维码", "error")
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
            
            self.log_response(f"成功从截图中检测到二维码", "success")
        except Exception as e:
            self.log_response(f"处理截图时出错: {str(e)}", "error")
    
    def on_closing(self):
        """关闭应用程序"""
        self.running = False
        if self.cap:
            self.cap.release()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.destroy()

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
