import json
import sys
from pathlib import Path
PY_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PY_ROOT))   # 添加 Python 根目录到模块搜索路径中
sys.path.append(str(Path(__file__).resolve().parent)) 
from guider import Guider
from animator import Animator
from pregame_align import PreAlignerPoints
import pygame
import argparse


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
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_1" / "std1-1.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_1",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_2": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_2" / "std1-2.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_2",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_3": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_3" / "std1-3.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_1" / "move_3",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
}

POSTURE_2_PATHS = {
    "MOVE_1": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_1" / "std2-1.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_1",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_2": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_2" / "std2-2.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_2",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_3": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_3" / "std2-3.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_2" / "move_3",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
}

POSTURE_3_PATHS = {
    "MOVE_1": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_3" / "move_1" / "std3-1.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_3" / "move_1",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "MOVE_2": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_3" / "move_2" / "std3-2.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_3" / "move_2",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    # "MOVE_3": {
    #     "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_3" / "move_3" / "std3-3.json",
    #     "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "Posture_3" / "move_3",
    #     "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    # },
}

FULL_PATHS = {
    "POSTURE_1": POSTURE_1_PATHS,
    "POSTURE_2": POSTURE_2_PATHS,
    "POSTURE_3": POSTURE_3_PATHS,
}

ANIMATOR_CONFIG = {
    # 招式X：xxxx
    "标题": {
        "字体": str(Path(PY_ROOT) / "gameAssets" / "fonts" / "SourceHanSerifCN-Bold.otf"),
        "字号": 80,
        "颜色": (255, 230, 0),  # pygame 用的直接 RGB(255, 230, 0)
        "位置": (180, 60),
    },
    "计分": {
        "文字": "当前动作分：",
        "字体": str(Path(PY_ROOT) / "gameAssets" / "fonts" / "SmileySans-Oblique.ttf"),
        "字号": 40,
    },
    # todo:: 招式得分
}


def user_jsons_combine(id, save_path):
    """
    遍历 FULL_PATHS 中所有 posture 和 move，
    组合各个 JSON 文件的数据为如下格式：
    
    {
      "description": "",
      "data": {
          "p1": {
              "m1": [ {...}, {...}, ... ],
              "m2": [ ... ],
              ...
          },
          "p2": { ... },
          ...
      }
    }
    
    将生成的 JSON 数据写入 save_path 目录下的 differences-<id>.json 文件中。
    """
    combined_data = {
        "description": "",
        "data": {}
    }
    # 定义 posture 映射，比如 POSTURE_1 -> p1, POSTURE_2 -> p2, POSTURE_3 -> p3
    posture_mapping = {
        "POSTURE_1": "p1",
        "POSTURE_2": "p2",
        "POSTURE_3": "p3",
        "POSTURE_4": "p4",
    }
    
    for posture_key, moves in FULL_PATHS.items():
        p_key = posture_mapping.get(posture_key, posture_key)
        combined_data["data"][p_key] = {}
        for move_key, move_info in moves.items():
            # 将 MOVE_1 转换为 m1
            m_key = move_key.lower().replace("move_", "m")
            json_path = move_info.get("标准 JSON 文件路径")
            records = []
            if json_path and Path(json_path).exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                record = json.loads(line)
                                records.append(record)
                            except Exception as e:
                                print(f"解析 {json_path} 行数据错误：", e)
            combined_data["data"][p_key][m_key] = records

    # 将合成的数据直接写入 save_path 下的 differences-<id>.json 文件
    output_file = Path(save_path) / f"differences-{id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)
    print(f"组合后的 JSON 已保存到 {output_file}", file=sys.stderr)


# 添加命令行参数解析
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unique_id", required=True, help="运动记录的唯一ID")
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    unique_id = args.unique_id

    # 创建实例时传入unique_id
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
    p3m1 = Guider(paths=FULL_PATHS["POSTURE_3"]["MOVE_1"], debug=DEBUG)
    p3m2 = Guider(paths=FULL_PATHS["POSTURE_3"]["MOVE_2"], debug=DEBUG)

    # 0. 用户对齐指引
    DataSender.send_control("PLAY_AUDIO",flag = 1)
    anim.animate_title(text="欢迎来到3A·元运动指南", duration=1.0, config=ANIMATOR_CONFIG)

    pre_align.main_loop_with_voice()

    DataSender.send_control("PLAY_AUDIO",flag = 6)

    anim.running = True
    anim.camera = CamUtils.camera_init(resolution=(1280,720))
    anim.animate_title(text="3", duration=1.0, config=ANIMATOR_CONFIG)
    anim.animate_title(text="2", duration=1.0, config=ANIMATOR_CONFIG)
    anim.animate_title(text="1", duration=1.0, config=ANIMATOR_CONFIG)

    pre_clip.main_loop()

    DataSender.send_control("PLAY_AUDIO",flag = 8)

    # 1. 招式一
    anim.running = True
    anim.camera = CamUtils.camera_init(resolution=(1280,720))
    anim.animate_title(text="3", duration=1.0, config=ANIMATOR_CONFIG)
    anim.animate_title(text="2", duration=1.0, config=ANIMATOR_CONFIG)
    anim.animate_title(text="1", duration=1.0, config=ANIMATOR_CONFIG)
    anim.animate_title(text="招式一：起势！", duration=1.0, config=ANIMATOR_CONFIG)
    p1m1.main_loop()
    p1m2.main_loop()
    p1m3.main_loop()
    anim.camera = CamUtils.camera_init(resolution=(1280, 720))
    anim.running = True
    anim.animate_summary(
        total_score=p1m1.score + p1m2.score + p1m3.score,
        move_scores=[p1m1.score, p1m2.score, p1m3.score],
        duration=2.5,
        config = ANIMATOR_CONFIG
    )

    # 2. 招式二
    anim.running = True
    anim.animate_title(text="招式二：左右野马分鬃！", duration=1.5, config=ANIMATOR_CONFIG)
    p2m1.main_loop()
    p2m2.main_loop()
    p2m3.main_loop()
    anim.camera = CamUtils.camera_init(resolution=(1280, 720))
    anim.running = True
    anim.animate_summary(
        total_score=p2m1.score + p2m2.score + p2m3.score,
        move_scores=[p2m1.score, p2m2.score, p2m3.score],
        duration=2.5,
        config = ANIMATOR_CONFIG
    )

    # 3. 招式三
    anim.running = True
    anim.animate_title(text="招式三：白鹤亮翅！", duration=1.5, config=ANIMATOR_CONFIG)
    p3m1.main_loop()
    p3m2.main_loop()
    anim.camera = CamUtils.camera_init(resolution=(1280, 720))
    anim.running = True
    anim.animate_summary(
        total_score=p3m1.score + p3m2.score,
        move_scores=[p3m1.score, p3m2.score],
        duration=2.5,
        config = ANIMATOR_CONFIG
    )

    # 把 differences-<id>.json 文件合并生成
    user_jsons_combine(id=unique_id, save_path=Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi")
    # todo:: 前端怎样拿到这个json？

    # 结束：发送动作分列表至前端
    DataSender.send_control(command="MOVE_SCORES", data=[p1m1.score, p1m2.score, p1m3.score, p2m1.score, p2m2.score, p2m3.score, p3m1.score, p3m2.score])

    pygame.quit()
