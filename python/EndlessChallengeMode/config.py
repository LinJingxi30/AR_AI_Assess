# -*- coding: utf-8 -*-            
# @Author :
# @Time : 2025/3/19 12:26
# @Content :
import sys
from pathlib import Path
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(MEDIA_PIPE_ROOT))
import os
os.chdir(MEDIA_PIPE_ROOT)

import pygame
pygame.init()
# 音频配置
SOUND_FILES = {
    "perfect": "gameAssets/sounds/perfect2.wav",
    "great": "gameAssets/sounds/great2.wav",
    "good": "gameAssets/sounds/good2.wav",
    "gameover": "gameAssets/sounds/good2.wav",
    "ouch": "gameAssets/sounds/awkward.mp3",
}

# 字体配置
FONT_CONFIG = {
    "feedback": pygame.font.Font("gameAssets/fonts/impact2.otf", 72),
    "score": pygame.font.Font("gameAssets/fonts/arial_bold2.otf", 36),
    "title": pygame.font.Font("gameAssets/fonts/Windhavi.otf", 36)
}

pygame.display.set_mode((1, 1))  # 最小化窗口，用以初始化heart_icon

VISUAL_CONFIG = {
    "heart_icon": pygame.transform.scale(pygame.image.load("gameAssets/icons/star.png").convert_alpha(), (30, 30)),  # 加载生命图标
    "arrow": {
        "normal_color": (0, 0, 255),    # BGR红色   rgb(255, 0, 0)
        "achieve_color": (0, 255, 0),   # BGR绿色   rgb(0, 255, 0)
        "thickness": 4,
        "size": 20,
        "num_arrows": 3,
        "checkmark_size": 15
    },
    "gradient": {
        "max_radius": 30,
        "steps": 5,  # 减少 steps 以提高性能
        "std_color": (255, 191, 0),     # BGR标准点颜色   rgb(0, 191, 255)
        "real_color": (72, 209, 204)    # BGR实时点颜色   rgb(204, 209, 72)
    },
    "feedback_colors": {
        "perfect": (0, 255, 0),
        "great": (255, 215, 0),
        "good": (255, 69, 0)
    }
}

POSE_LANDMARKS = {
    "左手掌": 15,
    "右手掌": 16,
    "左脚踝": 27,
    "右脚踝": 28
}

# 相较限时模式，添加
TIMER_CONFIG = {
    "round_duration": 25,  # 回合时长（秒）
    "max_lives": 3,        # 最大生命值
    "bar_width": 200,      # 读条宽度
    "bar_height": 20       # 读条高度
}

# @A last new line here:
