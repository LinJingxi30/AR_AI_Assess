from Config.common_data import COLOR, WIN_SIZE
from Config.paths import MEDIA_PIPE_ROOT
from pathlib import Path


STD_POSE_KEYPOINTS = {
    "头部": 0,
    
    "左肩": 11,
    "右肩": 12,
    
    "左肘": 13,
    "右肘": 14,
    
    "左手": 15,
    "右手": 16,
    
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

    "左小臂": ("左肘", "左手"),
    "右小臂": ("右肘", "右手"),

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


"""STD_POSE_LIST_CONNECTIONS = {
    "左肩 -> 右肩": (11, 12),

    "左肩 -> 左肘": (11, 13),
    "右肩 -> 右肘": (12, 14),

    "左肘 -> 左手": (13, 15),
    "右肘 -> 右手": (14, 16),

    "左肩 -> 左髋": (11, 23),
    "右肩 -> 右髋": (12, 24),

    "左髋 -> 右髋": (23, 24),
    "左髋 -> 左膝": (23, 25),
    "右髋 -> 右膝": (24, 26),
    
    "左膝 -> 左脚": (25, 27),
    "右膝 -> 右脚": (26, 28),

    "左脚": (31, 27),
    "右脚": (32, 28),
}
"""

BLACK_SKET_CONFIG = {
    "color_head": COLOR["black"],
    "color_fill": COLOR["black"],
    "color_point": COLOR["black"],
    "color_line": COLOR["black"],
    "radius": 18,
    "radius_head": 50,
    "thickness": 25,
    "connections": STD_POSE_CONNECTIONS,
    "fill_connections": STD_FILL_CONNECTIONS,
    "key_points": STD_POSE_KEYPOINTS,
}




win_width, win_height = WIN_SIZE

THRESHOLD = {
    "sample": 2000,  # 采样阈值
    "overlay": 2500,   # 遮罩阈值
    "color_glow": COLOR["lightyellow"],  # 轮廓边缘发光颜色
    "bg_opacity": 0.5,  # 背景透明度
    "glow_thickness": 10,  # 发光边缘的厚度
    "std_sket_scale": 2.4,  # 标准骨架缩放比例
    "std_sket_center_pos": (win_width // 2, win_height - 150),  # 标准骨架中心位置
}

PATHS = {
    "std_video": Path(MEDIA_PIPE_ROOT) / "Static/video/part2.mp4",  # 标准视频路径
    "std_frames_save_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/full_std_frames",  # 完整流帧保存路径
    "sampled_frames_save_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/sampled_std_frames",  # 抽样后帧保存路径
    "std_masked_frames_save_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/masked_sampled_std_frames",  # 抽样后、遮罩后帧保存路径
    "std_json_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/full_std_frames.json",  # 完整流JSON文件路径
    "sampled_json_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/sampled_std_frames.json",  # 抽样后的JSON文件路径
}