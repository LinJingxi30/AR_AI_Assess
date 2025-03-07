# websocket_server.py (修正版)
import asyncio
import websockets
import json
from skeleton_capture import RealtimeSkeleton
from coordinate_mapper import convert_to_ar_coords

# 假设的摄像头参数（需根据实际校准）
camera_params = {
    "focal_length": 1.0,
    "center_point": (0.5, 0.5)
}


async def send_skeleton(websocket):
    skeleton_provider = RealtimeSkeleton()
    try:
        while True:
            image, skeleton = skeleton_provider.get_skeleton()
            print(skeleton)
            if skeleton is not None:
                ar_coords = convert_to_ar_coords(skeleton, camera_params)
                await websocket.send(json.dumps(ar_coords.tolist()))
            await asyncio.sleep(0.033)  # 保持30fps
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")


async def main():
    async with websockets.serve(send_skeleton, "localhost", 8765):
        print("WebSocket server started")
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    # 使用标准方式启动事件循环
    asyncio.run(main())
