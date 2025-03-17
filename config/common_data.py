import os

"""
公用数据，避免代码段重复
"""


# 统一窗口大小
win_width, win_height = 1680, 1050
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