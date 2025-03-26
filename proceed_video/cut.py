import cv2
import os


def extract_frames(video_path, output_dir, target_fps=24):
    """
    将视频文件按指定帧率提取帧并保存到目标文件夹

    参数:
        video_path (str): 视频文件的路径
        output_dir (str): 保存图片的文件夹路径
        target_fps (int): 目标帧率（默认为24fps）
    """
    # 创建输出文件夹
    os.makedirs(output_dir, exist_ok=True)

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")

    # 获取视频原始帧率
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    if original_fps <= 0:
        original_fps = target_fps  # 处理无效帧率的情况

    saved_timestamps = set()  # 记录已保存的时间戳
    frame_count = 0  # 当前处理帧数
    saved_count = 0  # 已保存帧数

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # 视频读取结束

        # 计算当前帧的时间（秒）
        current_time = frame_count / original_fps

        # 计算最接近的目标时间点
        target_time = round(current_time * target_fps) / target_fps

        if target_time not in saved_timestamps:
            # 生成文件名：frame_0000.jpg, frame_0001.jpg...
            output_path = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
            cv2.imwrite(output_path, frame)
            saved_timestamps.add(target_time)
            saved_count += 1

        frame_count += 1

    cap.release()
    print(f"成功保存 {saved_count} 张图片到 {output_dir}")


# 使用示例
if __name__ == "__main__":
    extract_frames("./video1.mp4", "output", 24)