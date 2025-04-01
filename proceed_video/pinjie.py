import cv2
import numpy as np
import os

def images_to_video(image_folder, output_path, fps=30):
    # 获取文件夹中的所有图片文件
    images = [img for img in os.listdir(image_folder) if img.endswith((".png", ".PNG"))]
    images.sort()  # 按文件名排序，确保顺序正确

    if not images:
        print("没有找到图片文件！")
        return

    # 读取第一张图片以获取视频尺寸
    first_image_path = os.path.join(image_folder, images[0])
    frame = cv2.imread(first_image_path, cv2.IMREAD_UNCHANGED)  # 保留透明通道
    height, width, layers = frame.shape

    # 检查是否包含透明通道（4通道表示有Alpha）
    if layers != 4:
        print("图片不含透明通道，将按普通图片处理")
        frame = cv2.imread(first_image_path)  # 重新读取为3通道
        height, width, layers = frame.shape

    # 定义视频编码器和输出
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用 mp4v 编码
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # 逐帧写入视频
    for image in images:
        image_path = os.path.join(image_folder, image)
        frame = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)  # 读取带透明通道的图片

        if frame.shape[2] == 4:  # 如果有透明通道
            # 分离RGB和Alpha通道
            rgb = frame[:, :, :3]
            alpha = frame[:, :, 3]
            # 将透明部分处理为黑色背景（或其他背景色）
            background = np.zeros_like(rgb, dtype=np.uint8)
            frame = np.where(alpha[:, :, np.newaxis] > 0, rgb, background)
        else:
            frame = cv2.imread(image_path)  # 无透明通道时直接读取

        # 确保帧大小一致
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))

        video_writer.write(frame)  # 写入帧

    # 释放资源
    video_writer.release()
    print(f"视频已保存至: {output_path}")

# 使用示例
if __name__ == "__main__":
    image_folder = "out_person_transparent"  # 替换为你的图片文件夹路径
    output_video = "fin_.mp4"     # 输出视频文件名
    fps = 24                             # 每秒帧数，可调整
    images_to_video(image_folder, output_video, fps)
