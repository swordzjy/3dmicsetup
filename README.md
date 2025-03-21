# 3dmicsetup
# 3DMIC串口设备管理工具

这是一个用于管理3DMIC串口设备的工具，支持二维码扫描和指令发送。

## 功能特点

- 自动检测和连接3DMIC串口设备
- 通过摄像头扫描二维码
- 支持从文件加载二维码图像
- 屏幕截图功能，可截取屏幕上的二维码
- 解析二维码内容并发送指令到设备
- 手动输入和发送指令
- 实时显示设备响应信息

## 使用要求

- Python 3.6+
- 所需库：见`app/requirement.txt`

## 安装方法

1. 克隆本仓库
2. 安装依赖库：
   ```
   pip install -r app/requirement.txt
   ```
3. 运行程序：
   ```
   python app/3dmicsetup.py
   ```

## 使用说明

1. 启动程序后，将自动检测并尝试连接3DMIC设备
2. 如未自动连接，可从下拉列表选择设备并点击"连接"按钮
3. 连接成功后，可通过以下方式发送指令：
   - 使用摄像头扫描二维码
   - 选择包含二维码的图片文件
   - 使用屏幕截图功能截取屏幕上的二维码
   - 在命令输入框中手动输入指令

## 许可证

[MIT](https://opensource.org/licenses/MIT)