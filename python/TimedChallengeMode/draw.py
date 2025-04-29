# -*- coding: utf-8 -*-            
# @Author :
# @Time : 2025/3/19 12:04
# @Content : 

"""
draw_gradient_point: 绘制渐变点效果
draw_arrows_on_path: 在路径上绘制多个动态箭头
    └── draw_checkmark_arrow: 绘制对号形状的动态箭头
"""

import cv2
import numpy as np
from TimedChallengeMode.config import *
from Config.common_data import COLOR, WIN_SIZE


def draw_realtime_cap_only(canvas, cap_frame, use_flip=False):
    """绘制实时摄像头画面"""
    if cap_frame is not None:
        # 将摄像头画面缩放到窗口大小
        canvas = cv2.resize(cap_frame, (canvas.shape[1], canvas.shape[0]))
        return canvas   
    else:
        print("错误：摄像头画面为空！")


def draw_overlay_centered(canvas, overlay, center, scale=1.0):
    """
    将overlay遮罩图片以center为中心点，按scale缩放后叠加到canvas上。
    overlay可以有alpha通道，canvas为BGR三通道。
    只保留在canvas范围内的部分，超出部分自动裁剪。
    """
    if overlay is None or center is None:
        print("错误：遮罩或中心点为空！", file=sys.stderr)
        return

    # 1. 缩放overlay
    # h, w = overlay.shape[:2]
    w, h = overlay.shape[:2]
    print(w, h) # 测试
    new_w, new_h = int(w * scale), int(h * scale)
    overlay_resized = cv2.resize(overlay, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # 2. 计算放置位置
    cx, cy = int(center[0]), int(center[1])
    top_left_x = cx - new_w // 2
    top_left_y = cy - new_h // 2

    # 3. 计算有效区域（防止越界）
    canvas_h, canvas_w = canvas.shape[:2]
    x1 = max(top_left_x, 0)
    y1 = max(top_left_y, 0)
    x2 = min(top_left_x + new_w, canvas_w)
    y2 = min(top_left_y + new_h, canvas_h)

    # 对应overlay区域
    overlay_x1 = x1 - top_left_x
    overlay_y1 = y1 - top_left_y
    overlay_x2 = overlay_x1 + (x2 - x1)
    overlay_y2 = overlay_y1 + (y2 - y1)

    # 检查区域是否有效
    if x2 <= x1 or y2 <= y1 or overlay_x2 <= overlay_x1 or overlay_y2 <= overlay_y1:
        # 区域无效，直接返回
        return canvas

    # 4. 叠加
    if overlay_resized.shape[2] == 4:
        # 有alpha通道
        alpha = overlay_resized[overlay_y1:overlay_y2, overlay_x1:overlay_x2, 3:4] / 255.0
        overlay_rgb = overlay_resized[overlay_y1:overlay_y2, overlay_x1:overlay_x2, :3].astype(np.float32)
        canvas_roi = canvas[y1:y2, x1:x2].astype(np.float32)
        blended = overlay_rgb * alpha + canvas_roi * (1 - alpha)
        # canvas[y1:y2, x1:x2] = blended.astype(canvas.dtype)
        a = 0.5
        canvas[y1:y2, x1:x2] = (blended * a + canvas[y1:y2, x1:x2] * (1 - a)).astype(canvas.dtype)
    else:
        # 无alpha通道，直接覆盖
        canvas[y1:y2, x1:x2] = overlay_resized[overlay_y1:overlay_y2, overlay_x1:overlay_x2, :3]

    return canvas


def draw_overlay_on_canvas(canvas, overlay):
    """将遮罩叠加到画布上"""
    if overlay is not None:
        # 确保遮罩和画布大小一致
        overlay_resized = cv2.resize(overlay, (canvas.shape[1], canvas.shape[0]))
        # 将遮罩应用到画布上
        # if overlay_resized.shape[2] == 4:
        #     # 将 alpha 通道扩展为 (h, w, 1) 以便广播
        #     alpha = overlay_resized[..., 3:4] / 255.0
        #     # 混合操作：注意确保数据类型一致（一般为 float 或 uint8）
        #     canvas = (overlay_resized[..., :3] * alpha + canvas * (1 - alpha)).astype(canvas.dtype)
        #     return canvas
        # 如果有 alpha 通道
        if overlay_resized.shape[2] == 4:
            # 将数据转换为 float32 计算
            canvas_float = canvas.astype(np.float32)
            overlay_float = overlay_resized.astype(np.float32)
            # 提取 alpha 通道并扩展到三通道进行广播
            alpha = overlay_float[..., 3:4] / 255.0

            # 计算融合结果，注意保证数据在 [0,255]范围内
            blended = overlay_float[..., :3] * alpha + canvas_float * (1 - alpha)
            # 还原数据类型
            canvas[:] = blended.astype(canvas.dtype)
    else:
        print("错误：遮罩为空！")

def draw_points_with_arrow(canvas, std_points, real_points, condition_dict):
    """绘制标准点和实时点，每对点使用相同颜色"""
    if not std_points or not real_points:
        return canvas

    # 定义每对点的颜色（示例使用红、绿、蓝、黄）
    PAIR_COLORS = [
        # (255, 0, 0),    # 红色
        (255, 0, 0),
        (0, 255, 0),    # 绿色
        (255, 0, 0),    # 蓝色
        (0, 255, 0),  # 绿色

        # (255, 255, 0)   # 黄色
    ]

    for idx, ((std, real), name) in enumerate(zip(zip(std_points, real_points), POSE_LANDMARKS.keys())):
        std_pos = (int(std[0]), int(std[1]))
        real_pos = (int(real[0]), int(real[1]))

        # 根据配对索引选择颜色
        pair_color = PAIR_COLORS[idx % len(PAIR_COLORS)]  # 循环使用颜色列表

        # 绘制标准点（使用配对颜色）
        draw_gradient_point(canvas, std_pos, pair_color,
                            20,
                            VISUAL_CONFIG["gradient"]["steps"])
        
        # 绘制实时点（使用相同的配对颜色）
        draw_gradient_point(canvas, real_pos, pair_color,
                            VISUAL_CONFIG["gradient"]["max_radius"] // 2,
                            VISUAL_CONFIG["gradient"]["steps"] // 2)

        # 箭头颜色保持原有逻辑
        if condition_dict.get(name, False):
            arrow_color = VISUAL_CONFIG["arrow"]["achieve_color"]
        else:
            arrow_color = VISUAL_CONFIG["arrow"]["normal_color"]
        draw_arrows_on_path(canvas, real_pos, std_pos, arrow_color)

    return canvas


def draw_points_to_reach(canvas, std_points, real_points, threshold=50):
    """优化后的指导点绘制函数"""
    if not std_points or not real_points:
        return False

    all_points_matched = True
    for (std, real), name in zip(zip(std_points, real_points), POSE_LANDMARKS.keys()):
        std_pos = (int(std[0]), int(std[1]))
        real_pos = (int(real[0]), int(real[1]))

        # 绘制渐变点
        draw_gradient_point(canvas, std_pos, VISUAL_CONFIG["gradient"]["std_color"],
                                 VISUAL_CONFIG["gradient"]["max_radius"],
                                 VISUAL_CONFIG["gradient"]["steps"])
        draw_gradient_point(canvas, real_pos, VISUAL_CONFIG["gradient"]["real_color"],
                                 VISUAL_CONFIG["gradient"]["max_radius"] // 2,
                                 VISUAL_CONFIG["gradient"]["steps"] // 2)

        # 计算距离并绘制动态路径
        distance = np.linalg.norm(np.array(std) - np.array(real))
        if distance > threshold:
            all_points_matched = False
            arrow_color = COLOR["red"]
        else:
            arrow_color = COLOR["green"]

        # 绘制动态箭头路径
        draw_arrows_on_path(canvas, real_pos, std_pos, arrow_color)

    # 如果所有点都匹配，显示完成提示
    if all_points_matched:
        cv2.putText(canvas, "All points matched!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    return all_points_matched


def draw_checkmark_arrow(canvas, start_point, end_point, color, thickness, arrow_size):
    """绘制对号形状的动态箭头"""
    dx, dy = end_point[0] - start_point[0], end_point[1] - start_point[1]
    length = np.hypot(dx, dy)
    if length == 0:
        return
    dx, dy = dx / length, dy / length
    checkmark_point1 = (int(end_point[0] - arrow_size * (dx + dy)),
                        int(end_point[1] - arrow_size * (dy - dx)))
    checkmark_point2 = (int(end_point[0] - arrow_size * (dx - dy)),
                        int(end_point[1] - arrow_size * (dy + dx)))
    cv2.line(canvas, checkmark_point1, end_point, color, thickness)
    cv2.line(canvas, checkmark_point2, end_point, color, thickness)


def draw_gradient_point(canvas, center, color, max_radius=30, steps=5):
    """绘制渐变点效果"""
    overlay = canvas.copy()
    for i in range(steps):
        radius = int(max_radius * (i + 1) / steps)
        alpha = 1.0 - (i / steps)
        cv2.circle(overlay, center, radius, color, -1)
        cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)


def draw_arrows_on_path(canvas, start, end, color):
    """在路径上绘制多个动态箭头"""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = np.hypot(dx, dy)
    if length == 0:
        return

    config = VISUAL_CONFIG["arrow"]
    for i in range(1, config["num_arrows"] + 1):
        t = i / (config["num_arrows"] + 1)
        current = (
            int(start[0] + t * dx),
            int(start[1] + t * dy)
        )
        draw_checkmark_arrow(canvas, start, current, color,
                             config["thickness"], config["checkmark_size"])
