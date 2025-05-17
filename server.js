const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { instrument } = require("@socket.io/admin-ui");
const { spawn } = require('child_process');
require('dotenv').config(); // 加载环境变量
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = new Server(server,{
  cors: {
    origin: true,
    credentials: true
  }
});
// Socket.IO Admin UI
instrument(io, {
  auth: false
});

// 设置静态文件目录
app.use(express.static('Static'));

// 使用中间件解析请求体
app.use(express.json());

// 定义 Python 解释器路径和脚本路径
const PYTHON_INTERPRETER = (process.env.PYTHON_INTERPRETER || 'env/python.exe'); // 默认使用当前目录下的 python.exe

// 定义不同主模式和子模式对应的 Python 脚本
const PYTHON_SCRIPTS = {
    train: {
        "真人": "RealPractice.py",
        "虚拟人物": "VirtualPractice.py",
        "练习模式": "TaiJiGuiderSJTU/main.py",
    },
    challenge: {
        "限时": "OriginTimedchallengeMode/TimedchallengeClass.py",
        "无尽": "EndlessChallengeMode/EndlessChallengeClass.py"
    },
    fitness: {
        "单人": "1pFitness.py",
        "多人": "2pFitness.py"
    }
};

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

app.post('/api/chat', async (req, res) => {
  const { prompt } = req.body;

  const response = await fetch('http://localhost:11434/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'deepseek-r1:14b',
      messages: [{ role: 'user', content: prompt }],
      stream: true,
    }),
  });

  // 直接转发响应头
  res.setHeader('Content-Type', response.headers.get('Content-Type') || 'application/octet-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  // 直接 pipe 响应体
  response.body.pipeTo(require('stream').Writable.toWeb(res)).catch(() => {
    res.end();
  });
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
    // const defaultRoom = socket.id; // 默认房间为自身 ID
    const defaultRoom = "room";
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

    // 添加获取进程状态的处理
    socket.on('get_process_status', () => {
        const room = connections.get(socket.id)?.room;
        if (!room) return;
        
        const status = pythonProcesses.has(room) ? '运行中' : '未运行';
        socket.emit('process_status', status);
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

        const scriptPath = path.join('python', PYTHON_SCRIPTS[mainMode]?.[subMode]);
        if (!scriptPath) {
            console.error(`未找到对应的脚本: mainMode=${mainMode}, subMode=${subMode}`);
            return;
        }

        const pythonProcess = spawn(PYTHON_INTERPRETER, [scriptPath]);
        pythonProcesses.set(room, pythonProcess);

        broadcastProcessStatus(room, '启动中');

        // 初始化缓冲区和帧状态
        let buffer = Buffer.alloc(0);  // 用于存储接收到的数据
        let frameState = null;  // 用于跟踪当前帧的处理状态

        pythonProcess.stdout.on('data', (chunk) => {
            // console.log('收到数据块，长度:', chunk.length);
            // 将新接收的数据追加到缓冲区
            buffer = Buffer.concat([buffer, chunk]);
            // console.log('当前缓冲区总长度:', buffer.length);
            // 只要缓冲区还有数据就继续处理
            while (buffer.length > 0) {
                // 第一步：查找帧标记
                if (!frameState) {
                    // TODO: 可以将标记字符串定义为常量，提高复用性
                    const marker = Buffer.from('---FRAME---\n');
                    const markerIndex = buffer.indexOf(marker);
                    // console.log('查找帧标记:', markerIndex !== -1 ? '找到位置:' + markerIndex : '未找到');
                    // 优化点：可以缓存marker.length避免重复计算
                    if (markerIndex === -1) break;  // 没找到标记，等待更多数据

                    // 移除标记之前的数据和标记本身
                    buffer = buffer.slice(markerIndex + marker.length);
                    // 初始化新帧的状态
                    frameState = {
                        header: null,           // 帧头信息
                        expectedLength: 0,      // 预期的数据长度
                        receivedBuffer: []      // 接收到的数据缓冲区
                    };
                }

                // 第二步：解析帧头
                if (frameState && !frameState.header) {
                    const newlineIndex = buffer.indexOf(0x0A);  // 查找换行符
                    // console.log('查找帧头结束符:', newlineIndex !== -1 ? '找到位置:' + newlineIndex : '未找到');
                    if (newlineIndex === -1) break;  // 帧头不完整，等待更多数据

                    // 提取并解析帧头
                    const headerStr = buffer.slice(0, newlineIndex).toString('utf8');
                    buffer = buffer.slice(newlineIndex + 1);

                    try {
                        frameState.header = JSON.parse(headerStr);
                        // console.log('解析到的帧头:', headerStr);
                        // 处理控制帧
                        if (frameState.header.type === 'control') {
                            // console.log('解析到控制帧:', headerStr);
                            io.to(room).emit('control', frameState.header);
                            frameState = null;
                            continue;
                        }else if (frameState.header.type === 'image') {
                            frameState.expectedLength = frameState.header.length;
                            frameState.receivedLength = 0;
                        } else {
                            console.warn('未知帧类型：', frameState.header.type);
                            frameState = null;
                        }
                    } catch (err) {
                        console.error('解析帧头失败：', err);
                        frameState = null;
                    }
                }

                // 第三步：收集图像数据
                if (frameState?.header?.type === 'image') {
                    // 计算还需要接收的数据长度
                    const remaining = frameState.expectedLength - frameState.receivedLength;
                    const toTake = Math.min(buffer.length, remaining);
                    // console.log('接收图像数据片段:', toTake, '字节');
                    // 将数据添加到帧缓冲区
                    frameState.receivedBuffer.push(buffer.slice(0, toTake));
                    frameState.receivedLength += toTake;
                    buffer = buffer.slice(toTake);

                    // 检查是否接收完整帧
                    if (frameState.receivedLength >= frameState.expectedLength) {
                        // 合并所有接收到的数据块
                        const imageBuffer = Buffer.concat(frameState.receivedBuffer);
                        // 发送完整的图像帧
                        io.to(room).emit('frame', imageBuffer);
                        frameState = null;
                    }
                } else {
                    break;  // 等待下一个帧
                }
            }
        });


        pythonProcess.stderr.on('data', (data) => {
            console.error(`Python脚本错误 (${room}): ${data}`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Python脚本退出 (${room})，代码: ${code}`);
            pythonProcesses.delete(room);
            broadcastProcessStatus(room, '未运行');
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


