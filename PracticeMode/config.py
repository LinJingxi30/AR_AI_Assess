# -*- coding: utf-8 -*-            
# @Author :
# @Time : 2025/3/19 12:26
# @Content :

VISUAL_CONFIG = {
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
    }
}

POSE_LANDMARKS = {
    "左手掌": 15,
    "右手掌": 16,
    "左脚踝": 27,
    "右脚踝": 28
}

# @A last new line here:
