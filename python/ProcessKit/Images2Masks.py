from sys import stderr

import cv2
import numpy as np
from Config.common_data import COLOR, clear_directory, WIN_SIZE
import os
from tqdm import tqdm


def get_glow_edge(frame, contours, color=COLOR['babyblue'], thickness=4):
    """使用指定的颜色和线宽在BGRA图像上绘制轮廓边缘，并添加高斯模糊以实现柔化和发光效果"""
    bgr = frame[..., :3].copy()
    alpha = frame[..., 3].copy()
    
    # 在黑色画布上绘制轮廓，同时保持透明背景
    temp = np.zeros_like(bgr)
    cv2.drawContours(temp, contours, -1, color[:3], thickness)
    
    # 膨胀边缘，使发光效果更加明显
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(temp, kernel, iterations=1)
    
    # 对膨胀后的图像应用高斯模糊，模糊核可根据需要调整
    glow = cv2.GaussianBlur(dilated, (21, 21), 0)
    
    # 合成原始边缘与发光效果，glow权重可根据需求调整
    combined = cv2.addWeighted(temp, 1, glow, 1, 0)
    
    # 将发光效果叠加到原图BGR通道，同时保持原始的alpha通道不变
    result_bgr = cv2.add(bgr, combined)
    result = cv2.merge([result_bgr[..., 0], result_bgr[..., 1], result_bgr[..., 2], alpha])
    return result


def get_edge(frame, contours, color=COLOR['blue'], thickness=10):
    """使用指定的颜色和线宽在BGRA图像上绘制轮廓边缘，不改变alpha通道"""
    # 分离BGR和alpha通道，确保绘制时不影响透明度
    bgr = frame[..., :3].copy()
    alpha = frame[..., 3].copy()

    # 在BGR图像上绘制所有轮廓边缘（不填充）
    cv2.drawContours(bgr, contours, -1, color[:3], thickness)

    # 将更新后的BGR和原始alpha通道组合回BGRA图像
    result = cv2.merge([bgr[..., 0], bgr[..., 1], bgr[..., 2], alpha])
    return result


def get_alpha_background(frame, contours, bg_opacity=0.5, color_glow=COLOR['lightyellow'], thickness=10):
    """获取灰度遮罩mask"""
    # 获取灰度图
    mask_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 将灰度图填充为黑色（0）
    mask_gray = np.zeros_like(mask_gray)

    # 填充人体为白色（255）
    cv2.fillPoly(mask_gray, pts=contours, color=255)
    # cv2.imwrite("display\\mask.png", mask_gray)

    """计算透明遮罩alpha"""
    # 将人物区域填充为0（透明），背景区域填充为255（不透明）
    alpha = cv2.bitwise_not(mask_gray)  # 恰好是mask_gray的反转

    # 背景（白色）透明度设置为bg_opacity
    alpha = cv2.multiply(alpha, bg_opacity)
    
    # 将frame拓展至BGRA
    result = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    # 清空BGR颜色通道
    result[..., :3] = 0

    # 使用遮罩alpha，把背景图的透明通道对人物进行扣除
    result[..., 3] = alpha   # 将alpha通道替换为我们计算的alpha

    thickness = int(thickness)  # 确保线条粗细为整数

    result = get_glow_edge(result, contours, color=color_glow, thickness=thickness)  # 添加发光边缘

    cv2.imwrite("../display/alpha.png", result)

    return result


