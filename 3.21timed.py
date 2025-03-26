# -*- coding: utf-8 -*-
import cv2
import numpy as np
import pygame
from pygame.locals import *
from pygame import mixer
from cvzone.PoseModule import PoseDetector
from Config.common_data import WIN_SIZE, POSE_CONNECTIONS, COLOR
from ProcessKit import Json2PreviewClass as j2pc
import time
import math

# 初始化Pygame
pygame.init()
mixer.init()

# 音频配置
SOUND_FILES = {
    "perfect": "gameAssets/sounds/perfect2.wav",
    "great": "gameAssets/sounds/great2.wav",
    "good": "gameAssets/sounds/good2.wav"
}

# 字体配置
FONT_CONFIG = {
    "feedback": pygame.font.Font("gameAssets/fonts/impact2.otf", 72),
    "score": pygame.font.Font("gameAssets/fonts/arial_bold2.otf", 36),
    "title": pygame.font.Font("gameAssets/fonts/Windhavi.otf", 36)
}

# 视觉参数配置
VISUAL_CONFIG = {
    "arrow": {
        "thickness": 4,
        "size": 20,
        "num_arrows": 3,
        "checkmark_size": 15
    },
    "gradient": {
        "max_radius": 30,
        "steps": 5,
        "std_color": (255, 191, 0),
        "real_color": (72, 209, 204)
    },
    "feedback_colors": {
        "perfect": (0, 255, 0),
        "great": (255, 215, 0),
        "good": (255, 69, 0)
    }
}

POSE_LANDMARKS = {
    "left_wrist": 15,
    "right_wrist": 16,
    "left_ankle": 27,
    "right_ankle": 28
}

# 系统配置
WIN_WIDTH, WIN_HEIGHT = WIN_SIZE
FRAME_RATE = 60

def init_audio():
    """初始化音频系统"""
    global SOUNDS
    SOUNDS = {name: mixer.Sound(file) for name, file in SOUND_FILES.items()}

def draw_checkmark_arrow(canvas, start_point, end_point, color, thickness, arrow_size):
    """绘制对号形状的动态箭头"""
    dx, dy = end_point[0] - start_point[0], end_point[1] - start_point[1]
    length = np.hypot(dx, dy)
    if length == 0:
        return
    dx, dy = dx / length, dy / length
    checkmark_point1 = (int(end_point[0] - arrow_size * (dx + dy)),
                        int(end_point[1] - arrow_size * (dy - dx)))
    checkmark_point2 = (int(end_point[0] - arrow_size * (dx - dy)),
                        int(end_point[1] - arrow_size * (dy + dx)))
    cv2.line(canvas, checkmark_point1, end_point, color, thickness)
    cv2.line(canvas, checkmark_point2, end_point, color, thickness)

def draw_gradient_point(canvas, center, color, max_radius=30, steps=5):
    """绘制渐变点效果"""
    overlay = canvas.copy()
    for i in range(steps):
        radius = int(max_radius * (i + 1) / steps)
        alpha = 1.0 - (i / steps)
        cv2.circle(overlay, center, radius, color, -1)
        cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

def draw_arrows_on_path(canvas, start, end, color):
    """在路径上绘制多个动态箭头"""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = np.hypot(dx, dy)
    if length == 0:
        return

    config = VISUAL_CONFIG["arrow"]
    for i in range(1, config["num_arrows"] + 1):
        t = i / (config["num_arrows"] + 1)
        current = (
            int(start[0] + t * dx),
            int(start[1] + t * dy)
        )
        draw_checkmark_arrow(canvas, start, current, color,
                             config["thickness"], config["checkmark_size"])

def calculate_distance(point1, point2):
    """计算两点之间的欧氏距离"""
    return np.linalg.norm(np.array(point1) - np.array(point2))

