"""
video -> json
此脚本用于实时捕捉视频中的人体姿态，并通过 Kalman 滤波器和低通滤波器对关键点进行平滑处理。
处理后的关键点数据会通过 UDP 发送，并保存为 JSON 文件。同时，使用 Matplotlib 绘制关键点和骨架。
"""

import sys
import cv2
import numpy as np
import socket
from cvzone.PoseModule import PoseDetector
import matplotlib.pyplot as plt
import json
from CenterCoordProcess import coord_relativize
from config.common_data import POSE_CONNECTIONS

# 保存的 JSON 文件路径
json_dir = 'savedjsons/relatetest.json'
json_array = []

target_video = "./static/video2.mp4"

# 启用 matplotlib 交互模式
plt.ion()
fig, ax = plt.subplots()
ax.set_xlim(0, 640)
ax.set_ylim(0, 480)
ax.invert_yaxis()  #  去掉，避免上下反转
sc = ax.scatter([], [], c='red', s=10)  # 用于绘制关键点
bones_lines = []  # 用于绘制骨架线

ax.axis('off')

# 骨架连线的点对（可按需求调整）
bones = POSE_CONNECTIONS

# 为每条骨架线创建 Line2D 对象
for _ in bones:
    line_obj, = ax.plot([], [], c='green', linewidth=2)
    bones_lines.append(line_obj)

print("尝试初始化摄像头...")
cap = cv2.VideoCapture(target_video)
print("摄像头初始化结果:", cap.isOpened())
if not cap.isOpened():
    print("错误：摄像头初始化失败！请检查设备连接。")
    sys.exit()

# UDP 套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverAddressPort = ("127.0.0.1", 5053)

detector = PoseDetector()
jointnum = 33

# Kalman 滤波器参数
KalmanParamQ = 0.001
KalmanParamR = 0.0015
K = np.zeros((jointnum, 3), dtype=np.float32)
P = np.zeros((jointnum, 3), dtype=np.float32)
X = np.zeros((jointnum, 3), dtype=np.float32)

# 低通滤波器参数
PrevPose3D = np.zeros((6, jointnum, 3), dtype=np.float32)

frame_id = 0

# 每次运行前先清空json文件（循环里用的是追加模式，不会直接覆盖）
# 清空json文件（仅执行一次）
with open(json_dir, "w") as f:
    pass  # 空操作触发清空

while True:
    success, img = cap.read()
    if not success:
        print("警告：读取摄像头帧失败！")
        break

    img = detector.findPose(img)
    # 接收检测到的关键点lmList
    lmList, bboxInfo = detector.findPosition(img)
    print("检测到的关键点数量:", len(lmList) if lmList else 0)

    lmString = ''
    if bboxInfo:
        currdata = np.squeeze(lmList)   # to 33*3
        smooth_kps = np.zeros((jointnum, 3), dtype=np.float32)

        # Kalman
        for i in range(jointnum):
            K[i] = (P[i] + KalmanParamQ) / (P[i] + KalmanParamQ + KalmanParamR)
            P[i] = KalmanParamR * (P[i] + KalmanParamQ) / (P[i] + KalmanParamQ + KalmanParamR)
        for i in range(jointnum):
            smooth_kps[i] = X[i] + (currdata[i] - X[i]) * K[i]
            X[i] = smooth_kps[i]

        # 低通
        LowPassParam = 0.1
        PrevPose3D[0] = smooth_kps
        for j in range(1, 6):
            PrevPose3D[j] = (PrevPose3D[j] * LowPassParam
                             + PrevPose3D[j - 1] * (1.0 - LowPassParam))
        """
        NumPy数组，finalPose[i][0] 表示第 i 个关键点的 X 坐标。
        """
        finalPose = PrevPose3D[5]
        coord_relativize(finalPose, True)

        # 生成 lmString
        for lm in finalPose:
            # 不再做 img.shape[0] - lm[1]，避免上下反转
            lmString += f'{lm[0]},{lm[1]},{lm[2]},'

        # 发送数据
        sock.sendto(str.encode(str(lmString)), serverAddressPort)

        # 用 Matplotlib 绘制
        xvals = [640 - pt[0] for pt in finalPose]
        yvals = [pt[1] for pt in finalPose]
        sc.set_offsets(np.c_[xvals, yvals])

        for line_obj, (start_idx, end_idx) in zip(bones_lines, bones):
            if start_idx < len(xvals) and end_idx < len(xvals):
                line_obj.set_xdata([xvals[start_idx], xvals[end_idx]])
                line_obj.set_ydata([yvals[start_idx], yvals[end_idx]])

        # plt.draw()
        # plt.pause(0.001)

    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break

    # 写入 JSON 文件
    # 使用视频相对时间（单位 ms）作为时间戳
    video_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
    frame_id += 1
    try:
        # 处理姿态数据
        pose_str = lmString.rstrip(',')
        pose_array = json.loads(f"[{pose_str}]")  # 转换为Python列表

        # 构建合法JSON对象
        json_data = {
            "ID": str(frame_id),
            "time": f"{video_time_ms}ms",
            "poses": pose_array,  # 直接使用列表类型
        }
        print(json_data)
        # 写入文件（使用追加模式）
        with open(json_dir, 'a', encoding='utf-8') as f:
            f.write(json.dumps(json_data, ensure_ascii=False) + '\n')  # 自动处理转义

        print("成功写入 JSON 文件, Frame:", frame_id)
    except json.JSONDecodeError as e:
        print(f"JSON格式错误: {e} (检查pose字符串)")
    except Exception as e:
        print("文件写入失败:", e)

cap.release()
cv2.destroyAllWindows()