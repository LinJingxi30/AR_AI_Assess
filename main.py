from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
import cv2
import numpy as np
import base64
import asyncio
import uvicorn

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

    # 在此处添加图像处理逻辑（示例：灰度处理）
    processed = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 转换回JPEG
    _, jpeg = cv2.imencode('.jpg', processed)
    return base64.b64encode(jpeg.tobytes()).decode()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
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

if __name__ == '__main__':
    uvicorn.run(app='main:app', host="127.0.0.1", port=8000, reload=True)
# 运行命令：uvicorn main:app --reload