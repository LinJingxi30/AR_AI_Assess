const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');
require('dotenv').config(); // 加载环境变量

const app = express();
const server = http.createServer(app);
const io = new Server(server);

// 设置静态文件目录
app.use(express.static('Static'));

// 使用中间件解析请求体
app.use(express.json());

// 定义 Python 解释器路径和脚本路径
const PYTHON_INTERPRETER = process.env.PYTHON_INTERPRETER || 'python3';
const PYTHON_SCRIPT_PATH = 'Main.py';

let pythonProcess; // 保存 Python 进程实例
const pythonProcesses = new Map(); // 存储每个房间的 Python 子进程

const connections = new Map(); // 存储连接信息

// 广播连接信息到 admin 房间
function broadcastConnections() {
    const connectionList = Array.from(connections.entries()).map(([id, info]) => ({
        id,
        room: info.room,
    }));
    io.to('admin').emit('update_connections', connectionList);
}

// 广播子进程状态到房间
function broadcastProcessStatus(room, status) {
    io.to(room).emit('process_status', status);
}

// 添加 POST 路由
app.post('/start_capture', (req, res) => {
    if (pythonProcess) {
        return res.status(400).json({ status: 'error', message: 'Capture already started' });
    }

    // 启动 Python 脚本
    pythonProcess = spawn(PYTHON_INTERPRETER, [PYTHON_SCRIPT_PATH]);

    // 从 Python 脚本接收数据
    pythonProcess.stdout.on('data', (data) => {
        //  console.log(`Python脚本输出: ${data}`);
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
        io.emit('capture_stopped', { message: 'Capture process has stopped', code }); // 广播通知
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

// 获取所有连接信息
app.get('/connections', (req, res) => {
    const connectionList = Array.from(connections.entries()).map(([id, info]) => ({
        id,
        room: info.room,
    }));
    res.json({ connections: connectionList });
});

// 更新连接的房间
app.post('/update_room', (req, res) => {
    const { id, room } = req.body;
    if (!connections.has(id)) {
        return res.status(404).json({ error: 'Socket ID not found' });
    }
    connections.get(id).room = room;
    io.sockets.sockets.get(id)?.join(room); // 加入新房间
    res.json({ success: true });
});

// Socket.IO 连接处理
io.on('connection', (socket) => {
    console.log(`A user connected: ${socket.id}`);
    const defaultRoom = socket.id; // 默认房间为自身 ID
    connections.set(socket.id, { room: defaultRoom });
    socket.join(defaultRoom);

    broadcastConnections(); // 广播更新

    // 处理加入房间的请求
    socket.on('join_room', ({ room }) => {
        const currentRoom = connections.get(socket.id)?.room;
        if (currentRoom) {
            socket.leave(currentRoom); // 离开当前房间
        }
        connections.get(socket.id).room = room;
        socket.join(room);
        console.log(`Socket ${socket.id} joined room: ${room}`);
        broadcastConnections(); // 广播更新
    });

    // 处理开始捕捉的请求
    socket.on('start_capture', ({ action }) => {
        const room = connections.get(socket.id)?.room;
        if (!room) return;
        console.log(`Socket ${socket.id} requested to start capture in room: ${room}`);
        if (pythonProcesses.has(room)) {
            broadcastProcessStatus(room, '已启动');
            return;
        }

        // const pythonProcess = spawn(PYTHON_INTERPRETER, [PYTHON_SCRIPT_PATH, action]);
        const pythonProcess = spawn(PYTHON_INTERPRETER, [PYTHON_SCRIPT_PATH]);
        pythonProcesses.set(room, pythonProcess);

        broadcastProcessStatus(room, '启动中');

        pythonProcess.stdout.on('data', (data) => {
            io.to(room).emit('frame', data.toString('base64'));
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Python脚本错误 (${room}): ${data}`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Python脚本退出 (${room})，代码: ${code}`);
            pythonProcesses.delete(room);
            broadcastProcessStatus(room, '已停止');
        });

        broadcastProcessStatus(room, '运行中');
    });

    // 处理停止捕捉的请求
    socket.on('stop_capture', () => {
        const room = connections.get(socket.id)?.room;
        if (!room || !pythonProcesses.has(room)) return;

        const pythonProcess = pythonProcesses.get(room);
        pythonProcess.kill();
        pythonProcesses.delete(room);

        broadcastProcessStatus(room, '已停止');
    });

    socket.on('disconnect', () => {
        console.log(`A user disconnected: ${socket.id}`);
        connections.delete(socket.id);
        broadcastConnections(); // 广播更新
    });
});

const PORT = 8000;
// 启动服务器

server.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});


