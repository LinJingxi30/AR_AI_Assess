'''
该文件实现了一个基于 FastAPI 的后端服务器，摄像头在前端接入，通过WS将视频帧传给后端处理

注意前端想要接入摄像头，需要开启https
'''
import cv2
import numpy as np
import base64
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
import uvicorn
from fastapi.staticfiles import StaticFiles
from cvzone.PoseModule import PoseDetector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

detector = PoseDetector()

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



async def process_frame(frame_data):
    # 移除dataURL前缀
    header, encoded = frame_data.split(",", 1)
    binary = base64.b64decode(encoded)

    # 转换为OpenCV格式
    image = np.frombuffer(binary, dtype=np.uint8)
    frame = cv2.imdecode(image, cv2.IMREAD_COLOR)

    processed = detector.findPose(frame)

    # 在此处添加图像处理逻辑（示例：灰度处理）
    # processed = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 转换回JPEG
    _, jpeg = cv2.imencode('.jpg', processed)
    return base64.b64encode(jpeg.tobytes()).decode()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # print("New connection")
    try:
        while True:
            # 接收前端发送的帧
            data = await websocket.receive_text()

            # 处理帧
            processed = await process_frame(data)

            # 返回处理后的帧（dataURL格式）
            await websocket.send_text(f"data:image/jpeg;base64,{processed}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()
        # print("Connection  closed")

# 挂载静态文件目录(注意放在ws之后让websocket连接优先匹配，防止冲突报错)
app.mount("/", StaticFiles(directory="Static"), name="Static")

if __name__ == '__main__':
    uvicorn.run(app='Test:app', host="127.0.0.1", port=8000, reload=False)