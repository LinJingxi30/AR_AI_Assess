import sys
import json
import time
from pathlib import Path

import cv2
import numpy as np
import pygame
from pygame.locals import *
# 配置常量
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(MEDIA_PIPE_ROOT))

import mediapipe as mp
from cvzone.PoseModule import PoseDetector
from Config.common_data import FPS, WIN_SIZE
from Config.paths import SPORTS_TYPE_PATH
from ProcessKit import (
    Json2PreviewClass as j2pc,
    move_coords_by_center_to_pos_set_pts,
    get_center_pos_from_pts,
    Draw
)
from TimedChallengeMode.fbsys import FeedbackSystem
from TimedChallengeMode.config import *

WIN_WIDTH, WIN_HEIGHT = WIN_SIZE


class TimedChallengeMode:
    def __init__(self, sport_type="太极", challenge_time=60, distance_threshold=50):
        # 初始化配置参数
        self.setup_config(sport_type, challenge_time, distance_threshold)
        
        # 初始化系统资源
        self.load_resources()
        
        # 初始化Pygame环境
        self.init_pygame()
        
        # 初始化运行状态
        self.running = True
        self.start_ticks = pygame.time.get_ticks()
        
        # 初始化当前标准数据索引
        self.current_std_index = 0  

    def setup_config(self, sport_type, challenge_time, distance_threshold):
        """配置基本运行参数"""
        self.sport_type = sport_type
        self.challenge_time = challenge_time
        self.distance_threshold = distance_threshold
        
        # 运动数据路径配置
        if self.sport_type not in SPORTS_TYPE_PATH:
            print(f"未找到运动类型: {self.sport_type}，使用默认类型: 太极")
            self.sport_type = "太极"
            
        sport_path = SPORTS_TYPE_PATH[self.sport_type]
        self.std_json_path = sport_path / "sampled_std_frames.json"
        self.std_frames_dir = sport_path / "masked_sampled_std_frames"

    def load_resources(self):
        """加载所有必要资源"""
        # 标准数据加载
        self.load_standard_data()
        
        # 摄像头初始化
        self.init_camera()
        
        # 姿势检测模型初始化
        self.init_pose_detection()
        
        # 反馈系统初始化
        self.feedback_sys = FeedbackSystem()

    def init_pygame(self):
        """初始化Pygame显示和音频系统"""
        pygame.init()
        self.screen = pygame.display.set_mode(WIN_SIZE, DOUBLEBUF | RESIZABLE)
        pygame.display.set_caption("Motion Coach Pro")
        
        # 音频系统初始化
        self.init_audio()

    def init_audio(self):
        """初始化背景音乐"""
        pygame.mixer.music.load("gameAssets/sounds/SJTUbgm.mp3")
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.play(-1)

    def load_standard_data(self):
        """加载标准动作数据"""
        # 加载JSON姿势数据
        self.std_poses = self.load_json_data()
        
        # 加载遮罩帧
        self.std_frames = self.load_masked_frames()

    def load_json_data(self):
        """从JSON文件加载标准姿势数据"""
        try:
            with open(self.std_json_path) as f:
                return [self.process_json_line(line) for line in f if line.strip()]
        except FileNotFoundError:
            print(f"错误：未找到标准数据文件 {self.std_json_path}")
            return []

    def process_json_line(self, line):
        """处理单行JSON数据"""
        data = json.loads(line)
        frame_info = {
            "frame_idx": self.extract_frame_index(data["image"]),
            "poses": self.normalize_pose_data(data)
        }
        return frame_info

    @staticmethod
    def extract_frame_index(filename):
        """从文件名中提取帧索引"""
        return int(filename.split('_')[-1].split('.')[0])

    def normalize_pose_data(self, data):
        """标准化姿势坐标到窗口尺寸"""
        SCALE_FACTOR = 1  # 可根据实际需要调整
        poses = np.zeros((33, 3), dtype=np.int32)
        
        # 关键点映射
        keypoints = {
            15: data["points"]["left_h"],
            16: data["points"]["right_h"],
            27: data["points"]["left_f"],
            28: data["points"]["right_f"]
        }
        
        # 填充关键点数据
        for idx, pos in keypoints.items():
            x = int(pos[0] * SCALE_FACTOR)
            y = int(pos[1] * SCALE_FACTOR)
            poses[idx] = (x, y, 0)
            
        return poses.tolist()

    def load_masked_frames(self):
        """加载所有遮罩帧"""
        frames = []
        for frame_idx in range(912):  # 假设固定912帧
            frame_path = self.std_frames_dir / f"C0076_{frame_idx:04d}.png"
            frame = cv2.imread(str(frame_path), cv2.IMREAD_UNCHANGED)
            if frame is not None:
                frames.append(cv2.resize(frame, WIN_SIZE))
        return frames

    def init_camera(self):
        """初始化摄像头设备"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("摄像头初始化失败")

    def init_pose_detection(self):
        """初始化姿势检测模型"""
        self.pose_detector = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def run(self):
        """主运行循环"""
        while self.running:
            self.handle_events()
            self.process_frame()
            self.render_display()
            
            # 控制帧率
            pygame.time.Clock().tick(FPS)
            
        self.cleanup()

    def handle_events(self):
        """处理系统事件"""
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False

    def process_frame(self):
        """处理单帧画面"""
        # 获取摄像头画面
        success, frame = self.cap.read()
        if not success:
            return
            
        # 保存当前帧供后续使用
        self.current_frame = frame.copy()
        
        # 姿势检测
        landmarks = self.detect_landmarks(frame)
        
        # 获取实时关键点
        realtime_points = self.get_realtime_points(frame, landmarks)
        
        # 获取标准关键点
        std_points = self.get_standard_points()
        
        # 进行姿势匹配判断
        self.evaluate_posture(std_points, realtime_points)

    def detect_landmarks(self, frame):
        """检测姿势关键点"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose_detector.process(rgb_frame)
        return results.pose_landmarks

    def get_realtime_points(self, frame, landmarks):
        """获取实时关键点坐标"""
        if not landmarks:
            return []
            
        h, w = frame.shape[:2]
        return [
            (int(lm.x * w), int(lm.y * h))
            for lm in landmarks.landmark
        ]

    def get_standard_points(self):
        """获取当前标准关键点"""
        current_data = self.std_poses[self.current_std_index]
        return [
            (max(0, min(WIN_WIDTH-1, x)), max(0, min(WIN_HEIGHT-1, y)))
            for x, y, _ in current_data["poses"]
        ]

    def evaluate_posture(self, std_points, real_points):
        """姿势匹配度评估"""
        # 计算各关键点距离
        distances = [
            np.linalg.norm(np.array(std) - np.array(real))
            for std, real in zip(std_points, real_points)
        ]
        
        # 计算匹配分数
        total_distance = sum(distances)
        max_possible = len(std_points) * self.distance_threshold
        self.match_score = max(0, 1 - total_distance/max_possible) if max_possible else 0
        
        # 更新反馈系统
        self.update_feedback()

    def update_feedback(self):
        """根据当前分数更新反馈"""
        if self.match_score > 0.8:
            self.feedback_sys.add_feedback("perfect", 10)
        elif self.match_score > 0.6:
            self.feedback_sys.add_feedback("great", 7)
        else:
            self.feedback_sys.add_feedback("good", 3)

    def render_display(self):
        """渲染显示画面"""
        # 绘制摄像头画面
        self.draw_camera_view()
        
        # 绘制标准覆盖层
        self.draw_standard_overlay()
        
        # 绘制UI元素
        self.draw_ui()
        
        # 更新显示
        pygame.display.flip()

    def draw_camera_view(self):
        """绘制摄像头实时画面"""
        # 使用self.current_frame（已在process_frame中赋值）
        rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        pygame_frame = pygame.surfarray.make_surface(rgb_frame.swapaxes(0,1))
        self.screen.blit(pygame_frame, (0,0))

    def draw_standard_overlay(self):
        """绘制标准动作覆盖层"""
        if self.current_std_index < len(self.std_frames):
            overlay = self.std_frames[self.current_std_index]
            # 检查overlay是否为有效的ndarray（二维或三维）
            if isinstance(overlay, np.ndarray) and overlay.ndim in [2, 3]:
                overlay_surface = pygame.surfarray.make_surface(overlay.swapaxes(0,1))
                self.screen.blit(overlay_surface, (0,0))
            # ...可以添加 else 处理或直接跳过...

    def draw_ui(self):
        """绘制用户界面元素"""
        # 绘制倒计时
        self.draw_timer()
        
        # 绘制得分
        self.draw_score()
        
        # 绘制反馈信息
        self.feedback_sys.draw(self.screen)

    def draw_timer(self):
        """绘制剩余时间"""
        elapsed = (pygame.time.get_ticks() - self.start_ticks) // 1000
        remaining = max(0, self.challenge_time - elapsed)
        text = FONT_CONFIG["timer"].render(f"Time: {remaining}s", True, (255,255,255))
        self.screen.blit(text, (10, 10))

    def draw_score(self):
        """绘制当前得分"""
        text = FONT_CONFIG["score"].render(f"Score: {self.feedback_sys.total_score}", True, (255,215,0))
        self.screen.blit(text, (WIN_WIDTH-200, 10))

    def cleanup(self):
        """资源清理"""
        self.cap.release()
        pygame.mixer.music.stop()
        pygame.quit()

# 其他辅助类和函数保持不变（根据实际需要调整）
if __name__ == "__main__":
    # 创建并运行TimedChallengeMode实例
    challenge = TimedChallengeMode(sport_type="太极", challenge_time=600, distance_threshold=50)
    challenge.run()