def get_alpha_glow_border(image_path, color_threshold, bg_opacity=0.5, color_glow=COLOR['lightyellow'], thickness=10):

    # 读取图像
    image = cv2.imread(image_path)

    # 高斯滤波
    image = cv2.GaussianBlur(image, (5, 5), 0)

    # 计算每个像素的亮度
    brightness = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 定义背景的亮度阈值
    background_mask = brightness > color_threshold

    # 创建一个与原图像相同的空白图像
    output_image = np.zeros_like(image)

    # 将背景部分替换为白色
    output_image[background_mask] = [255, 255, 255]  # 白色

    # 将非背景部分（人）保留
    output_image[~background_mask] = image[~background_mask]

    # 定义卷积核
    kernel = np.ones((5, 5), np.uint8)
    # 腐蚀n次
    output_image = cv2.erode(output_image, kernel, iterations=7)  # 减少腐蚀次数（降低腐蚀次数，提高细节）
    # 膨胀n次
    output_image = cv2.dilate(output_image, kernel, iterations=2)  # 增加膨胀次数

    # 转为灰度图像并二值化
    gray_output = cv2.cvtColor(output_image, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray_output, 240, 255, cv2.THRESH_BINARY_INV)

    # 边缘检测
    edges = cv2.Canny(binary_image, 50, 150)  # 调整Canny的阈值

    # 检测轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 创建一个空白画布用于绘制平滑的边缘
    edge_image = np.zeros_like(image)

    # 绘制平滑的边缘
    for contour in contours:
        # 逼近轮廓以获得平滑的曲线
        epsilon = 5  # 减少逼近精度，提高细节
        approx = cv2.approxPolyDP(contour, epsilon, True)
        cv2.drawContours(edge_image, [approx], -1, (255, 255, 255), thickness=5)

    # 绘制轮廓边缘
    background_alpha = get_alpha_background(image, contours, bg_opacity=bg_opacity, color_glow=color_glow, thickness=thickness)

    return background_alpha  # 返回透明挖孔背景图像


def get_folder_masked_imgs(from_dir, save_dir, display_masked_img=False, overlayThreshold=155, bg_opacity=0.5, color_glow=COLOR['lightyellow'], thickness=10):
    print("开始获取抽样遮罩标准帧...")
    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    # 清空保存目录
    clear_directory(save_dir)

    # 遍历目录中的所有图像文件
    for filename in tqdm(os.listdir(from_dir), total=len(os.listdir(from_dir)), desc="获取抽样遮罩标准帧"):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            image_path = os.path.join(from_dir, filename)
            image = cv2.imread(image_path)

            # 处理图像
            alpha_mask = get_alpha_glow_border(image_path, color_threshold=overlayThreshold, bg_opacity=bg_opacity, color_glow=color_glow, thickness=thickness)

            """可选：显示处理后的图像"""
            if display_masked_img:
                cv2.imshow('Masked Image', alpha_mask)
                cv2.waitKey(500)

            # 保存处理后的图像
            save_path = os.path.join(save_dir, "masked_" + filename)
            cv2.imwrite(save_path, alpha_mask)
    cv2.destroyAllWindows()
    print(f"已保存遮罩标准帧到 {save_dir}！", "\n")


