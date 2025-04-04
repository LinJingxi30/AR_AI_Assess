from Config.common_data import COLOR, WIN_SIZE, STD_POSE_KEYPOINTS, STD_POSE_CONNECTIONS, STD_FILL_CONNECTIONS
from Config.paths import MEDIA_PIPE_ROOT
from pathlib import Path


win_width, win_height = WIN_SIZE

# [请勿修改] 根据窗口大小调整缩放比例，用于自动缩放节点半径和线条粗细
scale2 = win_width / win_width

# [自定义] 人物占窗口比例
WIN_OCCUPY_RATIO = 0.4
# [请勿修改] 用于自动坐标缩放，以及位置调整（pose 大致 bndbox 200*400）
scale = win_height * WIN_OCCUPY_RATIO / 400  # 标准骨架缩放比例 percenth = winh * 0.8, s = percenth / poseh = winh * 0.8/ poseh  

THRESHOLD = {
    "sample": 1000,  # 采样阈值
    "overlay": 200,   # 遮罩阈值，越大越
    "color_glow": COLOR["lightyellow"],  # 轮廓边缘发光颜色
    "bg_opacity": 0.5,  # 背景透明度
    "glow_thickness": 10 * scale2,  # 发光边缘的厚度
    "std_sket_scale": scale,
    "std_sket_center_pos": (win_width // 2, win_height - 400 * scale * 0.5),  # 标准骨架中心位置，处在窗口底部上移0.2身高
}


BLACK_SKET_CONFIG = {
    "color_head": COLOR["black"],
    "color_fill": COLOR["black"],
    "color_point": COLOR["black"],
    "color_line": COLOR["black"],
    "radius": 19 * scale2,
    "radius_head": 42 * scale2,
    "thickness": 34 * scale2,
    "key_points": STD_POSE_KEYPOINTS,
    "connections": STD_POSE_CONNECTIONS,
    "fill_connections": STD_FILL_CONNECTIONS,
}


PATHS = {
    "std_video": Path(MEDIA_PIPE_ROOT) / "Static\\video\\新太极彩色.mp4",  # 标准视频路径
    # "std_video_cut": Path(MEDIA_PIPE_ROOT) / "Static\\video\\C0073_cut.mp4",  # 标准视频裁剪路径
    "std_frames_save_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/full_std_frames",  # 完整流帧保存路径
    "sampled_frames_save_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/sampled_std_frames",  # 抽样后帧保存路径
    "std_masked_frames_save_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/masked_sampled_std_frames",  # 抽样后、遮罩后帧保存路径
    "std_json_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/full_std_frames.json",  # 完整流JSON文件路径
    "sampled_json_dir": Path(MEDIA_PIPE_ROOT) / "StdProcess/sampled_std_frames.json",  # 抽样后的JSON文件路径
}


StdSportsResults = Path(MEDIA_PIPE_ROOT) / "StdSportsResults"  # 标准运动结果路径
TaiChiFolder = Path(StdSportsResults) / "TaiChi"  # 太极文件夹路径
AerobicsFolder = Path(StdSportsResults) / "Aerobics"  # 健美操文件夹路径
YogaFolder = Path(StdSportsResults) / "Yoga"  # 瑜伽文件夹路径


TaiChiPaths = {
    "std_video": Path(MEDIA_PIPE_ROOT) / "Static\\video\\太极绿幕剪裁.mp4",  # 标准视频路径
    "std_frames_save_dir": Path(TaiChiFolder) / "full_std_frames",  # 完整流帧保存路径
    "sampled_frames_save_dir": Path(TaiChiFolder) / "sampled_std_frames",  # 抽样后帧保存路径
    "std_masked_frames_save_dir": Path(TaiChiFolder) / "masked_sampled_std_frames",  # 抽样后、遮罩后帧保存路径
    "std_json_dir": Path(TaiChiFolder) / "full_std_frames.json",  # 完整流JSON文件路径
    "sampled_json_dir": Path(TaiChiFolder) / "sampled_std_frames.json",  # 抽样后的JSON文件路径
}

AerobicsPaths = {
    "std_video": Path(MEDIA_PIPE_ROOT) / "Static\\video\\健美操.mp4",  # 标准视频路径
    "std_frames_save_dir": Path(AerobicsFolder) / "full_std_frames",  # 完整流帧保存路径
    "sampled_frames_save_dir": Path(AerobicsFolder) / "sampled_std_frames",  # 抽样后帧保存路径
    "std_masked_frames_save_dir": Path(AerobicsFolder) / "masked_sampled_std_frames",  # 抽样后、遮罩后帧保存路径
    "std_json_dir": Path(AerobicsFolder) / "full_std_frames.json",  # 完整流JSON文件路径
    "sampled_json_dir": Path(AerobicsFolder) / "sampled_std_frames.json",  # 抽样后的JSON文件路径
}

YogaPaths = {
    "std_video": Path(MEDIA_PIPE_ROOT) / "Static\\video\\瑜伽原.mp4",  # 标准视频路径
    "std_frames_save_dir": Path(YogaFolder) / "full_std_frames",  # 完整流帧保存路径
    "sampled_frames_save_dir": Path(YogaFolder) / "sampled_std_frames",  # 抽样后帧保存路径
    "std_masked_frames_save_dir": Path(YogaFolder) / "masked_sampled_std_frames",  # 抽样后、遮罩后帧保存路径
    "std_json_dir": Path(YogaFolder) / "full_std_frames.json",  # 完整流JSON文件路径
    "sampled_json_dir": Path(YogaFolder) / "sampled_std_frames.json",  # 抽样后的JSON文件路径
}

StdSportsResultsPATHS = {
    "太极": TaiChiPaths,
    "健美操": AerobicsPaths,
    "瑜伽": YogaPaths,
}