import json
import math
from j2pc import Json2PreviewClass as j2pc
import cv2
import numpy as np
from config.common_data import POSE_CONNECTIONS
import os


# 计算两个姿态之间的差异（欧氏距离）
def calculate_pose_difference(pose1, pose2):
    difference = 0
    for i in range(0, len(pose1), 3):  # 每3个值表示一个点的 (x, y, z)
        x1, y1, z1 = pose1[i], pose1[i + 1], pose1[i + 2]
        x2, y2, z2 = pose2[i], pose2[i + 1], pose2[i + 2]
        difference += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
    return difference


def get_sampled_json(json_input_dir, json_save_dir, threshold):
    print("开始采样明显变化帧到 JSON 文件")    
    
    # 逐行读取 JSON 数据
    with open(json_input_dir, 'r') as f:
        lines = f.readlines()

    # 初始化变量
    prev_pose = None
    save_data = []

    # 逐行处理 JSON 数据
    for line in lines:
        data = json.loads(line.strip())
        current_pose = data["poses"]

        # 如果是第一行，直接保存
        if prev_pose is None:
            save_data.append(data)
        else:
            # 计算当前姿态与前一姿态的差异
            difference = calculate_pose_difference(prev_pose, current_pose)

            # 如果差异超过阈值，保存当前帧
            if difference > threshold:
                save_data.append(data)

        # 更新前一姿态
        prev_pose = current_pose

    # 将明显变化的帧保存到新的 JSON 文件
    with open(json_save_dir, 'w') as f_save:
        for data in save_data:
            f_save.write(json.dumps(data) + "\n")

    print(f"已保存明显变化的帧到 JSON 文件 {json_save_dir}！")


def get_sampled_json_with_img(json_input_dir, json_save_dir, threshold, img_output_dir):
    print("开始采样明显变化帧到 JSON 文件和对应图片")    
    
    # 逐行读取 JSON 数据
    with open(json_input_dir, 'r') as f:
        lines = f.readlines()

    # 初始化变量
    prev_pose = None
    save_data = []
    
    # 导入绘制所需的模块和参数

    # 设置画布和绘制参数
    canvas_width, canvas_height = 1920, 1080  # 固定画布大小
    scale = 1.0  # 缩放比例
    center_pos = (canvas_width // 2, canvas_height // 2)  # 画布中心
    color_point = (203, 192, 255)  # 关键点颜色 (RGB)
    color_line = (150, 100, 150)   # 连接线颜色 (RGB)
    radius = 13  # 关键点半径
    thickness = 24  # 连接线厚度

    # 确保图片输出目录存在
    os.makedirs(img_output_dir, exist_ok=True)
    
    # 逐行处理 JSON 数据并绘制火柴人
    frame_index = 0
    for line in lines:
        data = json.loads(line.strip())
        current_pose = data["poses"]

        # 如果是第一帧，直接保存
        if prev_pose is None:
            save_data.append(data)
            
            # 初始化画布
            canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255
            # 绘制火柴人姿态
            j2pc.better_draw_pos_scale(canvas, data, scale, center_pos, color_point, color_line, radius, thickness, POSE_CONNECTIONS)
            # 保存图片
            img_path = os.path.join(img_output_dir, f"frame_{frame_index:04d}.png")
            cv2.imwrite(img_path, canvas)
            print(f"Saved image: {img_path}")
            frame_index += 1
        else:
            # 计算当前姿态与前一姿态的差异
            difference = calculate_pose_difference(prev_pose, current_pose)
            if difference > threshold:
                save_data.append(data)
                
                # 初始化画布
                canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255
                # 绘制火柴人姿态
                j2pc.better_draw_pos_scale(canvas, data, scale, center_pos, color_point, color_line, radius, thickness, POSE_CONNECTIONS)
                # 保存图片
                img_path = os.path.join(img_output_dir, f"frame_{frame_index:04d}.png")
                cv2.imwrite(img_path, canvas)
                print(f"Saved image: {img_path}")
                frame_index += 1

        # 更新前一姿态
        prev_pose = current_pose

    # 将采样数据写入 JSON 文件
    with open(json_save_dir, 'w') as f_save:
        for data in save_data:
            f_save.write(json.dumps(data) + "\n")
    
    print(f"已保存明显变化的帧到 JSON 文件 {json_save_dir}！")


if __name__ == "__main__":
    pass
