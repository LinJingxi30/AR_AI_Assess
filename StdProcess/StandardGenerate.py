# -*- coding: utf-8 -*-            
# @Author :
# @Time : 2025/3/14 17:51
# @Content : 
import sys
from pathlib import Path
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent  # 仓库根目录
sys.path.append(str(MEDIA_PIPE_ROOT))  # 将仓库根目录添加到系统路径中，以便导入其他模块

from ProcessKit import Video2Json as v2j, Json2Images as j2i, JsonDiffSampler as jdif, Images2Masks as i2m
from Config.common_data import WIN_SIZE
import shutil
from pathlib import Path
from config import *

std_video_fps = 30  # 标准视频帧率

# 标准原视频路径
std_video = PATHS["std_video"]  # 标准原视频路径

# 帧路径
std_frames_save_dir = PATHS["std_frames_save_dir"]  # 完整流帧保存路径
sampled_frames_save_dir = PATHS["sampled_frames_save_dir"]  # 抽样后帧保存路径
std_masked_frames_save_dir = PATHS["std_masked_frames_save_dir"]  # 抽样后、遮罩后帧保存路径

# JSON路径
std_json_dir = PATHS["std_json_dir"]  # 完整流JSON文件路径
sampled_json_dir = PATHS["sampled_json_dir"]  # 抽样后的JSON文件路径

# 参数
win_width, win_height = WIN_SIZE  # 在config/common_data.py中定义的标准窗口大小
std_sket_center_pos = THRESHOLD["std_sket_center_pos"]  # （以骨架中心点为基）希望骨架处在的坐标
std_sket_scale = THRESHOLD["std_sket_scale"]  # 缩放比例


def StandardGenerate(sampleThreshold=THRESHOLD["sample"], overlayThreshold=THRESHOLD["overlay"]):
    # 采样阈值threshold
    # 生成完整流 JSON
    # save_frames=True 配合 line45 中 direct_copy_from_std_frame_dir使用。都会先清空保存目录，再保存图片。
    v2j.get_std_json_images(std_video, 
                            std_json_dir, std_frames_save_dir, 
                            std_sket_center_pos, 
                            std_sket_scale, 
                            display_sket=False, 
                            draw_config=BLACK_SKET_CONFIG, 
                            save_frames=True, 
                            win_size=WIN_SIZE)

    # 采样明显变化帧到 JSON 文件
    jdif.get_sampled_json(std_json_dir, 
                          sampled_json_dir, 
                          threshold=sampleThreshold)

    # 从采样帧 JSON 文件生成图片/转存图片
    # direct_copy_from_std_frame_dir 启用转存
    j2i.get_img_from_json(sampled_json_dir, 
                          sampled_frames_save_dir, 
                          direct_copy_from_std_frame_dir=std_frames_save_dir, 
                          fps=10000 / sampleThreshold, 
                          scale=std_sket_scale, 
                          at_position=False, 
                          color_point=False, 
                          color_line=False, 
                          radius=13, 
                          thickness=24, 
                          display_sket=True, 
                          canvas_size=WIN_SIZE)

    # 根据采样帧存下的图片，生成遮罩后的图片
    i2m.get_folder_masked_imgs(sampled_frames_save_dir, 
                               std_masked_frames_save_dir, 
                               display_masked_img=False, 
                               overlayThreshold=overlayThreshold, 
                               bg_opacity=THRESHOLD["bg_opacity"], 
                               color_glow=THRESHOLD["color_glow"], 
                               thickness=THRESHOLD["glow_thickness"])

    # 把采样帧 JSON 文件拷贝到遮罩后的文件夹
    dest_json_path = Path(std_masked_frames_save_dir) / Path(sampled_json_dir).name
    shutil.copy(sampled_json_dir, dest_json_path)
    print(f"已保存采样帧 JSON 文件到 {dest_json_path}！")

if __name__ == '__main__':
    StandardGenerate(sampleThreshold=THRESHOLD["sample"], overlayThreshold=THRESHOLD["overlay"])  # 采样阈值和遮罩阈值

# @A last new line here:
