# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/4/29 21:11
# @Content : 

import cv2
import numpy as np

PTS_PAIR_COLORS = [
    (140, 50, 0),    # rgb(0, 50, 140)
    (150, 255, 0),    # rgb(20, 255, 150)
    (140, 0, 0),    # rgb(0, 0, 140)
    (50, 205, 0),    # rgb(20, 205, 0)
]

ARROW_COLORS = {
    "normal": (0, 0, 255),    # BGR红色   rgb(155, 0, 0)
    "achieve": (0, 255, 0),   # BGR绿色   rgb(0, 100, 0)
}

ARROW_NUM = 2
ARROW_SIZE = 12
ARROW_THICKNESS = 3

def draw_overlay_centered(canvas, std_overlay, center, target, win_size, scale=1.0, opacity=1.0):
    if std_overlay is None:
        return canvas
    
    # 缩放掩膜
    overlay_resized = cv2.resize(std_overlay, (0, 0), fx=scale, fy=scale)

    # 获取缩放后的掩膜尺寸
    o_h, o_w = overlay_resized.shape[:2]

    if center is None:
        center = (o_h // 2, o_w // 2)  # 默认中心点为掩膜中心
    else:
        center = (int(center[0]), int(center[1]))

    if target is None:
        target = (win_size[0] // 2, win_size[1] // 2)   # 默认目标点为窗口中心
    else:
        target = (int(target[0]), int(target[1]))

    # # 调试用：绘制 center 于掩膜（BGRA）（center）
    # if overlay_resized.shape[2] == 4:
    #     cv2.circle(overlay_resized, center, 10, (0, 165, 255, 150), -1)
    # else:
    #     cv2.circle(overlay_resized, center, 10, (0, 165, 255), -1)

    # 开始绘制掩膜
    # 计算偏移量
    offset_x = target[0] - center[0]
    offset_y = target[1] - center[1]

    # 计算掩膜左上角在画布上的位置
    x1 = offset_x
    y1 = offset_y

    # 计算掩膜在画布上的实际绘制区域
    h, w = canvas.shape[:2]
    x_start = max(x1, 0)
    y_start = max(y1, 0)
    x_end = min(x1 + o_w, w)
    y_end = min(y1 + o_h, h)

    # 计算掩膜的裁剪区域
    overlay_x_start = max(0, -x1)
    overlay_y_start = max(0, -y1)
    overlay_x_end = overlay_x_start + (x_end - x_start)
    overlay_y_end = overlay_y_start + (y_end - y_start)

    # 检查是否有可绘制区域
    if x_start >= x_end or y_start >= y_end:
        return canvas

    # 叠加掩膜（支持带 alpha 通道的 BGRA），支持 opacity
    if overlay_resized.shape[2] == 4:
        # 取出 alpha 通道并乘以 opacity
        alpha_overlay = (overlay_resized[overlay_y_start:overlay_y_end, overlay_x_start:overlay_x_end, 3] / 255.0) * opacity
        alpha_overlay = np.clip(alpha_overlay, 0, 1)
        alpha_canvas = 1.0 - alpha_overlay

        for c in range(3):  # BGR
            canvas[y_start:y_end, x_start:x_end, c] = (
                alpha_overlay * overlay_resized[overlay_y_start:overlay_y_end, overlay_x_start:overlay_x_end, c] +
                alpha_canvas * canvas[y_start:y_end, x_start:x_end, c]
            ).astype(np.uint8)
    else:
        # 没有 alpha 通道，直接覆盖
        canvas[y_start:y_end, x_start:x_end] = overlay_resized[overlay_y_start:overlay_y_end, overlay_x_start:overlay_x_end]

    # 调试用：绘制画布中心点（target）
    # cv2.circle(canvas, target, 10, (0, 50, 0), -1)

    return canvas

def draw_points_and_arrows(canvas, std_landmarks_list, rt_landmarks_list, condition, colors=PTS_PAIR_COLORS):
    # todo:: 这里的组合中 rt_landmarks_list 可能会有空值，导致不能绘制标准点
    for idx, (std_lm_pt, rt_lm_pt) in enumerate(zip(std_landmarks_list, rt_landmarks_list)):

        # 选择点对颜色
        # color = PTS_PAIR_COLORS[idx % len(PTS_PAIR_COLORS)]
        color = colors[idx]
        

        # 绘制标准点（配对配色）
        std_lm_pt = (int(std_lm_pt[0]), int(std_lm_pt[1]))  # 将点坐标转换为整数
        draw_gradient_point(canvas, std_lm_pt, color, size=20, steps=3)
        
        # 绘制实时点（配对配色）
        if rt_lm_pt:
            rt_lm_pt = (int(rt_lm_pt[0]), int(rt_lm_pt[1]))
            draw_gradient_point(canvas, rt_lm_pt, color, size=20, steps=3)

        # 绘制箭头
        # 获取箭头颜色
        if condition[idx]:
            arrow_color = ARROW_COLORS["achieve"]
        else:
            arrow_color = ARROW_COLORS["normal"]

        # 绘制箭头
        draw_arrows_line(canvas, 
                   start=rt_lm_pt, end=std_lm_pt, 
                   arrow_num=ARROW_NUM,
                   color=arrow_color, size=ARROW_SIZE, thickness=ARROW_THICKNESS)

    return canvas

def draw_gradient_point(canvas, point, color, size=20, steps=5):
    """绘制渐变点"""
    # print("画")
    overlay = canvas.copy()
    for i in range(steps):
        radius = int(size * (i + 1) / steps)
        alpha = 1.0 - (i / steps)
        cv2.circle(overlay, point, radius, color, -1)
        cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)
    # return canvas

def draw_arrows_line(canvas, start, end, arrow_num, color, size=20, thickness=4):
    """从起点到终点绘制多个箭头"""
    if start == end:
        return

    # 计算箭头间隔
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = np.hypot(dx, dy)
    if length == 0:
        return

    for i in range(1, arrow_num + 1):
        # 计算箭头位置占比
        t = i / (arrow_num + 1)

        # 计算箭头尖端坐标
        current_arrow_tip = (int(start[0] + dx * t), int(start[1] + dy * t))

        # 绘制箭头
        draw_arrow(canvas, start, current_arrow_tip, color, thickness, size)
        # cv2.arrowedLine(
        #     canvas,
        #     start,
        #     arrow_tip,
        #     color,
        #     thickness=thickness,
        #     tipLength=0.3
        # )

def draw_arrow(canvas, start, end, color, thickness, size):
    """绘制对号形状的动态箭头"""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = np.hypot(dx, dy)
    if length == 0:
        return
    dx, dy = dx / length, dy / length
    checkmark_point1 = (int(end[0] - size * (dx + dy)),
                        int(end[1] - size * (dy - dx)))
    checkmark_point2 = (int(end[0] - size * (dx - dy)),
                        int(end[1] - size * (dy + dx)))
    cv2.line(canvas, checkmark_point1, end, color, thickness)
    cv2.line(canvas, checkmark_point2, end, color, thickness)
    
# @A last new line here:
