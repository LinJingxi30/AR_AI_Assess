'''
该文件实现了一个基于 FastAPI 的后端服务器，服务器接入摄像头，用于处理视频捕获和姿态检测。
主要功能包括：
1. 启动和停止摄像头捕获任务
2. 处理视频帧并进行姿态检测
3. 通过 WebSocket 广播处理后的帧数据
4. 接收和广播视频控制指令
5. 提供静态文件服务

记得修改camera = cv2.VideoCapture(0)中的参数
'''

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
import cv2
import numpy as np
import time
import base64
import asyncio
import uvicorn
from cvzone.PoseModule import PoseDetector
from typing import List
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jsonProcessKit import Json2PreviewClass as j2pc
from config.common_data import COLOR, POSE_CONNECTIONS
from CenterCoordProcess import coord_relativize

# 全局状态管理
clients: List[WebSocket] = []
frame_interval = 1 / 20  #  FPS
detector = PoseDetector()
capture_task = None
camera = None

 # 读取json文件
frames = []
json_dir = 'savedjsons/2222.json'
j2pc.get_json_frames(frames, json_dir)

# 基础设置
camera_fps = 30
win_width, win_height = 1920, 1080

# 预览坐标生成器初始化
get_coords = j2pc.PreviewCoordsGenerator(
    preview_start_center_pos=(1900, 800),
    preview_end_center_pos=(1300, 800),
    preview_time=0.8,
    fps=camera_fps,
    current_idx=0,
    frames=frames,
    scale=0.9)

current_idx = 0#待修改


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    global camera
    camera = cv2.VideoCapture("./static/part1.mp4")
    if not camera.isOpened():
        raise RuntimeError("Failed to initialize camera - check if camera is connected and available")
    yield
    # 关闭时
    if camera:
        camera.release()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def camera_task():
    global camera
    global current_idx
    try:
        while True:
            start_time = time.time()
            success, frame = await asyncio.to_thread(camera.read)
            print(success)
            if not success:
                print("Camera read failed")
                await asyncio.sleep(1)
                continue

            processed_frame = await asyncio.to_thread(process_frame, frame)
            await broadcast(processed_frame)

            elapsed = time.time() - start_time
            await asyncio.sleep(max(0, frame_interval - elapsed))

            current_idx = (current_idx + 1) % len(frames)#待修改
    except asyncio.CancelledError:
        pass

def process_frame(_frame):
    _frame = detector.findPose(_frame)
    lmList, bboxInfo = detector.findPosition(_frame)
    
    if lmList:
        # 将坐标数据相对化
        lmList = coord_relativize(lmList, use_ground=True)
        
        # 构建JSON数据
        pose_data = {
            "type": "pose_data",
            "landmarks": lmList,  # 转换numpy数组为list
        }
        return pose_data
    return None

async def broadcast(data):
    if data is None:
        return
        
    for ws in clients.copy():
        try:
            await ws.send_json(data)  # 使用send_json
        except:
            clients.remove(ws)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            # 广播消息，转发控制指令实现多人实时同步
            message = await websocket.receive_text()
            for ws in clients.copy():
                if ws != websocket:
                    await ws.send_text(message)
    except:
        clients.remove(websocket)

@app.post("/start_capture")
async def start_capture():
    global capture_task
    if capture_task and not capture_task.done():
        raise HTTPException(status_code=400, detail="Capture already running")
    capture_task = asyncio.create_task(camera_task())
    return {"status": "Capture started"}

@app.post("/stop_capture")
async def stop_capture():
    global capture_task
    if not capture_task or capture_task.done():
        raise HTTPException(status_code=400, detail="No capture running")
    capture_task.cancel()
    capture_task = None
    return {"status": "Capture stopped"}

class VideoControlRequest(BaseModel):
    action: str
    currentTime: float = 0

@app.post("/video_control")
async def video_control(request: VideoControlRequest):
    action = request.action
    currentTime = request.currentTime
    # 广播控制指令到所有 WebSocket 连接
    message = {"type": "video_control", "action": action, "currentTime": currentTime}
    for ws in clients.copy():
        try:
            await ws.send_json(message)
        except:
            clients.remove(ws)
    return {"status": "success"}

# 挂载静态文件目录(注意放在ws之后让websocket连接优先匹配，防止冲突报错)
app.mount("/", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run("AR3DServer:app", host="0.0.0.0", port=8000, reload=False)