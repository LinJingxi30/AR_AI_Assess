import time, math
import pygame
from pygame import mixer

from Config.common_data import WIN_SIZE
from .config import *


WIN_WIDTH, WIN_HEIGHT = WIN_SIZE


class FeedbackSystem:
    """实时反馈管理系统"""
    def __init__(self):
        self.active_feedbacks = []
        self.total_score = 0
        self.score_history = []
        self.last_score_time = 0
        self.init_audio()

    def init_audio(self):
        """初始化音频系统"""
        global SOUNDS
        SOUNDS = {name: mixer.Sound(file) for name, file in SOUND_FILES.items()}

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
