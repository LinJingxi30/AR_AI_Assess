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
const PYTHON_SCRIPT_PATH = 'TimedChallengeMode/TimedChallengeClass.py';

// 定义不同主模式和子模式对应的 Python 脚本
const PYTHON_SCRIPTS = {
    train: {
        "真人": "RealPracticeMode/RealPracticeClass.py",
        "虚拟人物": "VirtualPracticeMode/VirtualPracticeClass.py"
    },
    challenge: {
        "限时": "TimedchallengeMode/TimedchallengeClass.py",
        "无尽": "EndlessChallengeMode/EndlessChallengeClass.py"
    },
    fitness: {
        // "单人": "1pFitnessMode/1pFitnessClass.py",
        "单人": "1pFitness.py",
        "多人": "2pFitness.py"
    }
};

let pythonProcess; // 保存 Python 进程实例
const pythonProcesses = new Map(); // 存储每个房间的 Python 子进程

const connections = new Map(); // 存储连接信息

// 获取所有连接信息
app.get('/connections', (req, res) => {
    const connectionList = Array.from(connections.entries()).map(([id, info]) => ({
        id,
        room: info.room,
    }));
    res.json({ connections: connectionList });
});

// 更新连接的房间并通知对应的 socket
app.post('/update_room', (req, res) => {
    const { id, room } = req.body;
    if (!connections.has(id)) {
        return res.status(404).json({ error: 'Socket ID not found' });
    }
    const socket = io.sockets.sockets.get(id);
    if (!socket) {
        return res.status(404).json({ error: 'Socket not connected' });
    }
    const currentRoom = connections.get(id).room;
    if (currentRoom) {
        socket.leave(currentRoom); // 离开当前房间
    }
    connections.get(id).room = room;
    socket.join(room); // 加入新房间
    socket.emit('update_room', room); // 通知对应的 socket
    res.json({ success: true });
});

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
    socket.on('start_capture', ({ mainMode, subMode }) => {
        const room = connections.get(socket.id)?.room;
        if (!room) return;

        console.log(`Socket ${socket.id} requested to start capture in room: ${room}, mainMode: ${mainMode}, subMode: ${subMode}`);
        
        if (pythonProcesses.has(room)) {
            broadcastProcessStatus(room, '已启动');
            return;
        }

        const scriptPath = PYTHON_SCRIPTS[mainMode]?.[subMode];
        if (!scriptPath) {
            console.error(`未找到对应的脚本: mainMode=${mainMode}, subMode=${subMode}`);
            return;
        }

        const pythonProcess = spawn(PYTHON_INTERPRETER, [scriptPath]);
        pythonProcesses.set(room, pythonProcess);

        broadcastProcessStatus(room, '启动中');
        let chunks = []
        pythonProcess.stdout.on('data', (data) => {
            const uintArray = new Uint8Array(data);
            // 检查 JPEG 文件头
            if (uintArray[0] === 0xFF && uintArray[1] === 0xD8) {
                console.log("检测到 JPEG 文件头，开始合并数据块");

                // 合并当前的 chunks 数组并发送
                if (chunks.length > 0) {
                    const completeImage = Buffer.concat(chunks);
                    io.to(room).emit('frame', completeImage);
                    // 清空数组以便接收新的图像
                    chunks = [];
                }
            }

            // 将数据块推入数组
            chunks.push(data);
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


