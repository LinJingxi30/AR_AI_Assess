import cv2
from cvzone.PoseModule import PoseDetector
import socket
import numpy as np

# 自定义绘制函数
def draw(img, lmList, point_radius=8, line_width=2):
    # 创建一个与输入图像大小相同的空白画布
    canvas = np.ones_like(img) * 255
    # 定义需要绘制的关键点索引
    key_points = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 31, 32]
    # 定义需要绘制的连接线（每对索引表示一条线）
    connections = [
        (11, 12), (11, 23), (11, 13),  # 11与12、23、13相连
        (13, 15),  # 13与15相连
        (12, 24), (12, 14),  # 12与11、24、14相连
        (16, 14),  # 16与14相连
        (23, 24), (23, 25),  # 23与24、25相连
        (24, 26),  # 24与23、26相连
        (26, 28),  # 26与28相连
        (28, 32),  # 28与32相连
        (23, 25),  # 23与25相连
        (25, 27),  # 25与27相连
        (27, 31)  # 27与31相连
    ]
    # 绘制连接线（深绿色线）
    for (start_idx, end_idx) in connections:
        if start_idx < len(lmList) and end_idx < len(lmList):
            start_x, start_y, _ = lmList[start_idx]
            end_x, end_y, _ = lmList[end_idx]
            cv2.line(canvas, (int(start_x), int(start_y)), (int(end_x), int(end_y)),
                     (0, 0, 0), line_width)  # 深绿色线
    # 绘制关键点
    for idx in key_points:
        if idx < len(lmList):
            x, y, _ = lmList[idx]
            if idx == 0:  # 单独处理序号为0的点
                cv2.circle(canvas, (int(x), int(y)), 24, (0, 0, 0), -1)  # 红色圆
            else:  # 其他点
                cv2.circle(canvas, (int(x), int(y)), point_radius, (0, 0, 0), -1)  # 黑色圆
    return canvas

if __name__ == '__main__':
    # 初始化视频捕获
    cap = cv2.VideoCapture(0)
    # 初始化UDP通信
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverAddressPort = ("127.0.0.1", 5053)
    # 初始化姿态检测器
    detector = PoseDetector()
    jointnum = 33
    # 初始化滤波器参数
    KalmanParamQ = 0.001
    KalmanParamR = 0.0015
    K = np.zeros((jointnum, 3), dtype=np.float32)
    P = np.zeros((jointnum, 3), dtype=np.float32)
    X = np.zeros((jointnum, 3), dtype=np.float32)
    PrevPose3D = np.zeros((6, jointnum, 3), dtype=np.float32)
    # 主循环
    while True:
        success, img = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置到第一帧
            PrevPose3D = np.zeros((6, jointnum, 3), dtype=np.float32)
            continue
        # 检测姿态并获取关键点
        img = detector.findPose(img, draw=False)  # 禁用默认绘制
        lmList, bboxInfo = detector.findPosition(img, draw=False)  # 禁用默认绘制
        # 调用自定义绘制函数
        if lmList:
            img = draw(img, lmList, point_radius=12, line_width=11)
        # 自适应窗口大小
        window_name = "Image"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, img.shape[1], img.shape[0])  # 根据图像大小调整窗口
        # 显示图像
        cv2.imshow(window_name, img)
        # 平滑处理并发送数据
        if bboxInfo:
            currdata = np.squeeze(lmList)
            smooth_kps = np.zeros((jointnum, 3), dtype=np.float32)
            # Kalman滤波
            for i in range(jointnum):
                K[i] = (P[i] + KalmanParamQ) / (P[i] + KalmanParamQ + KalmanParamR)
                P[i] = KalmanParamR * (P[i] + KalmanParamQ) / (P[i] + KalmanParamQ + KalmanParamR)
            for i in range(jointnum):
                smooth_kps[i] = X[i] + (currdata[i] - X[i]) * K[i]
                X[i] = smooth_kps[i]
            # 低通滤波
            LowPassParam = 0.1
            PrevPose3D[0] = smooth_kps
            for j in range(1, 6):
                PrevPose3D[j] = PrevPose3D[j] * LowPassParam + PrevPose3D[j - 1] * (1.0 - LowPassParam)
            # 格式化数据并发送
            lmString = ''
            for lm in PrevPose3D[5]:
                lmString += f'{lm[0]},{img.shape[0] - lm[1]},{lm[2]},'
            sock.sendto(str.encode(str(lmString)), serverAddressPort)
        # 退出程序
        if cv2.waitKey(1) == ord('q'):
            break
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
