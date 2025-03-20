# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/3/15 02:06
# @Content :


import cv2
import numpy as np
import os
import sys

from tqdm import tqdm
import json
from ProcessKit import Json2PreviewClass as j2pc, CenterCoordProcess as ccp
from cvzone.PoseModule import PoseDetector
from Config.common_data import POSE_CONNECTIONS, COLOR, WIN_SIZE, clear_directory


def get_std_json(std_video, std_json_dir, std_frames_save_dir, std_sket_center_pos, std_sket_scale, display_sket=False, save_frames=False, win_size=WIN_SIZE):
    # 初始化摄像头：使用标准视频
    cap = cv2.VideoCapture(std_video)
    if not cap.isOpened():
        print("错误：标准视频初始化失败！请检查视频路径。")
        sys.exit()
    else:
        print(f"使用标准视频 {std_video} 生成完整流 JSON 文件 {std_json_dir}...")

    # 循环前先清空json文件（循环里用的是追加模式，不会直接覆盖）
    if os.path.exists(std_json_dir):  # 若文件存在
        with open(std_json_dir, "w") as f:
            pass  # 空操作触发清空

    # 若启用保存帧，循环前清空保存目录
    if save_frames:
        if not os.path.exists(std_frames_save_dir):
            os.makedirs(std_frames_save_dir)    # 若无目录则创建
        clear_directory(std_frames_save_dir)  # 清空保存目录

    # 初始化姿态检测器
    detector = PoseDetector()

    # 初始化索引
    current_idx = 0

    # 获取视频总帧数（可能有些视频无法获得准确值）
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 获取视频帧率
    std_video_fps = cap.get(cv2.CAP_PROP_FPS)

    # 主循环：逐帧处理
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break   # 读取完毕跳出

        # cvzone处理
        image = detector.findPose(image)
        sketList, bndboxInfo = detector.findPosition(image)

        # 滤波处理
        # sketList = Filter(sketList, sketList, sketList, len(sketList), Q=0.001, R=0.0015, lpf_param=0.1)

        # 先缩放
        j2pc.get_scaled_coords(sketList, scale=std_sket_scale)  # 先缩放

        # 以脚为中心点，处理坐标
        sketList = ccp.coord_relativize(sketList, use_ground=True)

        # 将整个骨架以中心为基准移动到指定位置
        sketList = ccp.move_coords_by_center_to_pos(sketList, to_position=std_sket_center_pos, use_ground=True)

        # 只打印一次
        if current_idx == 0:
            print("开始展示标准视频骨架检测...")

        # 创建白色画布
        win_width, win_height = win_size
        canvas = np.ones((win_height, win_width, 3), dtype=np.uint8) * 255

        # 绘制骨架
        if sketList:
            # frame = {"poses": np.reshape(sketList, -1)}
            j2pc.better_draw_pos_scale(canvas, pose=sketList, frame_type='list', scale=1, at_position=std_sket_center_pos,
                                        color_point=COLOR["black"], color_line=COLOR["black"], radius=32,
                                        thickness=60, connections=POSE_CONNECTIONS)
        else:
            print("未检测到骨架！")

        """可选：展示标准视频骨架检测"""
        if display_sket:
            # 显示
            cv2.imshow('Pose Estimination of Standard Video', canvas)

        """可选：保存帧"""
        if save_frames:
            output_path = os.path.join(std_frames_save_dir, f"frame_{current_idx:05d}.png")
            cv2.imwrite(output_path, canvas)
            # print(f"Saved: {output_path}")

            # 按键控制
            key = cv2.waitKey(int(1000 / std_video_fps))
            if key == 27 or key == ord('q') or key == ord('Q'):
                break
            elif key == ord(' '):
                cv2.waitKey(0)

        """写入 JSON 文件"""
        if current_idx == 0:
            print("开始写入 JSON 文件...")
            pbar = tqdm(total=total_frames, desc="处理视频帧")

        try:
            # 处理poses格式
            flat_sketList = [item for sublist in sketList for item in
                             sublist]  # 2D(33*3) [[x1,y1,z1][x2,y2,z2]...[...]] -> 1D [x1, y1, z1, x2, y2, z2, ...]

            # 获取视频相对时间（单位 ms）作为时间戳
            video_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

            # 构建 JSON 数据
            data = {
                "ID": str(current_idx),
                # !不往键值后面加ms字符串了，接收麻烦
                "time_ms": video_time_ms,
                "poses": flat_sketList
            }
            # 写入 JSON 文件
            with open(std_json_dir, "a") as f:
                f.write(json.dumps(data) + "\n")

        except json.JSONDecodeError as e:
            print(f"JSON格式错误: {e} (检查pose字符串)")

        except Exception as e:
            print(f"写入 JSON 文件失败: {e}")

        # 索引后移
        current_idx += 1
        pbar.update(1)

    pbar.close()
    cap.release()
    cv2.destroyAllWindows()
    print("标准视频骨架检测结束！完整 JSON 文件已保存至", std_json_dir, "\n")

# @A last new line here:
