# -*- coding: utf-8 -*-            
# @Author :
# @Time : 2025/3/6 20:07
# @Content :

import json
import cv2
import numpy as np

# json_dir = 'SavedJsons/Squat.json'
json_dir = 'SavedJsons/relatetest.json'

def draw_pose(frame, scale, center_pos, color_point, color_line, radius, thickness, x_prog, y_prog):
    """
    :param frame: 要绘制的帧
    :param scale: 缩放倍率
    :param center_pos: 中心位置
    :param color_point:
    :param color_line:
    :param radius:
    :param thickness:
    :param x_prog:
    :param y_prog:
    :return:
    """
    if frame['poses']:
        pose = frame['poses']#[0]  # 取第一个姿势
        x_offset, y_offset = center_pos
        x_offset += x_prog
        y_offset += y_prog
        for i in range(0, len(pose), 3):
            x, y = int(pose[i] * scale + x_offset), int(pose[i + 1] * scale + y_offset)  # 坐标缩放
            cv2.circle(canvas, (x, y), radius, color_point, -1)

        for (i, j) in connections:
            if i * 3 + 2 < len(pose) and j * 3 + 2 < len(pose):
                pt1 = (int(pose[i * 3] * scale + x_offset), int(pose[i * 3 + 1] * scale + y_offset))
                pt2 = (int(pose[j * 3] * scale + x_offset), int(pose[j * 3 + 1] * scale + y_offset))
                cv2.line(canvas, pt1, pt2, color_line, thickness)

# def draw_pose(frame, scale, start_pos, color_point, color_line, radius, thickness, end_pos):

# 1. 解析JSON数据
frames = []
with open(json_dir, 'r') as f:
    for line in f:
        data = json.loads(line)
        time_ms = float(data['time'].replace('ms', ''))  # 转换为毫秒
        # poses = [np.fromstring(p, sep=',') for p in data['poses'] if p]
        poses = [np.array(p) for p in data['poses'] if p]
        frames.append({'time': time_ms, 'poses': poses})

# 2. 定义关节连接关系（示例，根据实际数据结构调整）
connections = [
    (11, 12),  # 左肩 -> 右肩
    (11, 13),  # 左肩 -> 左肘
    (12, 14),  # 右肩 -> 右肘
    (13, 15),  # 左肘 -> 左手
    (14, 16),  # 右肘 -> 右手
    (11, 23),  # 左肩 -> 左髋
    (12, 24),  # 右肩 -> 右髋
    (23, 25),  # 左髋 -> 左膝
    (24, 26),  # 右髋 -> 右膝
    (23, 24),  # 左髋 -> 右髋
    (25, 27),  # 左膝 -> 左脚
    (26, 28),  # 右膝 -> 右脚
]

# 3. 窗口和预览区域参数
win_width, win_height = 1280, 720
preview_width, preview_height = 250, 200


# 4. 主循环
current_idx = 0
time_scale = 1.0  # 时间缩放因子
cv2.namedWindow('Motion Preview', cv2.WINDOW_NORMAL)

# 颜色 BGR
red = (0, 0, 255)
green = (0, 255, 0)
blue = (150, 50, 50)
babyblue = (240, 207, 137)
lightyellow = (137, 207, 240)
pink = (255, 0, 255)
yellow = (0, 255, 255)

# 我的参数
fps = 20 # frame / s
center_main_pos = (200, 200)
# starter position
center_preview_pos = (1200, 520) # (1100, 650)
center_do_it_pos = center_preview_pos # (1200, 650)
# end position
pointer_pos = ()  # 指针位置
x_prog, y_prog = 0, 0
x_prog_do_it, y_prog_do_it = 0, 0
pause_frame = {}
preview_time = 3  # 预览时间（秒）
frame_num_3s = int(preview_time * fps)  # 3秒对应的帧数
moving_distance = 125  # 未来动作的移动距离（像素）
x_step, y_step = -int(moving_distance/frame_num_3s), 0  # 速度（步长），左负右正

while current_idx < len(frames):
    current_frame = frames[current_idx]
    current_time = current_frame['time']

    # 查找未来3秒和5秒的帧
    # target_3s = current_time + 3000  # 3000ms = 3秒

    # 二分查找最近的帧
    future_3s_idx = min((current_idx + frame_num_3s), len(frames) - 1)  # 示例简化，应改为实际时间查找

    # 创建画布
    canvas = np.zeros((win_height, win_width, 3), dtype=np.uint8)

    # 绘制当前骨架（主画面）
    draw_pose(current_frame, 0.5, center_main_pos, red, pink, 5, 3, 0, 0)   # 小红

    # 采样、步进
    if current_idx % frame_num_3s == 0:
        if pause_frame:
            do_it_frame = pause_frame
            x_prog_do_it, y_prog_do_it = x_prog, y_prog
        else:
            do_it_frame = current_frame
        x_prog, y_prog = 0, 0
        pause_frame = frames[future_3s_idx]
        draw_frame = frames[future_3s_idx]
    else:
        x_prog += x_step
        y_prog += y_step
        draw_frame = pause_frame

    # 绘制滑动指针（动态位置）
    progress = (current_idx % 100) / 100.0  # 示例进度，应根据实际时间计算
    # pointer_x = int(win_width - preview_width + progress * preview_width)
    pointer_x = center_preview_pos[0] + x_prog + 60
    cv2.line(canvas,
             (pointer_x, win_height - preview_height),
             (pointer_x, win_height),
             (0, 0, 255), 2)

    # 绘制预览区域（滑动小人）
    draw_pose(draw_frame, 0.2, center_preview_pos, blue, babyblue, 3, 2, x_prog, y_prog)    # 滑动小蓝
    draw_pose(do_it_frame, 0.2, center_do_it_pos, yellow, lightyellow, 4, 3, x_prog_do_it, y_prog_do_it)    # 小黄

    # 小框
    preview_area = canvas[win_height - preview_height:win_height,
                   win_width - preview_width:win_width]
    cv2.rectangle(canvas,
                  (win_width - preview_width, win_height - preview_height),
                  (win_width, win_height),
                  (255, 255, 255), 2)


    # 显示
    cv2.imshow('Motion Preview', canvas)

    # 控制播放速度
    key = cv2.waitKey(int(1000/fps))  # fps在循环外定义
    if key == 27 or key == ord('q') or key == ord('Q'):  # ESC、q、Q退出
        break
    elif key == ord(' '):  # 空格暂停
        cv2.waitKey(0)

    current_idx += 1

cv2.destroyAllWindows()

# @A last new line here:
