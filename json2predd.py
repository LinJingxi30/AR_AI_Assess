# -*- coding: utf-8 -*-
# @Author : LJX
# @Time : 2025/3/6 20:07
# @Content :

import json
import cv2
import numpy as np

# 1. 解析JSON数据
frames = []
with open('SavedJsons/MotionData.json', 'r') as f:
    for line in f:
        data = json.loads(line)
        time_ms = float(data['time'].replace('ms', ''))  # 转换为毫秒
        poses = [np.fromstring(p, sep=',') for p in data['poses'] if p]
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
    (25, 27),  # 左膝 -> 左脚
    (26, 28),  # 右膝 -> 右脚
]

# 3. 窗口和预览区域参数
win_width, win_height = 1280, 720
preview_width, preview_height = 300, 200
pointer_pos = (win_width - 50, win_height - 50)  # 指针位置

# 4. 主循环
current_idx = 0
time_scale = 1.0  # 时间缩放因子
cv2.namedWindow('Motion Preview', cv2.WINDOW_NORMAL)

while current_idx < len(frames):
    current_frame = frames[current_idx]
    current_time = current_frame['time']

    # 查找未来3秒和5秒的帧
    target_3s = current_time + 3000  # 3000ms = 3秒  # 大概差距25帧
    target_5s = current_time + 5000


    # 二分查找最近的帧
    future_3s_idx = min(current_idx + 25, len(frames) - 1)  # 示例简化，应改为实际时间查找
    future_5s_idx = min(current_idx + 50, len(frames) - 1)
    future_3s_frame = frames[future_3s_idx]

    # 创建画布
    canvas = np.zeros((win_height, win_width, 3), dtype=np.uint8)

    # 绘制当前骨架（主画面）
    if current_frame['poses']:
        pose = current_frame['poses'][0]  # 取第一个姿势
        for i in range(0, len(pose), 3):
            x, y = int(pose[i] * 0.5 + 500), int(pose[i + 1] * 0.5 + 400)  # 坐标缩放
            # 绘制关键点
            cv2.circle(canvas, (x, y), 3, (0, 255, 0), -1)
        for (i, j) in connections:
            if i * 3 + 2 < len(pose) and j * 3 + 2 < len(pose):
                pt1 = (int(pose[i * 3] * 0.5 + 500), int(pose[i * 3 + 1] * 0.5 + 400))
                pt2 = (int(pose[j * 3] * 0.5 + 500), int(pose[j * 3 + 1] * 0.5 + 400))
                # 绘制骨架线
                cv2.line(canvas, pt1, pt2, (0, 100, 100), 5)

    # 绘制未来3rd(s)骨架（小框）
    scale = 0.2
    x_offset, y_offset = 700, 600
    fps_3s = 25
    step = 3
    pointer_x = x_offset
    if current_idx % fps_3s == 0:

        draw_3s = future_3s_frame
        # 截取一次
        pause_frame = future_3s_frame
        do_it_frame = pause_frame
        x_moving = 0
    else:
        draw_3s = pause_frame
        x_moving += step


    if draw_3s['poses']:
        pose = draw_3s['poses'][0]  # 取第一个姿势
        for i in range(0, len(pose), 3):
            x, y = int(pose[i] * scale + x_offset - x_moving), int(pose[i + 1] * scale + y_offset)  # 坐标缩放
            # 绘制关键点
            cv2.circle(canvas, (x, y), 3, (0, 255, 0), -1)
        for (i, j) in connections:
            if i * 3 + 2 < len(pose) and j * 3 + 2 < len(pose):
                pt1 = (int(pose[i * 3] * scale + x_offset - x_moving), int(pose[i * 3 + 1] * scale + y_offset))
                pt2 = (int(pose[j * 3] * scale + x_offset - x_moving), int(pose[j * 3 + 1] * scale + y_offset))
                # 绘制骨架线
                cv2.line(canvas, pt1, pt2, (0, 100, 100), 5)



    # 绘制预览区域
    preview_area = canvas[win_height - preview_height:win_height,
                   win_width - preview_width:win_width]
    cv2.rectangle(canvas,
                  (win_width - preview_width, win_height - preview_height),
                  (win_width, win_height),
                  (255, 255, 255), 2)

    # 绘制滑动指针（动态位置）
    # progress = (current_idx % 100) / 100.0  # 示例进度，应根据实际时间计算
    # pointer_x = int(win_width - preview_width + progress * preview_width)
    # cv2.line(canvas,
    #          (pointer_x, win_height - preview_height),
    #          (pointer_x, win_height),
    #          (0, 0, 255), 2)

    # 显示
    cv2.imshow('Motion Preview', canvas)

    # 控制播放速度
    key = cv2.waitKey(120) # 120ms/帧
    if key == 27:  # ESC退出
        break
    elif key == ord(' '):  # 空格暂停
        cv2.waitKey(0)

    current_idx += 1

cv2.destroyAllWindows()

# @A last new line here:
