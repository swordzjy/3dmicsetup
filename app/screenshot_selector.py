import tkinter as tk
from PIL import Image, ImageTk
import pyautogui
import threading
import time

class ScreenshotSelector:
    def __init__(self, callback, instruction_text=None):
        """
        初始化截图选择器
        
        Args:
            callback: 截图完成后的回调函数，将接收截图图像作为参数
            instruction_text: Text to show as instruction (supports different languages)
        """
        self.callback = callback
        self.instruction_text = instruction_text or "Click and drag to select area, ESC to cancel"
    
        self.root = None
        self.canvas = None
        self.rect_id = None
        self.start_x = 0
        self.start_y = 0
        self.current_x = 0
        self.current_y = 0
        self.is_drawing = False
        self.screenshot = None
        self.tk_image = None
        
    def take_screenshot(self):
        """开始截图过程"""
        try:
            # 获取全屏截图
            self.screenshot = pyautogui.screenshot()
            screenshot_width, screenshot_height = self.screenshot.size
            
            # 创建全屏窗口
            self.root = tk.Toplevel()  # 使用Toplevel而不是Tk
            self.root.title("截图选择")
            self.root.attributes('-fullscreen', True)
            self.root.attributes('-alpha', 0.3)  # 半透明
            self.root.attributes('-topmost', True)
            
            # 创建Canvas用于绘制选择框
            self.canvas = tk.Canvas(self.root, width=screenshot_width, height=screenshot_height, highlightthickness=0)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            # 将截图转换为PhotoImage并保持引用
            self.tk_image = ImageTk.PhotoImage(self.screenshot)
            
            # 将图像显示在画布上
            self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
            
            # 绑定鼠标事件
            self.canvas.bind("<ButtonPress-1>", self.on_press)
            self.canvas.bind("<B1-Motion>", self.on_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_release)
            
            # 绑定键盘事件（ESC键退出）
            self.root.bind("<Escape>", lambda e: self.root.destroy())
            
            # 显示提示信息
            self.canvas.create_text(
                screenshot_width // 2, 
                30, 
                text=self.instruction_text, 
                fill="white", 
                font=("Arial", 16)
            )
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"截图过程发生错误: {str(e)}")
            if self.callback:
                self.callback(None)
    
    def on_press(self, event):
        """鼠标按下事件"""
        # 记录起始位置
        self.is_drawing = True
        self.start_x = event.x
        self.start_y = event.y
        self.current_x = event.x
        self.current_y = event.y
        
        # 创建初始选择框
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.current_x, self.current_y,
            outline="red", width=2
        )
    
    def on_drag(self, event):
        """鼠标拖动事件"""
        if self.is_drawing:
            # 更新当前位置
            self.current_x = event.x
            self.current_y = event.y
            
            # 更新选择框
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, self.current_x, self.current_y)
    
    def on_release(self, event):
        """鼠标释放事件 - 完成截图"""
        if self.is_drawing:
            self.is_drawing = False
            self.current_x = event.x
            self.current_y = event.y
            
            # 确保坐标是按左上角到右下角排序的
            left = min(self.start_x, self.current_x)
            top = min(self.start_y, self.current_y)
            right = max(self.start_x, self.current_x)
            bottom = max(self.start_y, self.current_y)
            
            # 裁剪选择区域
            if right > left + 10 and bottom > top + 10:  # 确保选择区域足够大
                try:
                    cropped = self.screenshot.crop((left, top, right, bottom))
                    self.root.destroy()
                    
                    # 调用回调函数
                    if self.callback:
                        self.callback(cropped)
                except Exception as e:
                    print(f"裁剪图像时出错: {str(e)}")
                    self.root.destroy()
                    if self.callback:
                        self.callback(None)
            else:
                # 选择区域太小，清除选择框
                self.canvas.delete(self.rect_id)
                self.rect_id = None

def start_screenshot(callback, instruction_text=None):
    """
    启动截图功能的便捷方法
    
    Args:
        callback: 截图完成后的回调函数
        instruction_text: Text to show as instruction (supports different languages)
    """
    try:
        selector = ScreenshotSelector(callback, instruction_text)
        thread = threading.Thread(target=selector.take_screenshot, daemon=True)
        thread.start()
    except Exception as e:
        print(f"启动截图线程时出错: {str(e)}")
        callback(None)

def capture_screenshot(self):
    """Start screenshot function"""
    try:
        self.log_response(self.texts["screenshot_start"])
        
        # Minimize current window to view screen
        self.root.iconify()
        
        # Give user time to prepare
        time.sleep(0.5)
        
        # Start screenshot with current language instruction text
        start_screenshot(self.process_screenshot, self.texts["screenshot_instruction"])
    except Exception as e:
        self.log_response(self.texts["screenshot_fail"].format(str(e)))
        # Ensure window is restored
        self.root.deiconify()

LANGUAGES = {
    "en": {
        # ... existing entries ...
        "screenshot_instruction": "Click and drag to select area, release to capture, ESC to cancel",
        "screenshot_start": "Starting screenshot function...",
        "screenshot_fail": "Failed to start screenshot function: {}",
    },
    "zh": {
        # ... existing entries ...
        "screenshot_instruction": "按住鼠标左键并拖动选择区域，松开完成截图，ESC键取消",
        "screenshot_start": "正在启动截图功能...",
        "screenshot_fail": "启动截图功能失败: {}",
    }
}
