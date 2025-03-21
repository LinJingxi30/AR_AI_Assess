import cv2
import numpy as np
import matplotlib.pyplot as plt
from Config.common_data import COLOR, clear_directory
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
    output_image = cv2.erode(output_image, kernel, iterations=1)  # 减少腐蚀次数（降低腐蚀次数，提高细节）
    # 膨胀n次
    output_image = cv2.dilate(output_image, kernel, iterations=1)  # 增加膨胀次数

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

def main():
    pass