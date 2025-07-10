# -*- coding: utf-8 -*-            
# @Author :
# @Time : 2025/4/10 14:42
# @Content :

import cv2
import os
import numpy as np
import glob
from tqdm import tqdm
from Config.common_data import WIN_SIZE

def create_video_from_png(input_img_dir, output_video_path, win_size, background_color=(0, 255, 0), fps=24):
    # 构造 png 文件路径列表，并按文件名排序（例如 C0077_0001.png）
    img_paths = sorted(glob.glob(os.path.join(input_img_dir, "*.png")))
    if not img_paths:
        print("未找到png图片")
        return

    # 定义视频编码与 VideoWriter 对象
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, win_size)

    for img_path in tqdm(img_paths, desc="Processing images"):
        # 读取图片
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            continue

        # 如果图片带有 alpha 通道，则进行透明背景的处理
        if img.shape[2] == 4:
            # 将png背景透明部分合成到纯色底上（注意cv2使用BGR格式）
            alpha_channel = img[:, :, 3] / 255.0
            img_bgr = img[:, :, :3]
            # 创建与图片大小一致的纯色背景
            bg = np.full(img_bgr.shape, background_color, dtype=np.uint8)
            img = cv2.convertScaleAbs(img_bgr * alpha_channel[..., np.newaxis] + bg * (1 - alpha_channel[..., np.newaxis]))
        # 否则，不处理直接使用

        # 图片尺寸与背景尺寸
        img_h, img_w = img.shape[:2]
        win_w, win_h = win_size

        # 计算缩放比例，按宽高适配
        scale = min(win_w / img_w, win_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 创建背景画布
        canvas = np.full((win_h, win_w, 3), background_color, dtype=np.uint8)
        # 计算居中位置
        x_offset = (win_w - new_w) // 2
        y_offset = (win_h - new_h) // 2

        # 粘贴图片到背景画布上
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_img

        # 写入视频帧
        video_writer.write(canvas)

    video_writer.release()
    print("视频保存到：", output_video_path)

#
# def create_video_from_png_transparent(input_img_dir, output_video_path, win_size, fps=24):
#     # 获取目录下所有png图片，并排序
#     img_paths = sorted(glob.glob(os.path.join(input_img_dir, "*.png")))
#     if not img_paths:
#         print("未找到png图片")
#         return
#
#     win_w, win_h = win_size
#     # 使用支持透明通道的 PNG 编码器创建 VideoWriter 对象
#     fourcc = cv2.VideoWriter_fourcc(*'PNG ')
#     video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (win_w, win_h), True)
#
#     for img_path in tqdm(img_paths, desc="Processing images"):
#         # 读取图片（保留 alpha 通道）
#         img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
#         if img is None:
#             continue
#
#         # 如果图片只有3通道，则转换为4通道
#         if img.shape[2] == 3:
#             img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
#
#         # 图片尺寸与背景尺寸
#         img_h, img_w = img.shape[:2]
#         scale = min(win_w / img_w, win_h / img_h)
#         new_w = int(img_w * scale)
#         new_h = int(img_h * scale)
#         resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
#
#         # 创建全透明背景画布（BGRA）
#         canvas = np.zeros((win_h, win_w, 4), dtype=np.uint8)
#
#         # 计算居中位置
#         x_offset = (win_w - new_w) // 2
#         y_offset = (win_h - new_h) // 2
#
#         # 将缩放后的图片复制到画布上（注意：如果图片带透明，则会融合）
#         canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_img
#
#         # 写入视频帧（注意 VideoWriter 仅支持 BGR 格式，故先转换为BGR+A）
#         video_writer.write(canvas)
#
#     video_writer.release()
#     print("透明视频保存到：", output_video_path)

def save_resized_png_transparent(input_img_dir, output_img_dir, win_size):
    # 如果输出目录不存在则创建
    if not os.path.exists(output_img_dir):
        os.makedirs(output_img_dir)

    # 获取目录下所有 png 图片路径，并按文件名排序
    img_paths = sorted(glob.glob(os.path.join(input_img_dir, "*.png")))
    if not img_paths:
        print("未找到png图片")
        return

    win_w, win_h = win_size

    current_idx = 0
    for img_path in tqdm(img_paths, desc="Processing images"):
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            continue

        # 如果图片为三通道，则转换为四通道
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

        h, w = img.shape[:2]
        scale = min(win_w / w, win_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 创建全透明背景的画布（BGRA，alpha=0）
        canvas = np.zeros((win_h, win_w, 4), dtype=np.uint8)
        x_offset = (win_w - new_w) // 2
        y_offset = (win_h - new_h) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

        out_path = os.path.join(output_img_dir, f"frame_{current_idx:05d}.png")
        current_idx += 1
        cv2.imwrite(out_path, canvas)
        cv2.imwrite(out_path, canvas)

    print("全透明图片已保存到：", output_img_dir)

if __name__ == '__main__':
    input_img = r"E:\WeChat\Chat_record\xwechat_files\wxid_tp1yuspiigso22_4579\msg\file\2025-04\taiji_all"
    input_img = r"E:\WeChat\Chat_record\xwechat_files\wxid_tp1yuspiigso22_4579\msg\file\2025-04\allall"

    green_video = "taiji_allall25.mp4"
    green_output_video_dir = os.path.join(r"E:\WeChat\Chat_record\xwechat_files\wxid_tp1yuspiigso22_4579\msg\file\2025-04\allall", green_video)

    alpha_img_out = r"E:\WeChat\Chat_record\xwechat_files\wxid_tp1yuspiigso22_4579\msg\file\2025-04\allall\alpha"

    win_size = WIN_SIZE
    bg_color = (0,255,0)
    create_video_from_png(input_img, green_output_video_dir, win_size, bg_color, fps=25)
    # save_resized_png_transparent(input_img, alpha_img_out, win_size)

# @A last new line here:

