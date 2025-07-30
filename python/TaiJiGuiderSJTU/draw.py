# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/4/29 21:11
# @Content : 

import cv2
import numpy as np
import time
import sys

PTS_PAIR_COLORS = [
    (255, 78, 0),  # rgb(0, 78, 255)
    (23, 210, 255),  # rgb(255, 210, 23)
    (255, 78, 0),  # rgb(0, 78, 255)
    (23, 210, 255),  # rgb(255, 210, 23)
]

ARROW_COLORS = {
    "normal": (0, 0, 255),  # BGR红色   rgb(155, 0, 0)
    "achieve": (0, 255, 0),  # BGR绿色   rgb(0, 100, 0)
}

ARROW_NUM = 4
ARROW_SIZE = 12
ARROW_THICKNESS = 6


def draw_overlay_centered(canvas, std_overlay, center, target, win_size, scale=1.0, opacity=1.0):
    if std_overlay is None:
        return canvas

    # start_time = time.time()
    # 缩放掩膜
    overlay_resized = cv2.resize(std_overlay, (0, 0), fx=scale, fy=scale)
    end_time = time.time()
    # sys.stderr.write(f"[MASK] mask resize: {end_time - start_time:.6f}s\n")

    # 获取缩放后的掩膜尺寸
    o_h, o_w = overlay_resized.shape[:2]

    if center is None:
        center = (o_h // 2, o_w // 2)  # 默认中心点为掩膜中心
    else:
        center = (int(center[0]), int(center[1]))

    if target is None:
        target = (win_size[0] // 2, win_size[1] // 2)  # 默认目标点为窗口中心
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
    # start_time = time.time()
    # 叠加掩膜（支持带 alpha 通道的 BGRA），支持 opacity
    if overlay_resized.shape[2] == 4:
        # 提取ROI区域，使用视图而非复制
        overlay_roi = overlay_resized[overlay_y_start:overlay_y_end, overlay_x_start:overlay_x_end]
        canvas_roi = canvas[y_start:y_end, x_start:x_end]
        
        # 预分配并计算alpha通道，使用更高效的类型转换
        alpha_overlay = overlay_roi[..., 3].astype(np.float16)
        alpha_overlay *= opacity / 255.0  # 合并运算减少步骤
        np.clip(alpha_overlay, 0.0, 1.0, out=alpha_overlay)  # 原地操作
        
        # 扩展维度以匹配3通道，避免创建新数组
        alpha_overlay_3d = alpha_overlay[:, :, np.newaxis]
        alpha_canvas_3d = 1.0 - alpha_overlay_3d
        
        # 分离overlay的RGB通道
        overlay_rgb = overlay_roi[..., :3].astype(np.float16)
        
        # 计算混合结果并转换回uint8，使用out参数避免临时数组
        np.multiply(alpha_overlay_3d, overlay_rgb, out=overlay_rgb)  # 原地计算 overlay部分
        temp = canvas_roi.astype(np.float16)
        np.multiply(alpha_canvas_3d, temp, out=temp)  # 原地计算 canvas部分
        np.add(overlay_rgb, temp, out=temp)  # 合并结果
        
        # 舍入并转换回uint8，直接写入原数组
        np.rint(temp, out=temp)
        canvas_roi[:] = temp.astype(np.uint8, casting='unsafe')
    else:
        # 无alpha通道时使用切片直接赋值，利用NumPy的优化赋值
        canvas[y_start:y_end, x_start:x_end] = overlay_resized[overlay_y_start:overlay_y_end,
                                              overlay_x_start:overlay_x_end]
    
    # end_time = time.time()
    # sys.stderr.write(f"[MASK] mask apply: {end_time - start_time:.6f}s\n")

    # 调试用：绘制画布中心点（target）
    # cv2.circle(canvas, target, 10, (0, 50, 0), -1)

    return canvas


def draw_points_and_arrows(canvas, std_landmarks_list, rt_landmarks_list, condition, colors=PTS_PAIR_COLORS):
    # todo:: 这里的组合中 rt_landmarks_list 可能会有空值，导致不能绘制标准点
    for idx, (std_lm_pt, rt_lm_pt) in enumerate(zip(std_landmarks_list, rt_landmarks_list)):

        # 选择点对颜色
        # color = PTS_PAIR_COLORS[idx % len(PTS_PAIR_COLORS)]
        color = colors[idx]
        # start_time = time.time()
        # 绘制标准点（配对配色）
        # print(type(std_lm_pt))
        # print(type(rt_lm_pt))
        # std_lm_pt = (int(std_lm_pt[0]), int(std_lm_pt[1]))  # 将点坐标转换为整数
        draw_transparent_circle(canvas, std_lm_pt, radius=35, color=color, opacity=0.3, thickness=2)

        # end_time = time.time()
        # sys.stderr.write(f"[Points and Arrow] std_lm_pt: {end_time - start_time:.6f}s\n")
        # start_time = time.time()
        # 绘制实时点（配对配色）
        if rt_lm_pt:
            draw_gradient_point(canvas, rt_lm_pt, color, size=30, steps=2)

        # end_time = time.time()
        # sys.stderr.write(f"[Points and Arrow] rt_lm_pt: {end_time - start_time:.6f}s\n")

        # 绘制箭头
        # 获取箭头颜色
        if condition[idx]:
            arrow_color = ARROW_COLORS["achieve"]
        else:
            arrow_color = ARROW_COLORS["normal"]

        # start_time = time.time()
        # 绘制箭头
        draw_arrows_line(canvas,
                         start=rt_lm_pt, end=std_lm_pt,
                         arrow_num=ARROW_NUM,
                         color=arrow_color, size=ARROW_SIZE, thickness=ARROW_THICKNESS)
        
        # end_time = time.time()
        # sys.stderr.write(f"[Points and Arrow] draw_arrows_line: {end_time - start_time:.6f}s\n")

    return canvas


def draw_transparent_circle(canvas, center, radius, color, opacity=0.5, thickness=2):
    # 计算圆形的边界框（局部区域）
    center = (int(center[0]), int(center[1]))
    x = center[0]
    y = center[1]
    
    # 计算局部区域坐标（确保不超出图像边界）
    x1 = max(0, x - radius)
    y1 = max(0, y - radius)
    x2 = min(canvas.shape[1], x + radius)
    y2 = min(canvas.shape[0], y + radius)

    # 检查区域有效性
    if x2 <= x1 or y2 <= y1:
        return
    
    # 仅复制需要处理的局部区域
    overlay = canvas[y1:y2, x1:x2].copy()
    
    # 在局部区域上绘制填充圆（调整坐标为局部坐标）
    local_center = (x - x1, y - y1)
    cv2.circle(overlay, local_center, radius, color, -1)
    
    # 仅对局部区域进行加权融合
    canvas[y1:y2, x1:x2] = cv2.addWeighted(
        overlay, opacity, 
        canvas[y1:y2, x1:x2], 1 - opacity, 
        0
    )
    
    # 绘制不透明边框（在原图上）
    if thickness > 0:
        cv2.circle(canvas, center, radius, color, thickness)


def draw_gradient_point(canvas, point, color, size=20, steps=5, opacity=1.0):
    """绘制渐变点，支持整体透明度，仅局部处理以提高效率"""
    x, y = int(point[0]), int(point[1])  # 确保坐标为整数
    max_radius = size  # 最大半径
    
    # 计算整体需要处理的区域（包含所有同心圆）
    x1 = max(0, x - max_radius)
    y1 = max(0, y - max_radius)
    x2 = min(canvas.shape[1], x + max_radius)
    y2 = min(canvas.shape[0], y + max_radius)

    if x2 <= x1 or y2 <= y1:
        return

    
    
    # 提取基础局部区域（只复制一次）
    base_roi = canvas[y1:y2, x1:x2].copy()
    current_roi = base_roi.copy()  # 用于累积绘制的局部区域
    
    # 局部坐标系转换
    local_x = x - x1
    local_y = y - y1
    
    for i in range(steps):
        # 由外向内依次绘制，最外层最透明，最内层最不透明
        t = (steps - i) / steps
        radius = int(max_radius * t)
        alpha = opacity * t
        
        # 在临时图层上绘制当前圆
        overlay = base_roi.copy()
        cv2.circle(overlay, (local_x, local_y), radius, color, -1)
        
        # 仅对局部区域进行加权融合
        current_roi = cv2.addWeighted(overlay, alpha, current_roi, 1 - alpha, 0)
    
    # 将处理好的局部区域放回原图
    canvas[y1:y2, x1:x2] = current_roi


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

        # 绘制1个箭头
        draw_arrow(canvas, start, current_arrow_tip, color, thickness, size)


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


from PIL import ImageFont, ImageDraw, Image


def draw_button(canvas, position, size, text, color=(0, 255, 0), text_color=(255, 255, 255), font_scale=1, thickness=2,
                font_path="simhei.ttf"):
    x, y = position
    w, h = size
    radius = min(w, h) // 4
    # 阴影
    shadow_offset = 8
    shadow_color = (50, 50, 50)
    overlay = canvas.copy()
    # 绘制阴影（比按钮略大，偏移）
    cv2.rectangle(overlay, (x + radius + shadow_offset, y + shadow_offset),
                  (x + w - radius + shadow_offset, y + h + shadow_offset), shadow_color, -1)
    cv2.rectangle(overlay, (x + shadow_offset, y + radius + shadow_offset),
                  (x + w + shadow_offset, y + h - radius + shadow_offset), shadow_color, -1)
    cv2.ellipse(overlay, (x + radius + shadow_offset, y + radius + shadow_offset), (radius, radius), 180, 0, 90,
                shadow_color, -1)
    cv2.ellipse(overlay, (x + w - radius + shadow_offset, y + radius + shadow_offset), (radius, radius), 270, 0, 90,
                shadow_color, -1)
    cv2.ellipse(overlay, (x + radius + shadow_offset, y + h - radius + shadow_offset), (radius, radius), 90, 0, 90,
                shadow_color, -1)
    cv2.ellipse(overlay, (x + w - radius + shadow_offset, y + h - radius + shadow_offset), (radius, radius), 0, 0, 90,
                shadow_color, -1)
    cv2.addWeighted(overlay, 0.3, canvas, 0.7, 0, canvas)

    # ----------- 新增：绘制按钮本体（圆角矩形） -----------
    overlay2 = canvas.copy()
    # 主体矩形
    cv2.rectangle(overlay2, (x + radius, y), (x + w - radius, y + h), color, -1)
    cv2.rectangle(overlay2, (x, y + radius), (x + w, y + h - radius), color, -1)
    # 四角圆弧
    cv2.ellipse(overlay2, (x + radius, y + radius), (radius, radius), 180, 0, 90, color, -1)
    cv2.ellipse(overlay2, (x + w - radius, y + radius), (radius, radius), 270, 0, 90, color, -1)
    cv2.ellipse(overlay2, (x + radius, y + h - radius), (radius, radius), 90, 0, 90, color, -1)
    cv2.ellipse(overlay2, (x + w - radius, y + h - radius), (radius, radius), 0, 0, 90, color, -1)
    # 叠加到canvas（不透明）
    cv2.addWeighted(overlay2, 1.0, canvas, 0.0, 0, canvas)
    # ----------- 新增结束 -----------

    # 将OpenCV的BGR图像转换为PIL的RGB图像
    img_pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try:
        font = ImageFont.truetype(font_path, int(32 * font_scale))
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = x + (w - text_width) // 2
    text_y = y + (h - text_height) // 2
    draw.text((text_x, text_y), text, font=font, fill=(text_color[2], text_color[1], text_color[0]))
    canvas[:, :, :] = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def draw_multiple_buttons(canvas, buttons_texts, size, color, text_color, font_scale, thickness, conditions=None,
                          highlight_color=(0, 200, 255),real_shape = None):
    button_width, button_height = size
    num_buttons = len(buttons_texts)
    spacing = canvas.shape[1] // (num_buttons) if real_shape == None else real_shape[0] // (num_buttons)
    for i, text in enumerate(buttons_texts):
        x = i * spacing + spacing//2 - button_width // 2 if real_shape == None else canvas.shape[1]//2 - real_shape[0]//2 + (i ) * spacing +spacing//2 - button_width // 2
        y = canvas.shape[0] // 4 - button_height // 2
        btn_color = highlight_color if (conditions and i < len(conditions) and conditions[i]) else color
        draw_button(canvas, (x, y), size, text, btn_color, text_color, font_scale, thickness)
        


def draw_pose_with_buttons(canvas, buttons_config, rt_landmarks_list, condition, colors=PTS_PAIR_COLORS,real_shape = None):
    """在画布上绘制姿态和按钮"""
    # 绘制姿态点
    for idx, rt_lm_pt in enumerate(rt_landmarks_list):
        if rt_lm_pt:
            rt_lm_pt = (int(rt_lm_pt[0]), int(rt_lm_pt[1]))

            # if condition[idx]:
            #     color = ARROW_COLORS["achieve"]
            # else:
            color = colors[idx % len(colors)]

            draw_gradient_point(canvas, rt_lm_pt, color, size=30, steps=2)

    # 绘制按钮
    draw_multiple_buttons(
        canvas,
        buttons_config["texts"],
        size=buttons_config["size"],
        color=buttons_config["color"],
        text_color=buttons_config["text_color"],
        font_scale=buttons_config["font_scale"],
        thickness=buttons_config["thickness"],
        conditions=condition,  # 新增
        highlight_color=(0, 200, 255),  # 高亮色可自定义
        real_shape = real_shape
    )

    return canvas


if __name__ == "__main__":
    # 测试按钮绘制：
    canvas = np.zeros((720, 1280, 3), dtype=np.uint8)  # 创建一个黑色画布
    TEST_BUTTONS_CONFIG = {
        "texts": ["太极操", "八法五步", "24式太极拳"],
        "size": (200, 100),
        "color": (155, 155, 0),
        "text_color": (255, 255, 255),
        "font_scale": 1,
        "thickness": 2
    }
    TEST_RT_LANDMARKS_LIST = [(100, 100), (200, 200), (300, 300), (400, 400)]
    TEST_CONDITION = [True, False, True, False]  # 条件列表
    TEST_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]  # 测试颜色列表
    canvas = draw_pose_with_buttons(canvas,
                                    buttons_config=TEST_BUTTONS_CONFIG,
                                    rt_landmarks_list=TEST_RT_LANDMARKS_LIST,
                                    condition=TEST_CONDITION,
                                    colors=PTS_PAIR_COLORS)
    cv2.imshow("Test Buttons", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# @A last new line here:
