# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import cv2
import numpy as np
import os
import time
from cvzone.PoseModule import PoseDetector
from Starter.SportSelector import get_sport_type
from Config.common_data import WIN_SIZE
import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties

from ProcessKit import Draw

WIN_WIDTH, WIN_HEIGHT = WIN_SIZE

VISUAL_CONFIG = {
    "gradient": {
        "std_color": (0, 0, 255),  # 红色
        "real_color": (0, 255, 0),  # 绿色
        "max_radius": 40,
        "steps": 10
    }
}

END_SCREEN_IMAGE_PATH = r"gameAssets\images\practice_end2.png"
FONT_PATH = r"gameAssets\\fonts\\arial_bold2.otf"

def draw_game_over(img_dir=END_SCREEN_IMAGE_PATH, score=0, font=FontProperties(fname=FONT_PATH)):
    """绘制游戏结束画面"""
    WIN_WIDTH, WIN_HEIGHT = WIN_SIZE
    fig, axes = plt.subplots(figsize=(WIN_WIDTH/100, WIN_HEIGHT/100), dpi=100)  # 按实际窗口尺寸设置
    canvas = FigureCanvasAgg(fig)
    axes.axis('off')  # 关闭坐标轴
    axes.set_xlim(0, 1)
    # 去白边
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    end_screen_img = cv2.imread(img_dir)
    # 加载并显示结束画面背景
    if end_screen_img is not None:
        end_screen_img = cv2.resize(end_screen_img, WIN_SIZE)
        end_screen_img = cv2.cvtColor(end_screen_img, cv2.COLOR_BGR2RGB)
        end_screen_img = cv2.resize(end_screen_img, WIN_SIZE)
        axes.imshow(end_screen_img, extent=[0, 1, 0, 1], aspect='auto')
    else:
        # print(f"无法加载结束画面图片: {END_SCREEN_IMAGE_PATH}")
        axes.set_facecolor('black')  # 加载失败时使用黑色背景

    # 显示最终得分
    # final_score_text = f"Final Score ; {score}"
    # axes.text(0.5, 0.5, final_score_text, ha='center', va='center',
    #                  bbox=dict(facecolor='black', alpha=0.8, edgecolor='white', boxstyle='round,pad=0.5'),
    #                  fontsize=40, fontweight='bold', color='cyan', fontproperties=font)
    # 转为cv2格式
    canvas.draw()
    img = np.array(canvas.buffer_rgba())
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    return img
def draw_gradient_point(frame, center, color, max_radius, steps):
    for r in range(max_radius, 0, -int(max_radius / steps)):
        alpha = r / max_radius
        blended_color = tuple(int(c * alpha) for c in color)
        cv2.circle(frame, center, r, blended_color, -1)


def load_and_resize_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is not None:
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        img = cv2.resize(img, (250, 250))
    return img

def main():
    # 初始化运动类型和图片相关变量
    sport_options = {
        "TaiChi": "StdSportsResults/trans_fram/xuni",
        "Aerobics": "StdSportsResults/trans_fram/xuni",
        "Yoga": "StdSportsResults/trans_fram/xuni"  # 可根据需要修改瑜伽的文件夹
    }
    sport_type = None
    image_folder = None
    image_files = []
    current_image_idx = 0
    overlay_image = None
    last_switch_time = time.time()
    switch_interval = 0.02
    images_played = False

    # 先运行选择模式
    sport_type = get_sport_type()
    if sport_type is None:
        print("未选择运动类型，程序退出", file=sys.stderr)
        return

    # 初始化主循环使用的摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头", file=sys.stderr)
        return

    # 设置图片文件夹和文件
    image_folder = sport_options[sport_type]
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    image_files = [f for f in os.listdir(image_folder)
                   if f.endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print(f"{image_folder} 中没有图片，程序将退出", file=sys.stderr)
        cap.release()
        cv2.destroyAllWindows()
        return

    overlay_image = load_and_resize_image(os.path.join(image_folder, image_files[0]))

    clock = pygame.time.Clock()

    pose_detector = PoseDetector()

    while True:
        clock.tick(15)  # 帧率控制
        ret, frame = cap.read()
        if not ret:
            print("无法获取摄像头画面", file=sys.stderr)
            break

        frame = cv2.resize(frame, (WIN_WIDTH, WIN_HEIGHT))

        frame = cv2.flip(frame, 1)
        # h, w = frame.shape[:2]

        # mp 官方绘制
        frame = pose_detector.findPose(frame, draw=False)
        sketList, _ = pose_detector.findPosition(frame, draw=False)

        Draw.draw_skeleton111(frame, sket=sketList, custom_config=Draw.alpha_DRAW_SKET_OVERALL_CONFIG)

        # 更新叠加图片
        if image_files and time.time() - last_switch_time >= switch_interval:
            current_image_idx = (current_image_idx + 1)
            if current_image_idx >= len(image_files):
                images_played = True
            else:
                overlay_image = load_and_resize_image(
                    os.path.join(image_folder, image_files[current_image_idx]))
                last_switch_time = time.time()

        # 叠加图片到右上角
        if overlay_image is not None and not images_played:
            overlay_h, overlay_w = overlay_image.shape[:2]
            top = 10
            right = WIN_WIDTH - overlay_w - 10

            if top + overlay_h <= WIN_HEIGHT and right + overlay_w <= WIN_WIDTH:
                frame_bgra = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                roi = frame_bgra[top:top + overlay_h, right:right + overlay_w]
                overlay_bgr = overlay_image[:, :, :3]
                alpha_mask = overlay_image[:, :, 3] / 255.0

                for c in range(3):
                    roi[:, :, c] = (1 - alpha_mask) * roi[:, :, c] + alpha_mask * overlay_bgr[:, :, c]
                frame_bgra[top:top + overlay_h, right:right + overlay_w] = roi
                frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)

        # 显示运动类型名称
        cv2.putText(frame, sport_type, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)

        # 如果图片播放完成，退出程序
        if images_played:
            print(f"{sport_type} 的图片已播放完成，程序退出")
            break

        # 编码并传输帧
        _, buffer = cv2.imencode('.jpg', frame, [
            int(cv2.IMWRITE_JPEG_QUALITY), 75,
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1
        ])
        sys.stdout.buffer.write(buffer)
        sys.stdout.flush()

        # 显示窗口
        display_frame = cv2.resize(frame, WIN_SIZE)
        cv2.imshow('Sport Display', display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    

    """结算"""
    clock = pygame.time.Clock()
    while True:
        frame = draw_game_over()
        """发送三"""
        _, buffer = cv2.imencode('.jpg', frame, [
            int(cv2.IMWRITE_JPEG_QUALITY), 75,  # 质量系数
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1  # 启用Huffman优化
        ])
        sys.stdout.buffer.write(buffer.tobytes())
        sys.stdout.flush()

        cv2.imshow("Game Over", frame)
        if cv2.waitKey(50) & 0xFF == 27:
            break
        clock.tick(1)   # 1fps
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