def overlay_images(in_glow_dir, in_alpha_dir, save_dir, WIN_SIZE=WIN_SIZE, transparency=0.7):
    """
    遍历 in_glow_dir 里的图片，与 in_alpha_dir 中对应的图片（命名规则：masked_frame_xxxxx.png 对应 frame_xxxxx.png）
    进行叠加。in_alpha_dir 图像背景全透明，叠加时将人物部分按指定透明度叠加到 in_glow_dir 图上，
    最终保存到 save_dir，并保证保存的图像为 BGRA 格式。

    参数：
        in_glow_dir: 存放 get_folder_masked_imgs 输出结果的文件夹路径
        in_alpha_dir: 存放背景全透明图片的文件夹路径
        save_dir: 保存叠加后图片的文件夹路径
        WIN_SIZE: 目标图片尺寸，如 (宽, 高)
        transparency: 人物图片的叠加透明度 (0~1)
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 获取 in_glow_dir 中的图片，按文件名排序确保顺序一致
    glow_filenames = sorted([f for f in os.listdir(in_glow_dir) if f.lower().endswith(('.png', '.jpg'))])
    for glow_file in tqdm(glow_filenames, desc="Processing glow files"):
        glow_path = os.path.join(in_glow_dir, glow_file)
        # 根据文件名前缀 masked_ 获取对应 in_alpha_dir 中图片名称
        if glow_file.startswith("masked_"):
            alpha_file = glow_file[len("masked_"):]
        else:
            # 如果不符合命名规则，则跳过
            print(glow_file, file=stderr)
            continue
        alpha_path = os.path.join(in_alpha_dir, alpha_file)
        if not os.path.exists(alpha_path):
            continue

        # 以不改变alpha通道的方式读取图像
        glow_img = cv2.imread(glow_path, cv2.IMREAD_UNCHANGED)
        alpha_img = cv2.imread(alpha_path, cv2.IMREAD_UNCHANGED)

        # 反转透明教练
        alpha_img = cv2.flip(alpha_img, 1)

        # 如果尺寸不是WIN_SIZE则调整大小（注意: cv2.resize中尺寸格式为 (宽, 高)）
        if (glow_img.shape[1], glow_img.shape[0]) != WIN_SIZE:
            glow_img = cv2.resize(glow_img, WIN_SIZE, interpolation=cv2.INTER_AREA)
        if (alpha_img.shape[1], alpha_img.shape[0]) != WIN_SIZE:
            alpha_img = cv2.resize(alpha_img, WIN_SIZE, interpolation=cv2.INTER_AREA)

        # 确保图像为四通道
        if glow_img.shape[2] == 3:
            glow_img = cv2.cvtColor(glow_img, cv2.COLOR_BGR2BGRA)
        if alpha_img.shape[2] == 3:
            alpha_img = cv2.cvtColor(alpha_img, cv2.COLOR_BGR2BGRA)

        # 转为浮点数，方便计算 (0~255)
        glow_float = glow_img.astype(np.float32)
        alpha_float = alpha_img.astype(np.float32)

        # 分离颜色与alpha
        glow_color = glow_float[..., :3]
        glow_alpha = glow_float[..., 3:4]

        alpha_color = alpha_float[..., :3]
        alpha_a = alpha_float[..., 3:4]  # 原图人物透明度，背景透明

        # 计算实际人物透明度（范围0~1）
        # 这里按原始alpha通道，再乘上用户设定的 transparency 参数
        effective_alpha = (alpha_a / 255.0) * transparency

        # 对颜色进行叠加：最终颜色 = in_alpha人物颜色 * effective_alpha + in_glow颜色 * (1-effective_alpha)
        out_color = alpha_color * effective_alpha + glow_color * (1.0 - effective_alpha)

        # 对 alpha 通道也进行叠加（这里简单地采用线性混合方式）
        out_alpha = alpha_a * transparency + glow_alpha * (1.0 - effective_alpha)

        # 合并BGR和alpha通道
        combined = np.concatenate((out_color, out_alpha), axis=2)
        # 转回 uint8
        combined = np.clip(combined, 0, 255).astype(np.uint8)

        # 保存结果
        save_path = os.path.join(save_dir, glow_file)
        cv2.imwrite(save_path, combined)

# 使用示例
# folder_path = "SavedJsons/sampled_standard_frames"
# color_threshold = 155  # 设置亮度阈值
# alpha_mask = get_alpha_glow_border(image_path, color_threshold)
# cv2.imwrite("display\\alpha_mask.png", alpha_mask)
# # 重置画布
# cv2.destroyAllWindows()
# cv2.imshow('alpha_mask', alpha_mask)
# cv2.waitKey(5000)  # 持续显示 5000 毫秒（即 5 秒）
# cv2.destroyAllWindows()

if __name__ == "__main__":
    # 测试函数
    folder_path = "SavedJsons/sampled_standard_frames"
    color_threshold = 155  # 设置亮度阈值
    alpha_mask = get_alpha_glow_border(folder_path, color_threshold)
    cv2.imwrite("display\\alpha_mask.png", alpha_mask)
    # 重置画布
    cv2.destroyAllWindows()
    cv2.imshow('alpha_mask', alpha_mask)
    cv2.waitKey(5000)  # 持续显示 5000 毫秒（即 5 秒）
    cv2.destroyAllWindows()