def draw_points_to_reach(canvas, std_points, real_points, threshold=50):
    """优化后的指导点绘制函数，返回匹配度"""
    if not std_points or not real_points:
        return 0.0

    total_distance = 0
    max_possible_distance = len(std_points) * threshold
    for (std, real), name in zip(zip(std_points, real_points), POSE_LANDMARKS.keys()):
        std_pos = (int(std[0]), int(std[1]))
        real_pos = (int(real[0]), int(real[1]))

        # 绘制渐变点
        draw_gradient_point(canvas, std_pos, VISUAL_CONFIG["gradient"]["std_color"],
                            VISUAL_CONFIG["gradient"]["max_radius"],
                            VISUAL_CONFIG["gradient"]["steps"])
        draw_gradient_point(canvas, real_pos, VISUAL_CONFIG["gradient"]["real_color"],
                            VISUAL_CONFIG["gradient"]["max_radius"] // 2,
                            VISUAL_CONFIG["gradient"]["steps"] // 2)

        # 计算距离并绘制动态路径
        distance = calculate_distance(std, real)
        total_distance += distance
        arrow_color = COLOR["green" if distance <= threshold else "red"]
        draw_arrows_on_path(canvas, real_pos, std_pos, arrow_color)

    match_score = 1.0 - (total_distance / max_possible_distance) if max_possible_distance > 0 else 1.0
    return match_score

class FeedbackSystem:
    """实时反馈管理系统"""
    def __init__(self):
        self.active_feedbacks = []
        self.total_score = 0
        self.score_history = []
        self.last_score_time = 0

    def add_feedback(self, text, score):
        """添加新的反馈"""
        self.active_feedbacks.append({
            "text": text,
            "start_time": time.time(),
            "color": VISUAL_CONFIG["feedback_colors"][text.lower()]
        })
        self.total_score += score
        self.score_history.append((score, time.time()))
        SOUNDS[text.lower()].play()

    def update_feedbacks(self):
        """更新反馈状态"""
        current_time = time.time()
        self.active_feedbacks = [
            fb for fb in self.active_feedbacks
            if current_time - fb["start_time"] < 1.5
        ]

    def draw_feedbacks(self, screen):
        """绘制所有动态反馈"""
        current_time = time.time()
        for i, fb in enumerate(self.active_feedbacks):
            alpha = min(255, int(255 * (1.5 - (current_time - fb["start_time"]))))
            text_surface = FONT_CONFIG["feedback"].render(
                fb["text"], True, (*fb["color"], alpha))
            
            # 动态位置计算
            x = WIN_WIDTH//2 - text_surface.get_width()//2
            y = 50 + i*80 + 10*math.sin(5*current_time)
            screen.blit(text_surface, (x, y))

    def draw_score(self, screen):
        """绘制得分信息"""
        score_text = FONT_CONFIG["score"].render(
            f"SCORE: {self.total_score}", True, (255, 215, 0))
        screen.blit(score_text, (20, 20))

def main():
    # 初始化系统
    init_audio()
    screen = pygame.display.set_mode(WIN_SIZE, DOUBLEBUF)
    pygame.display.set_caption("Motion Coach Pro")
    clock = pygame.time.Clock()

    # 加载背景音乐
    mixer.music.load("gameAssets/sounds/timed_bgm.mp3")
    mixer.music.set_volume(0.3)
    mixer.music.play(-1)

    # 加载标准数据
    std_json_frames = []
    j2pc.get_json_frames(std_json_frames, "stdProcess/sampled_std_frames.json")
    original_std_size = (WIN_WIDTH, WIN_HEIGHT)

    # 初始化计时变量
    start_ticks = pygame.time.get_ticks()

    # 预加载遮罩帧（原有代码不变）
    masked_frames = []
    for idx in range(len(std_json_frames)):
        frame_path = f"stdProcess/masked_sampled_std_frames/masked_frame_{idx:05d}.png"
        overlay = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
        if overlay is not None:
            overlay = cv2.resize(overlay, original_std_size)
        masked_frames.append(overlay)

    # 摄像头初始化（原有代码不变）
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        pygame.quit()
        return

    detector = PoseDetector()
    feedback_sys = FeedbackSystem()
    pose_start_time = None
    json_line_idx = 0
    std_mask_idx = 0

    running = True
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False

        # 计算剩余时间
        current_ticks = pygame.time.get_ticks()
        elapsed_seconds = (current_ticks - start_ticks) // 1000
        remaining_time = max(0, 60 - elapsed_seconds)

        # 读取摄像头帧（原有代码逻辑不变）
        success, image = cap.read()
        if not success:
            continue

        # 姿势检测
        image = cv2.flip(image, 1)
        image = detector.findPose(image, draw=False)
        sketList, _ = detector.findPosition(image, draw=False)

        # 创建OpenCV画布
        canvas = cv2.resize(image, (WIN_WIDTH, WIN_HEIGHT))

        # 叠加标准遮罩帧
        overlay = masked_frames[std_mask_idx]
        if overlay is not None:
            overlay = cv2.resize(overlay, (WIN_WIDTH, WIN_HEIGHT))
            if overlay.shape[2] == 4:
                alpha = overlay[:, :, 3] / 255.0
                for c in range(3):
                    canvas[:, :, c] = (overlay[:, :, c] * alpha +
                                      canvas[:, :, c] * (1 - alpha))

        # 获取骨架点
        std_points = []
        if json_line_idx < len(std_json_frames):
            frame_data = std_json_frames[json_line_idx]
            poses = np.array(frame_data["poses"]).reshape(33, 3)
            std_points = [
                (int(poses[l][0] * (WIN_WIDTH / original_std_size[0])),
                 int(poses[l][1] * (WIN_HEIGHT / original_std_size[1])))
                for l in POSE_LANDMARKS.values()
            ]

        real_points = []
        if sketList:
            cam_w, cam_h = image.shape[1], image.shape[0]
            real_points = [
                (sketList[l][0] * (WIN_WIDTH / cam_w),
                 sketList[l][1] * (WIN_HEIGHT / cam_h))
                if l < len(sketList) else (0, 0)
                for l in POSE_LANDMARKS.values()
            ]

        # 匹配度检测
        if std_points and real_points:
            match_score = draw_points_to_reach(canvas, std_points, real_points, threshold=50)

            # 动作计时逻辑
            if pose_start_time is None:
                pose_start_time = time.time()

            # 评分触发条件
            if match_score > 0.3:
                elapsed = time.time() - pose_start_time
                if elapsed < 1.5:
                    feedback_sys.add_feedback("perfect", 10)
                elif elapsed < 2.5:
                    feedback_sys.add_feedback("great", 5)
                else:
                    feedback_sys.add_feedback("good", 3)

                # 推进到下一动作
                if json_line_idx < len(std_json_frames) - 1:
                    json_line_idx += 1
                    std_mask_idx = std_json_frames[json_line_idx]["frame_idx"] + 1
                    print(f"跳转到第 {json_line_idx} 帧")
                pose_start_time = None

        # 转换到Pygame显示
        canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        pygame_surface = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0,1))
        screen.blit(pygame_surface, (0, 0))

        # 绘制界面元素
        # 1. 显示"Timed Mode"标题
        title_surf = FONT_CONFIG["title"].render("Timed Mode", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(WIN_WIDTH//2, 30))
        screen.blit(title_surf, title_rect)

        # 2. 显示倒计时
        time_text = FONT_CONFIG["score"].render(f"Time Left: {remaining_time}", True, (255, 215, 0))
        time_rect = time_text.get_rect(topright=(WIN_WIDTH - 20, 20))
        screen.blit(time_text, time_rect)

        # 更新反馈系统（原有逻辑不变）
        feedback_sys.update_feedbacks()
        feedback_sys.draw_feedbacks(screen)
        feedback_sys.draw_score(screen)

        # 刷新显示
        pygame.display.flip()
        clock.tick(FRAME_RATE)

    # 清理资源
    cap.release()
    mixer.music.stop()
    pygame.quit()

if __name__ == "__main__":
    main()