# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/4/29 21:11
# @Content : 

import cv2
import numpy as np

PTS_PAIR_COLORS = [
    (255, 78, 0),    # rgb(0, 78, 255)
    (23, 210, 255),  # rgb(255, 210, 23)
    (255, 78, 0),    # rgb(0, 78, 255)
    (23, 210, 255),  # rgb(255, 210, 23)
]

ARROW_COLORS = {
    "normal": (0, 0, 255),    # BGR红色   rgb(155, 0, 0)
    "achieve": (0, 255, 0),   # BGR绿色   rgb(0, 100, 0)
}

ARROW_NUM = 2
ARROW_SIZE = 12
ARROW_THICKNESS = 6

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
        draw_transparent_circle(canvas, std_lm_pt, radius=35, color=color, opacity=0.3, thickness=2)
        
        # 绘制实时点（配对配色）
        if rt_lm_pt:
            rt_lm_pt = (int(rt_lm_pt[0]), int(rt_lm_pt[1]))
            draw_gradient_point(canvas, rt_lm_pt, color, size=30, steps=2)

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

def draw_transparent_circle(canvas, center, radius, color, opacity=0.5, thickness=2):
    """在 canvas 上绘制一个透明填充但边缘不透明的圆
    参数：
      canvas   -- 要绘制的图像
      center   -- 圆心坐标 (x, y)
      radius   -- 半径
      color    -- BGR 颜色元组，如 (0, 255, 0)
      opacity  -- 填充透明度，范围 [0.0, 1.0]
      thickness-- 边框线宽（正数），若设置为 -1 则为实心
    """
    # 在一个 overlay 上画填充圆
    overlay = canvas.copy()
    cv2.circle(overlay, center, radius, color, -1)
    # 将 overlay 以 opacity 叠加到原图
    cv2.addWeighted(overlay, opacity, canvas, 1 - opacity, 0, canvas)
    # 再在原图上绘制不透明的边框
    cv2.circle(canvas, center, radius, color, thickness)

def draw_gradient_point(canvas, point, color, size=20, steps=5, opacity=1.0):
    """绘制渐变点，支持整体透明度"""
    # 用原始画布做底板，每次循环都从底板 copy 出 overlay
    base = canvas.copy()
    for i in range(steps):
        # 由外向内依次绘制，最外层最透明，最内层最不透明
        t = (steps - i) / steps
        radius = int(size * t)
        alpha = opacity * t
        overlay = base.copy()
        cv2.circle(overlay, point, radius, color, -1)
        cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

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

def draw_button(canvas, position, size, text, color=(0, 255, 0), text_color=(255, 255, 255), font_scale=1, thickness=2, font_path="simhei.ttf"):
    """在画布上绘制一个按钮，支持中文"""
    x, y = position
    w, h = size
    # 绘制按钮矩形
    # 创建一个 overlay 用于绘制半透明圆角矩形
    overlay = canvas.copy()
    radius = min(w, h) // 4  # 圆角半径可调
    # 绘制圆角矩形（填充，全部半透明，无不透明边框）
    cv2.rectangle(overlay, (x + radius, y), (x + w - radius, y + h), color, -1)
    cv2.rectangle(overlay, (x, y + radius), (x + w, y + h - radius), color, -1)
    cv2.ellipse(overlay, (x + radius, y + radius), (radius, radius), 180, 0, 90, color, -1)
    cv2.ellipse(overlay, (x + w - radius, y + radius), (radius, radius), 270, 0, 90, color, -1)
    cv2.ellipse(overlay, (x + radius, y + h - radius), (radius, radius), 90, 0, 90, color, -1)
    cv2.ellipse(overlay, (x + w - radius, y + h - radius), (radius, radius), 0, 0, 90, color, -1)
    # 叠加半透明
    cv2.addWeighted(overlay, 0.6, canvas, 0.4, 0, canvas)
    # 将OpenCV的BGR图像转换为PIL的RGB图像
    img_pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try:
        font = ImageFont.truetype(font_path, int(32 * font_scale))
    except:
        font = ImageFont.load_default()
    # 使用 textbbox 获取文本边界框
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = x + (w - text_width) // 2
    text_y = y + (h - text_height) // 2
    draw.text((text_x, text_y), text, font=font, fill=(text_color[2], text_color[1], text_color[0]))
    # 转回OpenCV的BGR格式
    canvas[:,:,:] = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

def draw_multiple_buttons(canvas, buttons_texts, size, color=(0, 255, 0), text_color=(255, 255, 255), font_scale=1, thickness=2):
    """在画布上绘制多个按钮
    参数：
        canvas       -- 要绘制的图像
        buttons_texts-- 按钮文本列表
        size         -- 每个按钮的大小 (width, height)
        color        -- 按钮颜色
        text_color   -- 按钮文本颜色
        font_scale   -- 文本缩放比例
        thickness    -- 文本线宽
    """
    button_width, button_height = size
    num_buttons = len(buttons_texts)
    # buttons_positions = []

    # 计算按钮间距
    spacing = canvas.shape[1] // (num_buttons + 1)  # 3 个按钮间距为 w / 4

    for i, text in enumerate(buttons_texts):
        # 计算每个按钮的位置
        x = (i + 1) * spacing - button_width // 2       # 水平均分布
        y = canvas.shape[0] // 2 - button_height // 2  # 垂直居中
        draw_button(canvas, (x, y), size, text, color, text_color, font_scale, thickness)
        # buttons_positions.append((x, y))

    # 返回的是按钮位置列表！！！
    # return buttons_positions

def draw_pose_with_buttons(canvas, buttons_config, rt_landmarks_list, condition, colors=PTS_PAIR_COLORS):
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
    draw_multiple_buttons(canvas, 
                          buttons_config["texts"], 
                          size=buttons_config["size"], 
                          color=buttons_config["color"],
                          text_color=buttons_config["text_color"], 
                          font_scale=buttons_config["font_scale"], 
                          thickness=buttons_config["thickness"])
    
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
