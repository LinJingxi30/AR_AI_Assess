// streamer.js
// webRTC推流
const io = require("socket.io-client");
const wrtc = require("wrtc");
const VideoStreamTrack = require('./components/video-track');
const { spawn } = require("child_process");

const socket = io("https://webrtc.chainpray.top/");

const pc = new wrtc.RTCPeerConnection();
const trackSource = new VideoStreamTrack(); // 管理视频帧输入
pc.addTrack(trackSource.getTrack());

socket.on("offer", async (offer) => {
  await pc.setRemoteDescription(new wrtc.RTCSessionDescription(offer));
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  socket.emit("answer", pc.localDescription);
});

socket.on("candidate", async (candidate) => {
  await pc.addIceCandidate(new wrtc.RTCIceCandidate(candidate));
});

const PYTHON_INTERPRETER = (process.env.PYTHON_INTERPRETER || 'env/python.exe'); // 默认使用当前目录下的 python.exe
const scriptPath = "python/TaiJiGuiderSJTU/main.py"
// 从 Python 读取图像帧
const pythonProcess = spawn(PYTHON_INTERPRETER, [scriptPath,'--unique_id',"asdad"]);

// 初始化缓冲区和帧状态
let buffer = Buffer.alloc(0);  // 用于存储接收到的数据
let frameState = null;  // 用于跟踪当前帧的处理状态

pythonProcess.stdout.on('data', async (chunk) => {
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
          // io.to(room).emit('control', frameState.header);
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
        try {
          await trackSource.pushFrameFromBuffer(imageBuffer);

        } catch (err) {
          console.error('处理图像帧失败:', err);
        }
        frameState = null;
      }
    } else {
      break;  // 等待下一个帧
    }
  }
});


pythonProcess.stderr.on('data', (data) => {
  console.error(`Python脚本错误 `);
});

pythonProcess.on('close', (code) => {
  console.log(`Python脚本退出 ，代码: ${code}`);
});


