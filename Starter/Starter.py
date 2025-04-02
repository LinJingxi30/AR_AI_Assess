import sys
from pathlib import Path
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(MEDIA_PIPE_ROOT))

import cv2
import numpy as np
from pygame.locals import *
from cvzone.PoseModule import PoseDetector
from Config.common_data import WIN_SIZE
from .config import *
from.draw import *


def get_sport_type():
    """
    在屏幕上横向显示三个红色圆点，并等待右手触摸其中一个点，
    一旦检测到左右手（关键点索引15，16）进入某个圆点的范围，就返回对应的数字（1、2或3）。
    显示窗口的尺寸由全局变量 WIN_SIZE 定义。
    """
    # 初始化摄像头和姿态检测器
    cap = cv2.VideoCapture(0)
    detector = PoseDetector()
    
    # 先读取一帧，确定图像尺寸
    ret, frame = cap.read()
    if not ret:
        print("无法读取摄像头帧")
        return None
    frame = cv2.flip(frame, 1)  # 镜像翻转
    h, w = frame.shape[:2]
    
    # 定义三个点的横向位置（比如在宽度的1/4, 1/2, 3/4处），纵坐标固定在200像素处
    points = [(int(w * 0.25), 200), (int(w * 0.50), 200), (int(w * 0.75), 200)]
    radius = 20  # 每个点的半径
    
    chosen = None
    print("请用右手触摸屏幕上的一个点以选择（按 'q' 退出）...")
    
    # 为确保显示窗口大小固定，使用 cv2.resize 进行显示前的缩放
    while chosen is None:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)  # 镜像翻转
        
        # 在原始尺寸图像上绘制三个选择点
        for i, pt in enumerate(points):
            # cv2.circle(frame, pt, radius, (0, 0, 255), -1)  # 红色圆点
            draw_gradient_point(frame, pt, VISUAL_CONFIG["gradient"]["std_color"],
                            VISUAL_CONFIG["gradient"]["max_radius"],
                            VISUAL_CONFIG["gradient"]["steps"])
            cv2.putText(frame, str(i+1), (pt[0]-10, pt[1]-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 进行姿态检测
        frame = detector.findPose(frame, draw=False)
        lmList, _ = detector.findPosition(frame, draw=False)
        
        # 检查右手位置（假设右手关键点索引为16）
        if lmList is not None and len(lmList) > 16:
            lwrist = lmList[15]  # 左手关键点
            # rwrist = lmList[16]  # 右手关键点
            # lwrist_pt = (int(lwrist[0]), int(lwrist[1]))
            lwrist_pt = (int(lwrist[0]), int(lwrist[1]))
            # 绘制检测到的左右手位置
            # cv2.circle(frame, lwrist_pt, 10, (0,255,0), -1)
            draw_gradient_point(frame, lwrist_pt, 
                                     VISUAL_CONFIG["gradient"]["real_color"],
                                     VISUAL_CONFIG["gradient"]["max_radius"] // 2,
                                     VISUAL_CONFIG["gradient"]["steps"] // 2)
            
            # 检查右手是否进入任意一个选择点区域
            for i, pt in enumerate(points):
                distance = np.linalg.norm(np.array(lwrist_pt) - np.array(pt))
                if distance < radius:
                    chosen = i + 1
                    break

        if chosen == 1:
            chosen_str = "太极"
        elif chosen == 2:
            chosen_str = "健美操"
        else:
            chosen_str = "瑜伽"

        # 将处理好的图像缩放到 WIN_SIZE 再显示
        display_frame = cv2.resize(frame, WIN_SIZE)

        """发送至前端"""
        _,buffer = cv2.imencode('.jpg', display_frame)  # 编码为 JPG 格式
        sys.stdout.buffer.write(buffer)  # 将编码后的数据写入标准输出流
        sys.stdout.flush()  # 刷新输出流

        cv2.imshow("选择区域", display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyWindow("选择区域")
    return chosen_str

WIN_WIDTH, h = WIN_SIZE

class StarterClass:
    def __init__(self):
        self.detector = PoseDetector()
        # 状态变量
        self.running = True
        self.chosen = None
        self.chosen_str = None
        self.out_frame = None

        """配置区"""
        self.points = [(int(WIN_WIDTH * 0.25), 200), (int(WIN_WIDTH * 0.50), 200), (int(WIN_WIDTH * 0.75), 200)]    # 选择点位置横坐标
        self.radius_threshold = 20  # 选中半径阈值


    def update(self, frame):
        if self.running:
            """处理单帧：检测手势、绘制选择UI，若选中则赋值 self.chosen"""
            # 翻转frame
            frame = cv2.flip(frame, 1)

            # 进行姿态检测
            frame = self.detector.findPose(frame, draw=False)
            lmList, _ = self.detector.findPosition(frame, draw=False)

            # 绘制三个选择点
            for i, pt in enumerate(self.points):
                draw_gradient_point(frame, pt, 
                                        VISUAL_CONFIG["gradient"]["std_color"],
                                        VISUAL_CONFIG["gradient"]["max_radius"],
                                        VISUAL_CONFIG["gradient"]["steps"])
                cv2.putText(frame, str(i+1), (pt[0]-10, pt[1]-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # 检查右手位置，绘制右手心跟踪点
            if lmList is not None:
                lwrist = lmList[15]  # 右手关键点
                lwrist_pt = (int(lwrist[0]), int(lwrist[1]))
                draw_gradient_point(frame, lwrist_pt, 
                                        VISUAL_CONFIG["gradient"]["real_color"],
                                        VISUAL_CONFIG["gradient"]["max_radius"] // 2,
                                        VISUAL_CONFIG["gradient"]["steps"] // 2)
                
                # 检查右手是否进入任意一个选择点区域
                for i, pt in enumerate(self.points):
                    distance = np.linalg.norm(np.array(lwrist_pt) - np.array(pt))
                    if distance < self.radius_threshold:
                        self.chosen = i + 1  # 1, 2, 3
                        break
            else:
                self.chosen = None

            if self.chosen is not None:
                self.running = False  # 选中后停止更新
                if self.chosen == 1:
                    self.chosen_str = "太极"
                elif self.chosen == 2:
                    self.chosen_str = "健美操"
                else:
                    self.chosen_str = "瑜伽"

            # 将处理好的图像缩放到 WIN_SIZE
            self.out_frame = cv2.resize(frame, WIN_SIZE)

            return self.chosen_str, self.out_frame


    def get_output_frame(self):
        return self.out_frame


if __name__ == "__main__":
    print(get_sport_type()) # 调试
    # pass