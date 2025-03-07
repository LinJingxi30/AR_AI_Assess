# import sys
import cv2
import numpy as np
import base64
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
import uvicorn
# import datetime
# import time
# import socket
from cvzone.PoseModule import PoseDetector
# import matplotlib
# import matplotlib.pyplot as plt


# 启用 matplotlib 交互模式
# plt.ion()
# fig, ax = plt.subplots()
# ax.set_xlim(0, 640)
# ax.set_ylim(0, 480)
# ax.invert_yaxis()  #  去掉，避免上下反转
# sc = ax.scatter([], [], c='red', s=10)  # 用于绘制关键点
# bones_lines = []  # 用于绘制骨架线

# ax.axis('off')

# 定义骨架连线的点对（可按需求调整）
# bones = [
#     (11, 12),  # 左肩 -> 右肩
#     (11, 13),  # 左肩 -> 左肘
#     (12, 14),  # 右肩 -> 右肘
#     (13, 15),  # 左肘 -> 左手
#     (14, 16),  # 右肘 -> 右手
#     (11, 23),  # 左肩 -> 左髋
#     (12, 24),  # 右肩 -> 右髋
#     (23, 25),  # 左髋 -> 左膝
#     (24, 26),  # 右髋 -> 右膝
#     (25, 27),  # 左膝 -> 左脚
#     (26, 28),  # 右膝 -> 右脚
# ]

# 为每条骨架线创建 Line2D 对象
# for _ in bones:
#     line_obj, = ax.plot([], [], c='green', linewidth=2)
#     bones_lines.append(line_obj)

# print("尝试初始化摄像头...")
# cap = cv2.VideoCapture(0)
# print("摄像头初始化结果:", cap.isOpened())
# if not cap.isOpened():
#     print("错误：摄像头初始化失败！请检查设备连接。")
#     sys.exit()

# UDP 套接字
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# serverAddressPort = ("127.0.0.1", 5053)

detector = PoseDetector()
# jointnum = 33

# Kalman 滤波器参数
# KalmanParamQ = 0.001
# KalmanParamR = 0.0015
# K = np.zeros((jointnum, 3), dtype=np.float32)
# P = np.zeros((jointnum, 3), dtype=np.float32)
# X = np.zeros((jointnum, 3), dtype=np.float32)

# 低通滤波器参数
# PrevPose3D = np.zeros((6, jointnum, 3), dtype=np.float32)

# frame_id = 0

# while True:
#     success, img = cap.read()
#     if not success:
#         print("警告：读取摄像头帧失败！")
#         break

#     img = detector.findPose(img)
#     cv2.imshow("Pose Detection", img)
#     cv2.waitKey(1)
    
#     lmList, bboxInfo = detector.findPosition(img)
#     print("检测到的关键点数量:", len(lmList) if lmList else 0)

#     lmString = ''
#     if bboxInfo:
#         currdata = np.squeeze(lmList)
#         smooth_kps = np.zeros((jointnum, 3), dtype=np.float32)

#         # Kalman
#         for i in range(jointnum):
#             K[i] = (P[i] + KalmanParamQ) / (P[i] + KalmanParamQ + KalmanParamR)
#             P[i] = KalmanParamR * (P[i] + KalmanParamQ) / (P[i] + KalmanParamQ + KalmanParamR)
#         for i in range(jointnum):
#             smooth_kps[i] = X[i] + (currdata[i] - X[i]) * K[i]
#             X[i] = smooth_kps[i]

#         # 低通
#         LowPassParam = 0.1
#         PrevPose3D[0] = smooth_kps
#         for j in range(1, 6):
#             PrevPose3D[j] = (PrevPose3D[j] * LowPassParam
#                              + PrevPose3D[j - 1] * (1.0 - LowPassParam))

#         finalPose = PrevPose3D[5]
#         # 生成 lmString
#         for lm in finalPose:
#             # 不再做 img.shape[0] - lm[1]，避免上下反转
#             lmString += f'{lm[0]},{lm[1]},{lm[2]},'

#         # 发送数据
#         sock.sendto(str.encode(str(lmString)), serverAddressPort)

#         # 用 Matplotlib 绘制
#         xvals = [640 - pt[0] for pt in finalPose]
#         yvals = [pt[1] for pt in finalPose]
#         sc.set_offsets(np.c_[xvals, yvals])

#         for line_obj, (start_idx, end_idx) in zip(bones_lines, bones):
#             if start_idx < len(xvals) and end_idx < len(xvals):
#                 line_obj.set_xdata([xvals[start_idx], xvals[end_idx]])
#                 line_obj.set_ydata([yvals[start_idx], yvals[end_idx]])

#         plt.draw()
#         plt.pause(0.001)

#     cv2.imshow("Image", img)
#     key = cv2.waitKey(1)
#     if key == ord('q'):
#         break

#     # 使用视频相对时间（单位 ms）作为时间戳
#     video_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
#     # 写入 JSON 文件
#     frame_id += 1
#     try:
#         with open("Squat.json", 'a', encoding='utf-8') as f:
#             pose_str = f"[{lmString.rstrip(',')}]"
#             f.write(f'{{{{"ID":"{frame_id}"}}{{"pose":"{pose_str}"}}{{"time":"{video_time_ms}ms"}}}}\n')
#         print("成功写入 JSON 文件, Frame:", frame_id)
#     except Exception as e:
#         print("JSON 文件写入失败:", e)

# cap.release()
# cv2.destroyAllWindows()

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
    uvicorn.run(app='test:app', host="127.0.0.1", port=8000, reload=True)