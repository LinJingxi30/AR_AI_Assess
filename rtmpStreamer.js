// rtmpStreamer.js
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

/**
 * 启动 ffmpeg 推流，返回 { proc, rtmpUrls }
 * @param {number} n 切割路数
 * @param {string} cameraName 摄像头设备名（dshow）
 * @param {number} fps 帧率
 * @param {bool} saveBat 选项 { saveBat?: boolean }
 * @returns {Promise<{proc: ChildProcess, rtmpUrls: string[]}>}
 */
async function startRtmpStreams(n, cameraName, fps = 25, saveBat = 0) {
  return new Promise((resolve, reject) => {
    if (typeof n !== 'number' || n <= 0) {
      return reject(new Error('n 必须是大于0的数字'));
    }
    if (typeof fps !== 'number' || fps <= 0) {
      return reject(new Error('fps 必须是大于0的数字'));
    }
    if (typeof cameraName !== 'string' || cameraName.trim() === '') {
      return reject(new Error('cameraName 必须是非空字符串'));
    }

    // 生成 filter_complex
    const cropFilters = [];
    for (let i = 0; i < n; i++) {
      cropFilters.push(`[0:v]crop=iw/${n}:ih:iw*${i}/${n}:0[v${i}]`);
    }
    const filterComplex = cropFilters.join('; ');

    // 生成 -map 和输出流部分
    const mapAndOutputs = [];
    const rtmpUrls = [];
    for (let i = 0; i < n; i++) {
      const url = `rtmp://localhost/live/part${i + 1}`;
      rtmpUrls.push(url);
      mapAndOutputs.push('-map', `[v${i}]`, '-c:v', 'libx264', '-preset', 'ultrafast', '-f', 'flv', url);
    }

    // 拼接 ffmpeg 参数
    const ffmpegArgs = [
      '-f', 'dshow',
      '-framerate', String(fps),
      '-rtbufsize', '100000000',
      '-i', `video=${cameraName}`,
      '-filter_complex', filterComplex,
      ...mapAndOutputs
    ];

    if (saveBat) {
      const batLines = [];
      batLines.push('@echo off');
      batLines.push(`REM 自动生成推流脚本，摄像头：${cameraName}，切割路数：${n}，帧率：${fps}`);
      batLines.push(
        `"${path.resolve(__dirname, 'tool', 'ffmpeg')}" ` +
        ffmpegArgs.map(arg => (arg.includes(' ') ? `"${arg}"` : arg)).join(' ')
      );
      batLines.push('pause');
      const outputPath = path.resolve(__dirname, 'output.bat');
      fs.writeFileSync(outputPath, batLines.join('\r\n'), 'utf8');
    }

    // 启动 ffmpeg 进程
    const ffmpegPath = path.resolve(__dirname, 'tool', 'ffmpeg');
    const proc = spawn(ffmpegPath, ffmpegArgs, {
      detached: true,
      stdio: 'ignore'
    });

    proc.unref();

    resolve({ proc, rtmpUrls });
  });
}

module.exports = {
  startRtmpStreams,
};
