const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

// 设置静态文件目录
app.use(express.static('Static'));

// 使用中间件解析请求体
app.use(express.json());

// 定义 Python 脚本路径
const PYTHON_SCRIPT_PATH = 'PracticeMode/RPClass.py';

let pythonProcess; // 保存 Python 进程实例

// 添加 POST 路由
app.post('/start_capture', (req, res) => {
    if (pythonProcess) {
        return res.status(400).json({ status: 'error', message: 'Capture already started' });
    }

    // 启动 Python 脚本
    pythonProcess = spawn('./venv/Scripts/python.exe', [PYTHON_SCRIPT_PATH]);

    // 从 Python 脚本接收数据
    pythonProcess.stdout.on('data', (data) => {
        // console.log(`Python脚本输出: ${data}`);
        io.emit('frame', data.toString('base64')); // 假设画面数据是二进制格式
    });

    // 处理错误
    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python脚本错误: ${data}`);
    });

    // Python 脚本结束时
    pythonProcess.on('close', (code) => {
        console.log(`Python脚本退出，代码: ${code}`);
        pythonProcess = null; // 清除进程实例
    });

    res.json({ status: 'success', message: 'Capture started' });
});

app.post('/stop_capture', (req, res) => {
    if (!pythonProcess) {
        return res.status(400).json({ status: 'error', message: 'No capture to stop' });
    }

    // 停止 Python 脚本
    pythonProcess.kill();
    pythonProcess = null;

    res.json({ status: 'success', message: 'Capture stopped' });
});

// Socket.IO 连接处理
io.on('connection', (socket) => {
    console.log(`A user connected: ${socket.id}`);

    socket.on('custom', (msg) => {
        console.log(`Message received from ${socket.id}:`, msg);
        io.emit('message', msg); // 广播消息
    });

    socket.on('disconnect', () => {
        console.log(`A user disconnected: ${socket.id}`);
    });
});

// 启动服务器
const PORT = 8000;
server.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
