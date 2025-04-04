import cv2
import numpy as np
import os


def extract_dancer_bodybox(video_path, output_folder):
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("无法打开视频文件")

    # 第一步：预览视频，找到最大边界框
    max_width = 0
    max_height = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 将绿色背景转换为掩码
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 40, 40])  # 绿色范围下限
        upper_green = np.array([85, 255, 255])  # 绿色范围上限
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # 反转掩码，得到人物区域
        mask = cv2.bitwise_not(mask)

        # 找到人物的轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # 更新最大尺寸
            max_width = max(max_width, w)
            max_height = max(max_height, h)

    # 重置视频到开头
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # 第二步：根据最大边界框处理每一帧并保存，保留绿色背景
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 将绿色背景转换为掩码
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_green, upper_green)
        mask = cv2.bitwise_not(mask)

        # 找到人物的轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # 计算填充边界，使人物居中于最大框
            pad_left = (max_width - w) // 2
            pad_right = max_width - w - pad_left
            pad_top = (max_height - h) // 2
            pad_bottom = max_height - h - pad_top

            # 创建统一大小的画布，初始化为原始帧的扩展版本
            uniform_frame = np.zeros((max_height, max_width, 3), dtype=np.uint8)

            # 计算原始帧中需要裁剪的区域，保留绿色背景
            frame_h, frame_w = frame.shape[:2]
            crop_x_start = max(0, x - pad_left)
            crop_x_end = min(frame_w, x + w + pad_right)
            crop_y_start = max(0, y - pad_top)
            crop_y_end = min(frame_h, y + h + pad_bottom)

            # 从原始帧中裁剪出扩展区域
            cropped_frame = frame[crop_y_start:crop_y_end, crop_x_start:crop_x_end]

            # 计算裁剪区域在统一画布中的位置
            place_y_start = pad_top - (y - crop_y_start)
            place_y_end = place_y_start + (crop_y_end - crop_y_start)
            place_x_start = pad_left - (x - crop_x_start)
            place_x_end = place_x_start + (crop_x_end - crop_x_start)

            # 将裁剪区域放入统一画布
            uniform_frame[place_y_start:place_y_end, place_x_start:place_x_end] = cropped_frame

            # 保存到输出文件夹
            output_path = os.path.join(output_folder, f"dancer_{frame_count:04d}.png")
            cv2.imwrite(output_path, uniform_frame)

        frame_count += 1

    cap.release()
    print(f"处理完成！共处理 {frame_count} 帧，输出尺寸为 {max_width}x{max_height}")


# 使用示例
video_path = "movie_004.mp4"  # 输入视频路径
output_folder = "out_person"  # 输出抠图的文件夹

extract_dancer_bodybox(video_path, output_folder)

# 可选：用 ffmpeg 拼接回视频
# ffmpeg -i out_person/dancer_%04d.png -c:v libx264 -pix_fmt yuv420p output_video.mp4
