import sys
from pathlib import Path
PY_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PY_ROOT))   # 添加 Python 根目录到模块搜索路径中
sys.path.append(str(Path(__file__).resolve().parent)) 
from guider import Guider
from animator import Animator
from pregame_align import PreAlignerPoints
import pygame


from Config import STD_SPORTS_RESULTS_ROOT
import utils.CamUtils as CamUtils
from utils.DataSender import DataSender

PRE_GAME_ALIGN_PATHS = {
    "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "pregame_align" / "pre.json",
    "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "pregame_align",
    "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
}

PRE_GAME_CLIP_PATHS = {
    "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "pregame_clip" / "preclip.json",
    "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "pregame_clip",
    "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
}

POSTURE_1_PATHS = {
    "MOVE_1": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_1" / "std.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_1",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_2": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_2" / "std.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_2",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_3": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_3" / "std.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_3",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
}

POSTURE_2_PATHS = {
    "MOVE_1": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_1" / "std.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_1",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_2": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_2" / "std.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_2",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_3": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_3" / "std.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_3",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
}

FULL_PATHS = {
    "PRE_GAME_ALIGN": PRE_GAME_ALIGN_PATHS,
    "POSTURE_1": POSTURE_1_PATHS,
    "POSTURE_2": POSTURE_2_PATHS,
}


if __name__ == "__main__":
    # 创建实例
    DEBUG = 0
    anim = Animator()
    pre_align = PreAlignerPoints(_paths=PRE_GAME_ALIGN_PATHS, debug=DEBUG)
    pre_clip = Guider(paths=PRE_GAME_CLIP_PATHS, debug=DEBUG)
    p1m1 = Guider(paths=FULL_PATHS["POSTURE_1"]["MOVE_1"], debug=DEBUG)
    p1m2 = Guider(paths=FULL_PATHS["POSTURE_1"]["MOVE_2"], debug=DEBUG)
    p1m3 = Guider(paths=FULL_PATHS["POSTURE_1"]["MOVE_3"], debug=DEBUG)
    p2m1 = Guider(paths=FULL_PATHS["POSTURE_2"]["MOVE_1"], debug=DEBUG)
    p2m2 = Guider(paths=FULL_PATHS["POSTURE_2"]["MOVE_2"], debug=DEBUG)
    p2m3 = Guider(paths=FULL_PATHS["POSTURE_2"]["MOVE_3"], debug=DEBUG)


    # 0. 用户对齐指引
    DataSender.send_control("PLAY_AUDIO",flag = 1)
    DataSender.send_control("PLAY_AUDIO",flag = 2)
    DataSender.send_control("PLAY_AUDIO",flag = 3)
    anim.animate_title(text="欢迎来到太极指导系统", duration=1.0)

    pre_align.main_loop_with_voice()

    DataSender.send_control("PLAY_AUDIO",flag = 11)
    DataSender.send_control("PLAY_AUDIO",flag = 12)

    anim.running = True
    anim.camera = CamUtils.camera_init(resolution=(1280,720))
    anim.animate_title(text="3", duration=1.0)
    anim.animate_title(text="2", duration=1.0)
    anim.animate_title(text="1", duration=1.0)

    pre_clip.main_loop()

    DataSender.send_control("PLAY_AUDIO",flag = 14)

    # 1. 招式一
    anim.running = True
    anim.camera = CamUtils.camera_init(resolution=(1280,720))
    anim.animate_title(text="3", duration=1.0)
    anim.animate_title(text="2", duration=1.0)
    anim.animate_title(text="1", duration=1.0)
    anim.animate_title(text="招式一：AAAA！", duration=1.0)
    p1m1.main_loop()
    p1m2.main_loop()
    p1m3.main_loop()
    anim.camera = CamUtils.camera_init(resolution=(1280, 720))
    anim.running = True
    anim.animate_summary(
        total_score=p1m1.score + p1m2.score + p1m3.score,
        move_scores=[p1m1.score, p1m2.score, p1m3.score],
        duration=2.5,
    )

    # 2. 招式二
    anim.running = True
    anim.animate_title(text="招式二：BBBB！", duration=1.5)
    p2m1.main_loop()
    p2m2.main_loop()
    p2m3.main_loop()
    anim.camera = CamUtils.camera_init(resolution=(1280, 720))
    anim.running = True
    anim.animate_summary(
        total_score=p2m1.score + p2m2.score + p2m3.score,
        move_scores=[p2m1.score, p2m2.score, p2m3.score],
        duration=2.5,
    )

    pygame.quit()
