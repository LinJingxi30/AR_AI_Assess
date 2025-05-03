# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/4/30 02:34
# @Content :

import pygame
import cv2

def main():
    # 初始化 pygame
    pygame.init()
    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Pygame 初始化示例")

    # 创建时钟控制帧率
    clock = pygame.time.Clock()
    running = True

    while running:
        # 处理 pygame 事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 填充背景颜色
        screen.fill((0, 0, 0))

        # 更新显示内容
        pygame.display.flip()

        # 保持帧率为 60 FPS
        clock.tick(60)

    # 退出 pygame
    pygame.quit()

def cv2test():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    if not cap.isOpened():
        print("无法打开摄像头")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头画面")
            break

        # 获取分辨率，打印
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera Resolution: {width}x{height}")

        cv2.imshow("Camera 1300x1000", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break



    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    cv2test()

# @A last new line here:
