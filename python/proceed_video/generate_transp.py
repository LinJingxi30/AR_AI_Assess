import cv2
import numpy as np
import os


def extract_dancer_bodybox_with_transparency(video_path, output_folder):
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

    # 第二步：根据最大边界框处理每一帧，绿色部分变透明
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 将绿色背景转换为掩码
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # 反转掩码，人物区域为255，背景为0
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

            # 创建带alpha通道的统一画布（初始全透明）
            uniform_frame = np.zeros((max_height, max_width, 4), dtype=np.uint8)

            # 从原始帧中裁剪出人物区域
            dancer_roi = frame[y:y + h, x:x + w]

            # 创建对应的人物区域掩码
            roi_mask = mask[y:y + h, x:x + w]

            # 将人物区域转换为带alpha通道的格式
            dancer_roi_bgra = cv2.cvtColor(dancer_roi, cv2.COLOR_BGR2BGRA)
            dancer_roi_bgra[:, :, 3] = roi_mask  # alpha通道使用掩码

            # 将人物放置在画布中心
            uniform_frame[pad_top:pad_top + h, pad_left:pad_left + w] = dancer_roi_bgra

            # 保存到输出文件夹（PNG支持透明）
            output_path = os.path.join(output_folder, f"dancer_{frame_count:04d}.png")
            cv2.imwrite(output_path, uniform_frame)

        frame_count += 1

    cap.release()
    print(f"处理完成！共处理 {frame_count} 帧，输出尺寸为 {max_width}x{max_height}")


# 使用示例
video_path = "movie_004.mp4"  # 输入视频路径
output_folder = "out_xuni_person_transparent"  # 输出抠图的文件夹

extract_dancer_bodybox_with_transparency(video_path, output_folder)

# 可选：用 ffmpeg 拼接回视频（注意：需要支持透明的格式，如 mov）
# ffmpeg -i out_person_transparent/dancer_%04d.png -c:v png -pix_fmt rgba output_video.mov
