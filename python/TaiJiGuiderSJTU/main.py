import json
import sys
from pathlib import Path

PY_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PY_ROOT))  # 添加 Python 根目录到模块搜索路径中
sys.path.append(str(Path(__file__).resolve().parent))
from guider import Guider
from selector import Selector
from animator import Animator
from pregame_align import PreAlignerPoints
import pygame
import argparse
import time

from Config import STD_SPORTS_RESULTS_ROOT, WIN_SIZE
from utils.CamUtils import CameraUtil
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

# 运动项目选择-配置
SPORTS_SEL = {
    "texts": ["太极操", "八法五步", "24式太极拳"],
    "size": (140, 80),  # 按钮大小
    "color": (0, 155, 0),  # 按钮颜色
    "text_color": (255, 255, 255),  # 按钮文本颜色
    "font_scale": 1.0,
    "thickness": 4,  # 文本线宽，对中文字体无效
    "reach_threshold": 50,  # 按钮被按下的距离阈值
}

MODES_SEL = {
    "texts": ["学习", "训练"],
    "size": (150, 100),  # 按钮大小
    "color": (100, 100, 0),  # 按钮颜色
    "text_color": (255, 255, 255),  # 按钮文本颜色
    "font_scale": 1.2,
    "thickness": 4,  # 文本线宽，对中英文无效
    "reach_threshold": 50,  # 按钮被按下的距离阈值
}

REDO_SEL_CONFIG = {
    "texts": ["重做", "继续"],
    "size": (150, 100),
    "color": (0, 120, 200),
    "text_color": (255, 255, 255),
    "font_scale": 1.2,
    "thickness": 4,
    "reach_threshold": 50,
}

"""
todo:: 即便不做，时延也还好
法1：
    共享路径集；
法2：
    使用自己的json构建路径集，避免构建不需要的文件；
"""
TJC_Learning_PATHS = {
    "POSTURE_1": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p1.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "POSTURE_2": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p2.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "POSTURE_3": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p3.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "POSTURE_4": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p4.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "POSTURE_5": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p5.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "POSTURE_6": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p6.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "POSTURE_7": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p7.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "POSTURE_8": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p8.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
    "POSTURE_9": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "LearningMode" / "p9.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    },
}

TJC_Learning_CONFIG = {
    # todo:: 音频路径？
    "路径": TJC_Learning_PATHS,
    "片段标题": [
        "招式一：起势！",
        "招式二：金刚转体！",
        "招式三：左右云手！",
        "招式四：左右卷肱！",
        "招式五：丁步抱球！",
        "招式六：野马分鬃！",
        "招式七：白鹤亮翅！",
        "招式八：金鸡独立！",
        "招式九：收势！"
    ],
}

TJC_Training_PATHS = {
    "POSTURE_1": {
        "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC" / "TrainingMode" / "full.json",
        "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "TJC",
        "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
    }
}

