# -*- coding: utf-8 -*-            
# @Author :
# @Time : 2025/3/14 17:51
# @Content : 
import os

from jsonProcessKit import Video2Json as v2j, Json2Images as j2i, JsonDiffSampler as jdif, Images2Masks as i2m
from config.common_data import WIN_SIZE
import shutil

std_video_fps = 30  # 标准视频帧率

# 标准原视频路径
std_video = "./static/part2.mp4"

# 帧路径
std_frames_save_dir = "stdProcess/full_std_frames"    # 完整流帧保存路径
sampled_frames_save_dir = "stdProcess/sampled_std_frames"  # 抽样后帧保存路径
std_masked_frames_save_dir = "stdProcess/masked_sampled_std_frames"  # 抽样后、遮罩后帧保存路径

# JSON路径
std_json_dir = 'stdProcess/full_std_frames.json' # 完整流JSON文件路径
sampled_json_dir = 'stdProcess/sampled_std_frames.json'  # 抽样后的JSON文件路径

# 参数
win_width, win_height = WIN_SIZE  # 在config/common_data.py中定义的标准窗口大小
std_sket_center_pos = (win_width // 2, win_height - 100)  # （以骨架中心点为基）希望骨架处在的坐标
std_sket_scale = 1.0  # 缩放比例


def main():
    threshold = 1200  # 采样阈值

    # 生成完整流 JSON
    # save_frames=True 配合 line45 中 direct_copy_from_std_frame_dir使用。都会先清空保存目录，再保存图片。
    v2j.get_std_json(std_video, std_json_dir, std_frames_save_dir, std_sket_center_pos, std_sket_scale, display_sket=False, save_frames=True, win_size=WIN_SIZE)

    # 采样明显变化帧到 JSON 文件
    jdif.get_sampled_json(std_json_dir, sampled_json_dir, threshold=threshold)

    # 从采样帧 JSON 文件生成图片/转存图片
    # direct_copy_from_std_frame_dir 启用转存
    j2i.get_img_from_json(sampled_json_dir, sampled_frames_save_dir, direct_copy_from_std_frame_dir=std_frames_save_dir, fps=10000/threshold, scale=std_sket_scale, at_position=False, color_point=0, color_line=0, radius=13, thickness=24, display_sket=True, canvas_size=WIN_SIZE)

    # 根据采样帧存下的图片，生成遮罩后的图片
    i2m.get_folder_masked_imgs(sampled_frames_save_dir, std_masked_frames_save_dir, display_masked_img=False)

    # 把采样帧 JSON 文件拷贝到遮罩后的文件夹
    dest_json_path = os.path.join(std_masked_frames_save_dir, os.path.basename(sampled_json_dir))
    shutil.copy(sampled_json_dir, dest_json_path)
    print(f"已保存采样帧 JSON 文件到 {dest_json_path}！")

if __name__ == '__main__':
    main()

# @A last new line here:
