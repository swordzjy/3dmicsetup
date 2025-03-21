class SerialTerminal {
    constructor() {
        this.port = null;
        this.reader = null;
        this.writer = null;
        this.isConnected = false;
        this.lastResponse = '';
        this.responseHandler = null;
        this.readInProgress = false;
        this.responseCompleteTimer = null;
        this.qrcodeCommands = []; // 存储解析的二维码指令
        
        // DOM元素
        this.connectButton = document.getElementById('connect-button');
        this.sendButton = document.getElementById('send-button');
        this.commandInput = document.getElementById('command');
        this.logContent = document.getElementById('log-content');
        this.clearLogButton = document.getElementById('clear-log');
        this.baudrateSelect = document.getElementById('baudrate');
        this.dtrEnabled = document.getElementById('dtr-enabled');
        this.responseDisplay = document.getElementById('response-display');
        this.qrcodeFile = document.getElementById('qrcode-file');
        this.dragArea = document.getElementById('drag-area');
        this.previewContainer = document.getElementById('preview-container');
        this.qrcodeResult = document.getElementById('qrcode-result');
        this.sendQrcodeButton = document.getElementById('send-qrcode');

        // 绑定事件处理
        this.connectButton.addEventListener('click', () => this.toggleConnection());
        this.sendButton.addEventListener('click', () => this.sendCommand());
        this.clearLogButton.addEventListener('click', () => this.clearLog());
        this.commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendCommand();
        });
        
        // 二维码文件处理事件
        this.qrcodeFile.addEventListener('change', (e) => this.handleFileSelect(e));
        this.sendQrcodeButton.addEventListener('click', () => this.sendQrcodeCommands());
        
        // 拖放事件处理
        this.dragArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dragArea.classList.add('active');
        });
        
        this.dragArea.addEventListener('dragleave', () => {
            this.dragArea.classList.remove('active');
        });
        
        this.dragArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dragArea.classList.remove('active');
            if (e.dataTransfer.files.length) {
                this.handleFile(e.dataTransfer.files[0]);
            }
        });

        // 检查浏览器支持
        if (!navigator.serial) {
            this.addLog('您的浏览器不支持Web Serial API。请使用Chrome或Edge浏览器。', 'error');
            this.connectButton.disabled = true;
        }
    }

    async toggleConnection() {
        if (this.isConnected) {
            await this.disconnect();
        } else {
            await this.connect();
        }
    }

    async connect() {
        try {
            // 请求选择串口设备
            this.port = await navigator.serial.requestPort();
            
            // 打开串口连接
            await this.port.open({
                baudRate: parseInt(this.baudrateSelect.value),
                dataBits: 8,
                stopBits: 1,
                parity: 'none',
                flowControl: 'none'
            });
            
            // 设置DTR信号
            if (this.port.setSignals && this.dtrEnabled.checked) {
                await this.port.setSignals({ dataTerminalReady: true });
            }

            this.isConnected = true;
            this.connectButton.textContent = '断开连接';
            this.sendButton.disabled = false;
            this.sendQrcodeButton.disabled = this.qrcodeCommands.length === 0;
            this.addLog('设备已连接', 'success');

            // 开始读取数据
            this.startReading();

        } catch (error) {
            this.addLog(`连接失败: ${error.message}`, 'error');
        }
    }

    async disconnect() {
        try {
            // 先取消任何等待中的响应处理
            if (this.responseHandler) {
                const tempHandler = this.responseHandler;
                this.responseHandler = null;
                tempHandler('设备断开连接');
            }
            
            // 停止读取循环
            this.readInProgress = false;
            
            // 取消并释放读取器
            if (this.reader) {
                await this.reader.cancel();
                this.reader = null;
            }
            
            // 关闭端口
            if (this.port) {
                await this.port.close();
                this.port = null;
            }

            this.isConnected = false;
            this.connectButton.textContent = '连接设备';
            this.sendButton.disabled = true;
            this.sendQrcodeButton.disabled = true;
            this.addLog('设备已断开', 'info');
        } catch (error) {
            this.addLog(`断开连接错误: ${error.message}`, 'error');
        }
    }

    async startReading() {
        this.readInProgress = true;
        
        while (this.port && this.port.readable && this.readInProgress) {
            try {
                this.reader = this.port.readable.getReader();

                while (true) {
                    const { value, done } = await this.reader.read();
                    if (done) break;
                    
                    // 将接收到的数据转换为字符串
                    const text = new TextDecoder().decode(value);
                    
                    // 保存响应并显示
                    this.lastResponse += text;
                    
                    // 如果收到一定量的数据，且最近没有新数据，视为完整响应
                    clearTimeout(this.responseCompleteTimer);
                    this.responseCompleteTimer = setTimeout(() => {
                        if (this.lastResponse && this.responseHandler) {
                            const completeResponse = this.lastResponse.trim();
                            this.displayResponse(completeResponse);
                            this.addLog(`接收: ${completeResponse}`, 'received');
                            
                            // 调用响应处理函数
                            const tempHandler = this.responseHandler;
                            this.responseHandler = null;
                            tempHandler(completeResponse);
                            
                            // 重置响应缓存
                            this.lastResponse = '';
                        }
                    }, 300); // 300毫秒内没有新数据就认为响应完成
                }

            } catch (error) {
                if (!this.port || !this.readInProgress) {
                    // 正常断开连接的情况，不需要显示错误
                    break;
                }
                
                this.addLog(`读取错误: ${error.message}`, 'error');
                
                // 检查是否是设备断开错误
                if (error.message.includes('device disconnected') || 
                    error.message.includes('port is closed')) {
                    this.handleDisconnect();
                    break;
                }
                
                await new Promise(resolve => setTimeout(resolve, 1000)); // 避免无限循环
            } finally {
                if (this.reader) {
                    try {
                        await this.reader.releaseLock();
                    } catch (e) {
                        console.error('释放读取器失败:', e);
                    }
                }
            }
        }
        
        this.readInProgress = false;
    }

    async sendCommand(command = null) {
        if (!this.port || !this.isConnected) {
            this.addLog('设备未连接，无法发送命令', 'error');
            return false;
        }

        const cmdToSend = command || this.commandInput.value;
        if (!cmdToSend) return false;

        try {
            // 发送数据 - 添加正确的回车换行符
            const writer = this.port.writable.getWriter();
            const data = new TextEncoder().encode(cmdToSend + '\r\n');
            await writer.write(data);
            writer.releaseLock();

            this.addLog(`发送: ${cmdToSend}`, 'sent');
            if (!command) this.commandInput.value = '';

            // 等待响应
            await this.waitForResponse(3000);
            return true;

        } catch (error) {
            this.addLog(`发送失败: ${error.message}`, 'error');
            
            // 如果是设备断开导致的错误，更新状态
            if (error.message.includes('device disconnected') || 
                error.message.includes('port is closed')) {
                this.handleDisconnect();
            }
            return false;
        }
    }

    waitForResponse(timeout = 3000) {
        return new Promise((resolve) => {
            // 设置超时
            const timeoutId = setTimeout(() => {
                if (this.responseHandler) {
                    const tempHandler = this.responseHandler;
                    this.responseHandler = null;
                    this.displayResponse('响应超时', true);
                    this.addLog('读取响应超时', 'error');
                    tempHandler('响应超时');
                }
                resolve(false);
            }, timeout);

            // 设置响应处理函数
            this.responseHandler = (response) => {
                clearTimeout(timeoutId);
                resolve(true);
            };
        });
    }

    handleDisconnect() {
        this.isConnected = false;
        this.connectButton.textContent = '连接设备';
        this.sendButton.disabled = true;
        this.sendQrcodeButton.disabled = true;
        this.addLog('设备连接已断开', 'error');
        
        // 清理任何等待中的操作
        if (this.responseHandler) {
            const tempHandler = this.responseHandler;
            this.responseHandler = null;
            tempHandler('设备已断开');
        }
        
        // 重置状态
        this.readInProgress = false;
        this.reader = null;
        this.port = null;
    }

    displayResponse(response, isError = false) {
        const responseItem = document.createElement('div');
        responseItem.className = `response-item ${isError ? 'error' : ''}`;

        const timestamp = document.createElement('div');
        timestamp.className = 'response-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();

        const content = document.createElement('div');
        content.className = 'response-content';
        content.textContent = response;

        // 添加十六进制显示，帮助调试不可见字符
        const hexContent = document.createElement('div');
        hexContent.className = 'response-hex';
        hexContent.textContent = 'HEX: ' + Array.from(new TextEncoder().encode(response))
            .map(b => b.toString(16).padStart(2, '0'))
            .join(' ');

        responseItem.appendChild(timestamp);
        responseItem.appendChild(content);
        responseItem.appendChild(hexContent);

        // 添加到显示区域
        this.responseDisplay.appendChild(responseItem);
        // 滚动到底部
        this.responseDisplay.scrollTop = this.responseDisplay.scrollHeight;

        // 限制显示的响应数量（保留最新的20条）
        while (this.responseDisplay.children.length > 20) {
            this.responseDisplay.removeChild(this.responseDisplay.firstChild);
        }
    }

    addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = `[${timestamp}] ${message}`;
        this.logContent.appendChild(logEntry);
        this.logContent.scrollTop = this.logContent.scrollHeight;
    }

    clearLog() {
        this.logContent.innerHTML = '';
        this.responseDisplay.innerHTML = '';
    }

    // 二维码相关方法
    handleFileSelect(e) {
        if (e.target.files.length) {
            this.handleFile(e.target.files[0]);
        }
    }

    handleFile(file) {
        if (!file.type.match('image.*')) {
            this.addLog('请选择图片文件', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.previewContainer.innerHTML = '';
            const img = document.createElement('img');
            img.src = e.target.result;
            img.onload = () => this.decodeQRCode(img);
            this.previewContainer.appendChild(img);
        };
        reader.readAsDataURL(file);
    }

    decodeQRCode(img) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        // 设置canvas尺寸与图片一致
        canvas.width = img.width;
        canvas.height = img.height;
        
        // 在canvas上绘制图片
        context.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // 获取图像数据
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        
        // 使用jsQR库解码二维码
        const code = jsQR(imageData.data, imageData.width, imageData.height);
        
        if (code) {
            // 成功解码
            this.addLog('二维码解析成功', 'success');
            
            // 解析二维码内容为命令行列表
            this.parseQRCodeCommands(code.data);
        } else {
            this.addLog('无法解析二维码，请确保图片清晰', 'error');
            this.qrcodeResult.textContent = '解析失败';
            this.sendQrcodeButton.disabled = true;
            this.qrcodeCommands = [];
        }
    }

    parseQRCodeCommands(data) {
        // 将二维码内容按行分割为命令
        this.qrcodeCommands = data.split(/\r?\n/).filter(cmd => cmd.trim() !== '');
        
        // 显示解析结果
        this.qrcodeResult.textContent = this.qrcodeCommands.join('\n');
        
        // 更新按钮状态
        this.sendQrcodeButton.disabled = !(this.isConnected && this.qrcodeCommands.length > 0);
        
        this.addLog(`解析出 ${this.qrcodeCommands.length} 条指令`, 'info');
    }

    async sendQrcodeCommands() {
        if (!this.isConnected || this.qrcodeCommands.length === 0) {
            return;
        }
        
        this.sendQrcodeButton.disabled = true;
        this.addLog('开始发送二维码中的指令...', 'info');
        
        let successCount = 0;
        for (let i = 0; i < this.qrcodeCommands.length; i++) {
            const command = this.qrcodeCommands[i];
            this.addLog(`发送指令 ${i+1}/${this.qrcodeCommands.length}: ${command}`, 'info');
            
            // 发送命令并等待响应
            const success = await this.sendCommand(command);
            if (success) {
                successCount++;
            }
            
            // 每条命令之间等待一段时间，避免设备来不及处理
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        this.addLog(`二维码指令发送完成，成功: ${successCount}/${this.qrcodeCommands.length}`, 
            successCount === this.qrcodeCommands.length ? 'success' : 'info');
        this.sendQrcodeButton.disabled = false;
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new SerialTerminal();
});