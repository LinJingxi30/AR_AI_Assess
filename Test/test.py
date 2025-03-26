import cv2
import sys
import base64

from cvzone.PoseModule import PoseDetector

def main():
    # 打开默认摄像头
    cap = cv2.VideoCapture(0)
    detector = PoseDetector()
    

    if not cap.isOpened():
        print("无法打开摄像头", file=sys.stderr)
        return

    while True:
        # 读取一帧
        ret, frame = cap.read()
        frame = detector.findPose(frame)

        if not ret:
            print("无法读取帧", file=sys.stderr)
            break

        # 将帧编码为 JPEG 格式
        _, buffer = cv2.imencode('.jpg', frame)

        # 将编码后的帧转换为 Base64 并输出
        sys.stdout.buffer.write(buffer)
        sys.stdout.flush()

    # 释放资源
    cap.release()
    print("摄像头已关闭", file=sys.stderr)

if __name__ == "__main__":
    main()
