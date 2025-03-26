import os

"""
公用数据，避免代码段重复
"""


# 统一窗口大小
# win_width, win_height = 1920, 1080
# win_width, win_height = 1600, 900
win_width, win_height = 1280, 720
# win_width, win_height = 640, 480
WIN_SIZE = (win_width, win_height)


# 定义关节连接关系（示例，根据实际数据结构调整）
POSE_CONNECTIONS = [
    (11, 12),  # 左肩 -> 右肩
    (11, 13),  # 左肩 -> 左肘
    (12, 14),  # 右肩 -> 右肘
    (13, 15),  # 左肘 -> 左手
    (14, 16),  # 右肘 -> 右手
    (11, 23),  # 左肩 -> 左髋
    (12, 24),  # 右肩 -> 右髋
    (23, 25),  # 左髋 -> 左膝
    (24, 26),  # 右髋 -> 右膝
    (23, 24),  # 左髋 -> 右髋
    (25, 27),  # 左膝 -> 左脚
    (26, 28),  # 右膝 -> 右脚
]


# 颜色 BGR
# ! 注意：OpenCV 默认使用 BGR 格式，非 RGB
COLOR = {   
    "black": (0, 0, 0),                 # rgb(0, 0, 0)
    "white": (255, 255, 255),           # rgb(255, 255, 255)
    "red": (0, 0, 255),                 # rgb(255, 0, 0)
    "green": (0, 255, 0),               # rgb(0, 255, 0)
    "blue": (150, 50, 50),              # rgb(50, 50, 150)
    "babyblue": (240, 207, 137),        # rgb(137, 207, 240)
    "lightyellow": (137, 207, 240),     # rgb(240, 207, 137)
    "pink": (255, 0, 255),              # rgb(255, 0, 255)
    "yellow": (0, 255, 255)             # rgb(255, 255, 0)
}


STD_POSE_KEYPOINTS = {
    "头部": 0,
    
    "左肩": 11,
    "右肩": 12,
    
    "左肘": 13,
    "右肘": 14,
    
    "左手掌": 15,
    "右手掌": 16,

    "左食指": 17,
    "右食指": 18,

    "左小指": 19,
    "右小指": 20,
    
    "左髋": 23,
    "右髋": 24,
    
    "左膝": 25,
    "右膝": 26,

    "左脚踝": 27,
    "右脚踝": 28,
    
    "左脚跟": 29,
    "右脚跟": 30,
    
    "左脚尖": 31,
    "右脚尖": 32,

}


STD_FILL_CONNECTIONS = {
    "躯干": ("左肩", "右肩", "左髋", "右髋"),
}


STD_POSE_CONNECTIONS = {
    "脖子": ("头部", "脖子根"),

    "肩膀": ("左肩","右肩"),

    "左大臂": ("左肩", "左肘"),
    "右大臂": ("右肩", "右肘"),

    "左小臂": ("左肘", "左手掌"),
    "右小臂": ("右肘", "右手掌"),

    "左手": ("左手掌", "左手心"),
    "右手": ("右手掌", "右手心"),

    "左躯干": ("左肩", "左髋"),
    "右躯干": ("右肩", "右髋"),

    "臀部": ("左髋", "右髋"),

    "左大腿": ("左髋", "左膝"),
    "右大腿": ("右髋", "右膝"),

    "左小腿": ("左膝", "左脚跟"),
    "右小腿": ("右膝", "右脚跟"),

    "左脚背": ("左脚踝", "左脚尖"),
    "右脚背": ("右脚踝", "右脚尖"),

    "左跟腱": ("左脚跟", "左脚踝"),
    "右跟腱": ("右脚跟", "右脚踝"),

    "左脚底": ("左脚跟", "左脚尖"),
    "右脚底": ("右脚跟", "右脚尖"),
}



# 一个默认的骨架绘制配置
DRAW_SKET_OVERALL_CONFIG = {
    "color_head": COLOR["lightyellow"],
    "color_fill": COLOR["lightyellow"],
    "color_point": COLOR["black"],
    "color_line": COLOR["babyblue"],
    "radius": 22,
    "radius_head": 64,
    "thickness": 45,
    "key_points": STD_POSE_KEYPOINTS,
    "connections": STD_POSE_CONNECTIONS,
    "fill_connections": STD_FILL_CONNECTIONS,
}


def clear_directory(directory):
    """
    清空指定文件夹内所有文件。
    """
    if os.path.exists(directory):
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                os.remove(item_path)

if __name__ == "__main__":
    pass