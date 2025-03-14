# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/3/14 17:51
# @Content : 
import cv2
import numpy as np
import os
import sys

from tqdm import tqdm
import json
from j2pc import Json2PreviewClass as j2pc
import Json2Images as j2i
import Video2Json as v2j
from cvzone.PoseModule import PoseDetector
import CenterCoordProcess as ccp
import JsonDiffSampler as jdif
from config.common_data import POSE_CONNECTIONS, COLOR, WIN_SIZE

std_video_fps = 30  # 标准视频帧率
std_video = "./static/part2.mp4"
std_frames_save_dir = "./display/std_frames"    # 完整流帧保存路径
sampled_frames_save_dir = "savedjsons/sampled_standard_frames"  # 抽样后帧保存路径

std_json_dir = 'savedjsons/2222.json' # 完整流JSON文件路径
sampled_json_dir = 'savedjsons/sampled_standard_frames.json'  # 抽样后的JSON文件路径

win_width, win_height = WIN_SIZE  # 1920, 1080
std_sket_center_pos = (win_width // 2, win_height - 100)  # （以骨架中心点为基）希望骨架处在的坐标
std_sket_scale = 1.0  # 缩放比例



def main():
    threshold = 1200  # 采样阈值

    # 生成完整流 JSON
    v2j.get_std_json(std_video, std_json_dir, std_frames_save_dir, std_sket_center_pos, std_sket_scale, display_sket=True, save_frames=True, win_size=WIN_SIZE)

    # 采样明显变化帧到 JSON 文件
    jdif.get_sampled_json(std_json_dir, sampled_json_dir, threshold=threshold)

    # 清空 sampled_frames_save_dir
    if os.path.exists(sampled_frames_save_dir):
        for file in os.listdir(sampled_frames_save_dir):
            file_path = os.path.join(sampled_frames_save_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    # 从采样帧 JSON 文件生成图片
    j2i.get_img_from_json(sampled_json_dir, sampled_frames_save_dir, fps=10000/threshold, scale=std_sket_scale, at_position=False, color_point=0, color_line=0, radius=13, thickness=24, display_sket=True, canvas_size=WIN_SIZE)


if __name__ == '__main__':
    main()

# @A last new line here:
