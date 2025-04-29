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


def draw_overlay_centered1(canvas, overlay, center, origin_center=None, scale=1.0):
    """
    参数:
    canvas: 目标画布 (numpy数组)
    overlay: 要叠加的掩膜图像 (numpy数组)
    center: 目标画布上的中心坐标 (x,y)
    origin_center: 掩膜图像上的原点坐标 (默认图像中心)
    scale: 缩放比例
    """
    if overlay is None:
        return canvas
    
    # 获取掩膜尺寸
    oh, ow = overlay.shape[:2]
    
    # 1. 计算缩放后的掩膜尺寸
    scaled_w = int(ow * scale)
    scaled_h = int(oh * scale)
    
    # 2. 缩放掩膜图像
    scaled_overlay = cv2.resize(overlay, (scaled_w, scaled_h))
    
    # 3. 确定原点锚点（默认使用图像中心）
    if origin_center is None:
        origin_center = (scaled_w // 2, scaled_h // 2)
    else:
        # 将原始掩膜坐标映射到缩放后图像
        origin_center = (int(origin_center[0] * scale), 
                        int(origin_center[1] * scale))
        
    cv2.circle(scaled_overlay, origin_center, radius=15, color=(0, 0, 255), thickness=-1)
    
    # 4. 计算绘制位置
    x = int(center[0] - origin_center[0])
    y = int(center[1] - origin_center[1])
    
    # 5. 处理越界情况（仅绘制可见部分）
    canvas_h, canvas_w = canvas.shape[:2]
    
    # 计算源图像ROI
    src_x1 = max(0, -x)
    src_y1 = max(0, -y)
    src_x2 = min(scaled_w, canvas_w - x)
    src_y2 = min(scaled_h, canvas_h - y)
    
    # 计算目标ROI
    dst_x1 = max(0, x)
    dst_y1 = max(0, y)
    dst_x2 = min(canvas_w, x + scaled_w)
    dst_y2 = min(canvas_h, y + scaled_h)
    
    # 6. 仅当有重叠区域时进行混合
    if src_x2 > src_x1 and src_y2 > src_y1:
        # 处理alpha通道（如果有）
        if scaled_overlay.shape[2] == 4:
            alpha = scaled_overlay[src_y1:src_y2, src_x1:src_x2, 3] / 255.0
            for c in range(3):
                canvas[dst_y1:dst_y2, dst_x1:dst_x2, c] = \
                    (1 - alpha) * canvas[dst_y1:dst_y2, dst_x1:dst_x2, c] + \
                    alpha * scaled_overlay[src_y1:src_y2, src_x1:src_x2, c]
        else:
            # 无alpha通道直接覆盖
            canvas[dst_y1:dst_y2, dst_x1:dst_x2] = \
                scaled_overlay[src_y1:src_y2, src_x1:src_x2]
    
    return canvas


def draw_overlay_centered(canvas, overlay, center, origin_center=None, scale=1.0, opacity=0.5):
    if overlay is None:
        return canvas
    
    # 获取掩膜尺寸
    oh, ow = overlay.shape[:2]
    s_ow, s_oh = int(ow * scale), int(oh * scale)

    if origin_center is None:
        origin_center = (s_ow // 2, s_oh // 2)
    else:
        # 将原始掩膜坐标映射到缩放后图像
        origin_center = (int(origin_center[0] * scale), 
                        int(origin_center[1] * scale))
    
    s_overlay = cv2.resize(overlay, (s_ow, s_oh))

    # 在scaled_overlay上标记原点，但避免修改alpha通道
    if s_overlay.shape[2] == 4:
        bgr_part = s_overlay[:, :, :3].copy()

        cv2.circle(bgr_part, origin_center, radius=15, color=(0, 0, 255), thickness=-1)
        s_overlay = np.dstack([bgr_part, s_overlay[:, :, 3]])
    else:
        cv2.circle(s_overlay, origin_center, radius=15, color=(0, 0, 255), thickness=-1)
    

    x = int(center[0] - origin_center[0])
    y = int(center[1] - origin_center[1])

    # canvas 上的四个角
    canvas_h, canvas_w = canvas.shape[:2]
    c_topleft = (max(0, x), max(0, y))  # 左上角，不小于0
    c_topright = (min(canvas_w, x + s_ow), max(0, y))   # 右上角，x不大于canvas宽度, y不小于0
    c_bottomleft = (max(0, x), min(canvas_h, y + s_oh))  # 左下角，x不小于0, y不大于canvas高度
    c_bottomright = (min(canvas_w, x + s_ow), min(canvas_h, y + s_oh))  # 右下角，x不大于canvas宽度, y不大于canvas高度

    # overlay 上的四个角
    o_topleft = (max(0, -x), max(0, -y))  # 左上角，不小于0
    o_topright = (min(s_ow, canvas_w - x), max(0, -y))  # 右上角，x不大于canvas宽度, y不小于0
    o_bottomleft = (max(0, -x), min(s_oh, canvas_h - y))  # 左下角，x不小于0, y不大于canvas高度
    o_bottomright = (min(s_ow, canvas_w - x), min(s_oh, canvas_h - y))  # 右下角，x不大于canvas宽度, y不大于canvas高度

    if o_topright[0] > o_topleft[0] and o_bottomleft[1] > o_topleft[1]:
        # 处理alpha通道（如果有）
        if s_overlay.shape[2] == 4:
            alpha = s_overlay[o_topleft[1]:o_bottomleft[1], o_topleft[0]:o_topright[0], 3] / 255.0
            for c in range(3):
                canvas[c_topleft[1]:c_bottomleft[1], c_topleft[0]:c_topright[0], c] = \
                    (1 - alpha) * canvas[c_topleft[1]:c_bottomleft[1], c_topleft[0]:c_topright[0], c] + \
                    opacity * alpha * s_overlay[o_topleft[1]:o_bottomleft[1], o_topleft[0]:o_topright[0], c]
        else:
            # 无alpha通道直接覆盖
            canvas[c_topleft[1]:c_bottomleft[1], c_topleft[0]:c_topright[0]] = \
                s_overlay[o_topleft[1]:o_bottomleft[1], o_topleft[0]:o_topright[0]]
    
    # print(center)
    int_center = (int(center[0]), int(center[1]))
    cv2.circle(canvas, int_center, radius=10, color=(0, 165, 255), thickness=-1)
            
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
