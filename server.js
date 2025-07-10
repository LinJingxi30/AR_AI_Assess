const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { instrument } = require("@socket.io/admin-ui");
const { spawn } = require('child_process');
const bonjour = require('bonjour')();
require('dotenv').config(); // 加载环境变量
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const jwt = require('jsonwebtoken');
const fs = require('fs').promises;
// const sharp = require('sharp');
const dgram = require('dgram');
const UDPBroadcaster = require('./components/UDPBroadcaster');
const { startRtmpStreams } = require('./rtmpStreamer');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*',
        // credentials: true
        methods: ['GET', 'POST'],
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

async function getMergedPrompt(prompt, uuid) {
    try {
        // 并行读取文件
        // 并行读取文件，如果文件不存在则返回空字符串
        const [promptText1,promptText2, diffJson] = await Promise.all([
            fs.readFile(path.join(__dirname, 'Static/others/prompt1.txt'), 'utf8').catch(() => ''),
            fs.readFile(path.join(__dirname, 'Static/others/prompt2.txt'), 'utf8').catch(() => ''),
            fs.readFile(path.join(__dirname, `python/StdSportsResults/TaiJi/differences-${uuid}.json`), 'utf8').catch(() => '')
        ]);

        // 解析 differences.json
        let diffData = "";
        try {
            diffData = JSON.stringify(JSON.parse(diffJson), null, 2);
        } catch (err) {
            console.warn('解析 differences.json 失败:', err);
        }

        // 合并内容
        return promptText1 + "\n下面是标志动作差异的json数据:\n" + diffData + "\n" + promptText2;
    } catch (err) {
        console.error('读取提示文件失败:', err);
        return "";
    }
}

// 修改 chat API endpoint
app.post('/api/chat', async (req, res) => {
    const { prompt, uuid } = req.body;
    console.log('UUid:', uuid);
    try {
        const mergedPrompt = await getMergedPrompt(prompt, uuid);
        console.log('Merged Prompt:', mergedPrompt);

        const response = await fetch('http://ollama.chainpray.top:11434/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'deepseek-r1:14b',
                messages: [{ role: 'user', content: mergedPrompt }],
                stream: true,
            }),
        });

        res.setHeader('Content-Type', response.headers.get('Content-Type') || 'application/octet-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');

        response.body.pipeTo(require('stream').Writable.toWeb(res)).catch(() => {
            res.end();
        });
    } catch (err) {
        console.error('处理聊天请求失败:', err);
        res.status(500).json({ error: '内部服务器错误' });
    }
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
function broadcastProcessStatus(room) {
    let started = pythonProcesses.has(room) ? 1 : 0;
    let uuid = pythonProcesses.get(room)?.uniqueId || null;
    io.to(room).emit('process_status', {
        started,
        uuid
    });
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

        const started = pythonProcesses.has(room) ? 1 : 0;
        const uuid = pythonProcesses.get(room)?.uniqueId || null;
        socket.emit('process_status', { started, uuid });
    });

    // 处理开始捕捉的请求
    socket.on('start_capture', ({ mainMode, subMode }) => {
        const room = connections.get(socket.id)?.room;
        if (!room) return;

        console.log(`Socket ${socket.id} requested to start capture in room: ${room}, mainMode: ${mainMode}, subMode: ${subMode}`);

         // 广播 start_capture 事件到房间
        io.to(room).emit('start_capture', { mainMode, subMode });

        if (pythonProcesses.has(room)) {
            return;
        }

        // 判断对应模式是否存在
        if (!PYTHON_SCRIPTS[mainMode] || !PYTHON_SCRIPTS[mainMode][subMode]) {
            console.error(`模式 ${mainMode} 或 ${subMode} 不存在`);
            return;
        }
        const scriptPath = path.join('python', PYTHON_SCRIPTS[mainMode][subMode]);
        // 生成唯一ID
        const uniqueId = uuidv4();
        const pythonProcess = spawn(PYTHON_INTERPRETER, [
            scriptPath,
            '--unique_id', uniqueId
        ]);

        // 将 uniqueId 设置为 pythonProcess 的属性
        pythonProcess.uniqueId = uniqueId;

        pythonProcesses.set(room, pythonProcess);

        broadcastProcessStatus(room);  // 修改这里，传入 uniqueId

        // 初始化缓冲区和帧状态
        let buffer = Buffer.alloc(0);  // 用于存储接收到的数据
        let frameState = null;  // 用于跟踪当前帧的处理状态

        pythonProcess.stdout.on('data', async(chunk) => {
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
                        } else if (frameState.header.type === 'image') {
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
                        const imageBuffer = Buffer.concat(frameState.receivedBuffer);
                        // 使用 sharp 处理图像
                        try {
                            // const processedBuffer = await sharp(imageBuffer)
                            //     .resize(1080,720) // 降低分辨率
                            //     .jpeg({ quality: 60 }) // 使用 webp 格式并设置压缩质量
                            //     .toBuffer();

                            // 发送处理后的图像帧
                            io.to(room).emit('frame', imageBuffer);
                        } catch (err) {
                            console.error('图像处理失败:', err);
                            // 如果处理失败，发送原始图像
                            io.to(room).emit('frame', imageBuffer);
                        }
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
            broadcastProcessStatus(room);
        });
    });

    // 处理停止捕捉的请求
    socket.on('stop_capture', () => {
        const room = connections.get(socket.id)?.room;
        if (!room || !pythonProcesses.has(room)) return;

        const pythonProcess = pythonProcesses.get(room);
        pythonProcess.kill();
        pythonProcesses.delete(room);

        // broadcastProcessStatus(room);
    });

    socket.on('disconnect', () => {
        console.log(`A user disconnected: ${socket.id}`);
        connections.delete(socket.id);
        broadcastConnections(); // 广播更新
    });
});

