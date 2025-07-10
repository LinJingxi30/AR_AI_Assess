# -*- coding: utf-8 -*-
import cv2
from cvzone.PoseModule import PoseDetector


def main():
    # 摄像头初始化
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：摄像头初始化失败！")
        return

    detector = PoseDetector()
    cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)

    while cap.isOpened():
        # 读取实时帧
        success, image = cap.read()
        if not success:
            continue

        # # 水平翻转画面
        # image = cv2.flip(image, 1)

        # 实时骨架检测
        image = detector.findPose(image, draw=False)  # 关闭内置绘图
        lmList, _ = detector.findPosition(image, draw=False)

        # 定义手的关节点索引
        left_wrist_idx = 17  # 左手腕
        right_wrist_idx = 18  # 右手腕

        # 获取手的坐标
        if lmList:
            # 左手坐标
            if len(lmList) > left_wrist_idx:
                left_hand = lmList[left_wrist_idx][0:2]  # 只取x,y坐标
                print(f"左手坐标: {left_hand}")
                cv2.circle(image, (int(left_hand[0]), int(left_hand[1])), 10, (0, 255, 0), -1)

            # 右手坐标
            if len(lmList) > right_wrist_idx:
                right_hand = lmList[right_wrist_idx][0:2]  # 只取x,y坐标
                print(f"右手坐标: {right_hand}")
                cv2.circle(image, (int(right_hand[0]), int(right_hand[1])), 10, (0, 0, 255), -1)

        # 水平翻转画面
        image = cv2.flip(image, 1)
        # 显示画面
        cv2.imshow("Hand Tracking", image)

        # 按键控制
        key = cv2.waitKey(1)
        if key == 27:  # ESC 键退出
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()