import cv2
import os
import time
from pathlib import Path


def load_images_from_folder(folder):
    """加载指定文件夹中的所有图片文件"""
    image_files = sorted([f for f in os.listdir(folder)
                          if f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
    images = []
    for image_file in image_files:
        image_path = os.path.join(folder, image_file)
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)  # 保留透明通道
        if img is not None:
            images.append(img)
    return images


def overlay_image(background, overlay, x, y):
    """将带有透明通道的图片叠加到背景上"""
    # 获取叠加图片的尺寸
    h, w = overlay.shape[:2]

    # 确保叠加区域在背景图像范围内
    if x + w > background.shape[1] or y + h > background.shape[0]:
        return background

    # 分离前景图片的 BGR 和 Alpha 通道
    if overlay.shape[2] == 4:  # 如果有 Alpha 通道
        bgr = overlay[:, :, :3]
        alpha = overlay[:, :, 3] / 255.0
    else:  # 如果没有 Alpha 通道，直接使用图片
        bgr = overlay
        alpha = None

    # 计算叠加区域
    roi = background[y:y + h, x:x + w]

    # 如果有透明通道，进行 Alpha 混合
    if alpha is not None:
        for c in range(3):  # 对每个颜色通道进行混合
            roi[:, :, c] = (1 - alpha) * roi[:, :, c] + alpha * bgr[:, :, c]
    else:
        roi[:] = bgr  # 无透明通道直接覆盖

    background[y:y + h, x:x + w] = roi
    return background


def main():
    # 设置图片文件夹路径
    image_folder = r"F:\task\media_pipe\proceed_video\out_person_transparent"
    if not os.path.exists(image_folder):
        print(f"文件夹 {image_folder} 不存在！")
        return

    # 加载图片
    images = load_images_from_folder(image_folder)
    if not images:
        print("文件夹中没有找到图片！")
        return

    # 打开摄像头
    cap = cv2.VideoCapture(0)  # 0 表示默认摄像头
    if not cap.isOpened():
        print("无法打开摄像头！")
        return

    # 设置显示间隔（秒）
    display_interval = 0.007  # 每 0.007 秒切换一次图片
    last_switch_time = time.time()
    image_index = 0

    while True:
        # 读取摄像头帧
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头帧！")
            break

        # 左右镜像翻转摄像头画面
        frame = cv2.flip(frame, 1)  # 1 表示水平翻转（左右镜像）

        # 获取当前时间
        current_time = time.time()

        # 如果超过显示间隔，切换图片
        if current_time - last_switch_time >= display_interval:
            image_index = (image_index + 1) % len(images)  # 循环显示图片
            last_switch_time = current_time

        # 调整叠加图片大小（可选，按比例缩放）
        overlay_img = images[image_index]
        scale = 0.5  # 缩放到 50% 大小
        new_height = int(overlay_img.shape[0] * scale)
        new_width = int(overlay_img.shape[1] * scale)
        overlay_img = cv2.resize(overlay_img, (new_width, new_height))

        # 计算右上角位置
        x_offset = frame.shape[1] - new_width - 10  # 距离右边 10 像素
        y_offset = 10  # 距离顶部 10 像素

        # 叠加图片到右上角
        frame = overlay_image(frame, overlay_img, x_offset, y_offset)

        # 显示结果
        cv2.imshow("Camera with Overlay", frame)

        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