TJC_Training_CONFIG = {
    "路径": TJC_Training_PATHS,
    "片段标题": ["完整演示"],
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


def combine_simple(id, save_path):
    """
    遍历 FULL_PATHS 中所有 posture 和 move，
    简化每一帧的数据为如下格式，每帧一行：

    {
       "frame": "C0076_0021.png",
       "points": {
           "left_h": [822, 930],
           "right_h": [484, 899],
           "left_f": [712, 1543],
           "right_f": [624, 1546]
       }
    }
    保存到 save_path 目录下的 differences_simple-<id>.json 文件中。
    """
    output_file = Path(save_path) / f"differences-{id}.json"
    with open(output_file, "w", encoding="utf-8") as fout:
        # 遍历所有 posture
        for posture_info in TJC_Learning_PATHS.values():
            json_path = posture_info.get("标准 JSON 文件路径")
            if json_path and Path(json_path).exists():
                with open(json_path, "r", encoding="utf-8") as fin:
                    for line in fin:
                        line = line.strip()
                        if not line or line.startswith("//"):
                            continue
                        try:
                            record = json.loads(line)
                            # 从记录中提取 image 和需要的关键点
                            frame_id = record.get("image", "")
                            pts = record.get("points", {})
                            simplified = {
                                "frame": frame_id,
                                "points": {
                                    "left_h": pts.get("left_h"),
                                    "right_h": pts.get("right_h"),
                                    "left_f": pts.get("left_f"),
                                    "right_f": pts.get("right_f")
                                }
                            }
                            fout.write(json.dumps(simplified, ensure_ascii=False, separators=(',', ':')) + "\n")
                        except Exception as e:
                            print(f"解析 {json_path} 出错：{e}", file=sys.stderr)
    print(f"简化后的 JSON 合并文件已保存到 {output_file}", file=sys.stderr)


# 添加命令行参数解析
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unique_id", required=True, help="运动记录的唯一ID")
    parser.add_argument("--rtmp_url", required=False, help="RTMP流地址")
    return parser.parse_args()


# main.py

def run_sport_routine(sport_type_config, anim, camera, pre_align, pre_clip, DEBUG, unique_id):
    # 招式实例列表
    routines = []
    for i in range(len(sport_type_config["路径"])):
        routines.append(Guider(camera=camera,uuid = unique_id, paths=sport_type_config["路径"][f"POSTURE_{i + 1}"], debug=DEBUG))

    # ?
    sys.stderr.write(f"Start\n")

    # 大标题
    DataSender.send_control("PLAY_AUDIO", flag=1)
    anim.animate_title(text="欢迎来到3A·元运动指南", duration=1.0, config=ANIMATOR_CONFIG)

    # 对齐四点指引
    pre_align.main_loop_with_voice()

    # 语音：好，接下来是对齐掩膜指引。
    DataSender.send_control("PLAY_AUDIO", flag=6)

    # 倒计时3s
    anim.animate_countdown(duration=1.0, config=ANIMATOR_CONFIG, cnt=3)

    # 对齐掩膜指引
    pre_clip.main_loop()

    # 语音：对齐掩膜指引完成，接下来正式开始。
    DataSender.send_control("PLAY_AUDIO", flag=8)

    # 倒计时3s
    anim.animate_countdown(duration=1.0, config=ANIMATOR_CONFIG, cnt=3)

    # 运动开始：遍历每个片段
    i = 0
    while i < len(sport_type_config["路径"]):
        # 语音：开始招式 i
        # todo:: 针对性的语音提示，比如播放的是完整演示or实际训练

        # 招式 i 标题
        anim.animate_title(text=sport_type_config["片段标题"][i], duration=1.0, config=ANIMATOR_CONFIG)
        # 招式 i 主循环
        routines[i].main_loop()

        # todo:: 用嵌入在config的条件来判断是否需要评分
        # 招式 i 评分
        anim.animate_summary(total_score=routines[i].score, move_scores=[routines[i].score], duration=2.5,
                             config=ANIMATOR_CONFIG)

        # sys.stderr.write(f"已执行片段 {i+1} finished.\n")   # 调试

        # ******** 添加重做/继续逻辑的开始 ********
        redo_selector = Selector(camera=camera,uuid = unique_id, buttons_config=REDO_SEL_CONFIG, debug=DEBUG,
                                 win_size=(WIN_SIZE[0], WIN_SIZE[1]))
        sys.stderr.write(str(redo_selector.buttons_positions))
        redo_selector.main_loop_with_voice()

        if redo_selector.selection == 0:  # 用户选择了“重做”
            # 重置当前招式的状态，准备重做
            routines[i] = Guider(camera=camera,uuid = unique_id, paths=sport_type_config["路径"][f"POSTURE_{i + 1}"], debug=DEBUG)
            continue  # 再次执行当前循环，即重做当前招式
        elif redo_selector.selection == 1:  # 用户选择了“继续”
            i += 1  # 进入下一个招式
        # ******** 添加重做/继续逻辑的结束 ********

    # # 把 differences-<id>.json 文件合并生成
    # combine_simple(id=unique_id, save_path=Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi")

    # 结束：发送动作分列表至前端
    DataSender.send_control(command="MOVE_SCORES", data=[t.score for t in routines])

    # 退出 pygame
    pygame.quit()


if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    unique_id = args.unique_id
    rtmp_url = args.rtmp_url
    video_source = rtmp_url if rtmp_url else 0
    camera = CameraUtil(source=video_source, resolution=(1280, 720))  # WIN_SIZE=(1280, 720) 默认分辨率

    DEBUG = 0
    # todo:: winsize问题，按钮会超框，因为根据的是未分割的窗口尺寸
    sport_selector = Selector(camera=camera,uuid = unique_id, buttons_config=SPORTS_SEL, debug=0,
                              win_size=(WIN_SIZE[0], WIN_SIZE[1]))  # debug=0 使用udp相机
    mode_selector = Selector(camera=camera,uuid = unique_id, buttons_config=MODES_SEL, debug=0,
                             win_size=(WIN_SIZE[0], WIN_SIZE[1]))  # debug=0 使用udp相机
    anim = Animator(camera=camera)
    pre_align = PreAlignerPoints(camera=camera,uuid = unique_id, _paths=PRE_GAME_ALIGN_PATHS, debug=DEBUG)
    pre_clip = Guider(camera=camera,uuid = unique_id, paths=PRE_GAME_CLIP_PATHS, debug=DEBUG)

    # 倒计时3s
    anim.animate_countdown(duration=1.0, config=ANIMATOR_CONFIG, cnt=3)

    # 选择运动项目
    sport_selector.main_loop_with_voice()  # -> sport_selector.selection

    # 倒计时3s
    anim.animate_countdown(duration=1.0, config=ANIMATOR_CONFIG, cnt=3)

    # todo:: 发送控制帧，告诉前端要播放哪个视频

    # 选择模式
    mode_selector.main_loop_with_voice()  # -> mode_selector.selection

    # 根据选择的模式
    if mode_selector.selection == 0:
        # 学习模式
        # 根据选择的运动项目 创建对应的（路径） Guider 实例
        if sport_selector.selection == 0:
            DataSender.send_control("PLAY_VIDEO", flag ="part1.mp4")
            time.sleep(8)
            # 太极操 9 式
            run_sport_routine(sport_type_config=TJC_Learning_CONFIG, anim=anim, camera=camera, pre_align=pre_align,
                              pre_clip=pre_clip, DEBUG=DEBUG, unique_id=unique_id)

        elif sport_selector.selection == 1:
            DataSender.send_control("PLAY_VIDEO", flag="part1.mp4")
            time.sleep(8)
            # 八法五步
            run_sport_routine(sport_type_config=TJC_Learning_CONFIG, anim=anim, camera=camera, pre_align=pre_align,
                              pre_clip=pre_clip, DEBUG=DEBUG, unique_id=unique_id)

        elif sport_selector.selection == 2:
            DataSender.send_control("PLAY_VIDEO", flag="part1.mp4")
            time.sleep(8)
            # 24式太极拳
            run_sport_routine(sport_type_config=TJC_Learning_CONFIG, anim=anim, camera=camera, pre_align=pre_align,
                              pre_clip=pre_clip, DEBUG=DEBUG, unique_id=unique_id)
    elif mode_selector.selection == 1:
        # 训练模式
        # 选择的运动项目
        if sport_selector.selection == 0:
            DataSender.send_control("PLAY_VIDEO", flag ="part1.mp4")
            time.sleep(8)
            # 太极操 9 式
            run_sport_routine(sport_type_config=TJC_Training_CONFIG, anim=anim, camera=camera, pre_align=pre_align,
                              pre_clip=pre_clip, DEBUG=DEBUG, unique_id=unique_id)
        elif sport_selector.selection == 1:
            DataSender.send_control("PLAY_VIDEO", flag ="part1.mp4")
            time.sleep(8)
            # 八法五步
            run_sport_routine(sport_type_config=TJC_Training_CONFIG, anim=anim, camera=camera, pre_align=pre_align,
                              pre_clip=pre_clip, DEBUG=DEBUG, unique_id=unique_id)

        elif sport_selector.selection == 2:
            DataSender.send_control("PLAY_VIDEO", flag ="part1.mp4")
            time.sleep(8)
            # 24式太极拳
            run_sport_routine(sport_type_config=TJC_Training_CONFIG, anim=anim, camera=camera, pre_align=pre_align,
                              pre_clip=pre_clip, DEBUG=DEBUG, unique_id=unique_id)