const PORT = 8000;

// 创建并配置 UDP 广播器
const broadcaster = new UDPBroadcaster({
    port: 9999,
    interval: 1000,
    serviceName: 'arsport',
    servicePort: PORT
});

server.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    // 启动 UDP 广播
    broadcaster.start();

    // 注册 Bonjour/mDNS 服务
    // bonjour.publish({
    //     name: 'arsport',
    //     type: 'http',
    //     port: PORT,
    //     host: 'arsport.local', // 可选，不指定也可以
    // });
    console.log('mDNS service published as arsport.local');
});

// 在服务器关闭时停止广播
process.on('SIGINT', () => {
    broadcaster.stop();
    process.exit();
});

// const authRoutes = require('./routes/auth');
// const { authenticateToken, checkPermission } = require('./middleware/auth');

// // 添加认证路由
// app.use('/auth', authRoutes);

// // 保护需要认证的路由
// app.use('/connections', authenticateToken, checkPermission('view_connections'));
// app.use('/update_room', authenticateToken, checkPermission('manage_rooms'));

// // 保护 Socket.IO 连接
// io.use((socket, next) => {
//     const token = socket.handshake.auth.token;
//     if (!token) {
//         return next(new Error('Authentication error'));
//     }

//     jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key', (err, decoded) => {
//         if (err) return next(new Error('Authentication error'));
//         socket.user = decoded;
//         next();
//     });
// });

// RTMP 推流和 main.py 进程管理
let rtmpState = {
    proc: null,
    rtmpUrls: [],
    mainProcs: [],
    n: 0
};

