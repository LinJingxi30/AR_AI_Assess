const { RTCVideoSource } = require('wrtc').nonstandard;
const { createCanvas, loadImage } = require('canvas');

class VideoStreamTrack {
  constructor() {
    this.source = new RTCVideoSource();
    this.track = this.source.createTrack();

    this.canvas = createCanvas(640, 480);
    this.ctx = this.canvas.getContext('2d');
  }

  // 外部调用：传入图像 Buffer 或 base64
  async pushFrameFromBuffer(buffer) {
    try {
      const image = await loadImage(buffer);
      this.ctx.drawImage(image, 0, 0, this.canvas.width, this.canvas.height);

      const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);

      this.source.onFrame({
        data: imageData.data,
        width: imageData.width,
        height: imageData.height,
      });
    } catch (err) {
      console.error('Push frame error:', err);
    }
  }

  getTrack() {
    return this.track;
  }
}

module.exports = VideoStreamTrack;