// 启动 RTMP 推流和 main.py
app.post('/api/start_rtmp', async (req, res) => {
    const { n, cameraName, fps } = req.body;
    if (rtmpState.proc) {
        return res.status(400).json({ error: 'RTMP 已在运行' });
    }
    try {
        
        // const { proc, rtmpUrls } = await startRtmpStreams(n, cameraName, fps || 10);

        const pyPath = path.join('python', 'utils', 'Split.py');
        const pyArgs = [
            // '--camera_index', '0',
            '--n', String(n),
            // '--resolution', resolution || '1280x720',
            // '--jpeg_quality', jpegQuality || '80'
        ];
        const proc = spawn(
            PYTHON_INTERPRETER,
            [pyPath, ...pyArgs],
            { stdio: ['ignore', 'pipe', 'pipe'] }
        );

        // 阻塞直到获取到端口列表
        let rtmpUrls = [];
        const getPorts = new Promise((resolve, reject) => {
            let dataBuffer = '';
            const onData = (chunk) => {
                dataBuffer += chunk.toString();
                // 假设端口列表一行为JSON数组
                const regex = /\[.*?\]/s;
                const match = regex.exec(dataBuffer);
                if (match) {
                    try {
                        const ports = JSON.parse(match[0]);
                        // 生成 rtmp url 列表
                        rtmpUrls = ports.map(port => `UDP://127.0.0.1:${port}`);
                        proc.stdout.off('data', onData);
                        resolve();
                    } catch (e) {
                        // 解析失败，继续等待
                        console.error('解析端口列表时发生错误:', e);
                    }
                }
            };
            proc.stdout.on('data', onData);
            proc.stderr.on('data', (err) => {
                // 若有错误输出也可考虑 reject
            });
            proc.on('close', (code) => {
                reject(new Error('Split.py 进程提前退出'));
            });
        });

        await getPorts;

        rtmpState.proc = proc;
        rtmpState.rtmpUrls = rtmpUrls;
        rtmpState.n = n;
        rtmpState.mainProcs = [];

        // console.log(`RTMP 推流已启动， 路数: ${n}, 摄像头: ${cameraName}, 帧率: ${fps} rtmpUrls:${rtmpUrls.join(', ')}`);
        console.log(`UDP 推流已启动， 路数: ${n}, 摄像头: ${cameraName}, 帧率: ${fps} rtmpUrls:${rtmpUrls.join(', ')}`);

        // 启动 n 个 main.py，每个传入 uuid 和 rtmp_url
        for (let i = 0; i < n; i++) {
            const uuid = uuidv4();
            const room = `room${i + 1}`;
            const rtmpUrl = rtmpUrls[i];
            const pyPath = path.join('python',  'TaiJiGuiderSJTU/main.py');
            const pyProc = spawn(
                PYTHON_INTERPRETER,
                [pyPath, '--unique_id', uuid, '--rtmp_url', rtmpUrl],
                { stdio: ['ignore', 'pipe', 'pipe'] }
            );
            pyProc.room = room;
            pyProc.idx = i;
            rtmpState.mainProcs.push(pyProc);

            // 处理图片帧和控制帧
            let buffer = Buffer.alloc(0);
            let frameState = null;
            pyProc.stdout.on('data', async (chunk) => {
                buffer = Buffer.concat([buffer, chunk]);
                while (buffer.length > 0) {
                    if (!frameState) {
                        const marker = Buffer.from('---FRAME---\n');
                        const markerIndex = buffer.indexOf(marker);
                        if (markerIndex === -1) break;
                        buffer = buffer.slice(markerIndex + marker.length);
                        frameState = { header: null, expectedLength: 0, receivedBuffer: [] };
                    }
                    if (frameState && !frameState.header) {
                        const newlineIndex = buffer.indexOf(0x0A);
                        if (newlineIndex === -1) break;
                        const headerStr = buffer.slice(0, newlineIndex).toString('utf8');
                        buffer = buffer.slice(newlineIndex + 1);
                        try {
                            frameState.header = JSON.parse(headerStr);
                            if (frameState.header.type === 'control') {
                                io.to(room).emit('control', frameState.header);
                                frameState = null;
                                continue;
                            } else if (frameState.header.type === 'image') {
                                frameState.expectedLength = frameState.header.length;
                                frameState.receivedLength = 0;
                            } else {
                                frameState = null;
                            }
                        } catch {
                            frameState = null;
                        }
                    }
                    if (frameState?.header?.type === 'image') {
                        const remaining = frameState.expectedLength - frameState.receivedLength;
                        const toTake = Math.min(buffer.length, remaining);
                        frameState.receivedBuffer.push(buffer.slice(0, toTake));
                        frameState.receivedLength += toTake;
                        buffer = buffer.slice(toTake);
                        if (frameState.receivedLength >= frameState.expectedLength) {
                            const imageBuffer = Buffer.concat(frameState.receivedBuffer);
                            try {
                                // const processedBuffer = await sharp(imageBuffer)
                                //     .resize(1080, 720)
                                //     .jpeg({ quality: 60 })
                                //     .toBuffer();
                                io.to(room).emit('frame', imageBuffer);
                            } catch {
                                io.to(room).emit('frame', imageBuffer);
                            }
                            frameState = null;
                        }
                    } else {
                        break;
                    }
                }
            });
            pyProc.stderr.on('data', (data) => {
                console.error(`main.py[${room}] 错误:`, data.toString());
            });
            pyProc.on('close', (code) => {
                console.log(`main.py[${room}] 退出，代码: ${code}`);
            });
        }

        res.json({ rtmpUrls });
    } catch (err) {
        console.error('启动 RTMP/main.py 失败:', err);
        res.status(500).json({ error: '启动失败' });
    }
});

// 停止 RTMP 推流和 main.py
app.post('/api/stop_rtmp', (req, res) => {
    if (rtmpState.proc) {
        try {
            rtmpState.proc.kill();
        } catch {}
        rtmpState.proc = null;
    }
    for (const pyProc of rtmpState.mainProcs) {
        try {
            pyProc.kill();
        } catch {}
    }
    rtmpState.mainProcs = [];
    rtmpState.rtmpUrls = [];
    rtmpState.n = 0;
    res.json({ success: true });
});


