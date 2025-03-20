import cv2
import numpy as np

# 相机图像分辨率 h=480 w=640

# 初始化配置参数
input_source = "Static/10-1剪辑慢放.mp4"  # 输入源：视频路径 或 摄像头ID（0）
output_scale = 2.8  # 窗口显示缩放比例
crop_top = 220  # 顶部裁剪像素（切除量）
crop_bottom = 120  # 底部裁剪像素
num_windows = 10  # 分割窗口数量

# 全局变量存储当前帧分割结果（供外部调用）
current_frames = [None] * num_windows


def process_frame(frame):
    """帧处理方法"""
    # 1. 切天切地操作
    h, w = frame.shape[:2]
    # print(h, w)
    cropped = frame[crop_top:h - crop_bottom, 0:w]

    # # 2. 水平均分画面
    # split_width = w // num_windows
    # # if not hasattr(process_frame, '_printed'):
    # #     print(f"每个窗格的宽度：{split_width}pixels")
    # #     process_frame._printed = True
    # splits = []
    # for i in range(num_windows):
    #     x_start = i * split_width
    #     x_end = (i + 1) * split_width
    #     splits.append(cropped[:, x_start:x_end])
    # return splits

    # 2.2 水平精准指定分割位置
    coords = {f'split_width_line_{0}': (0, 80)}
    coords[f'split_width_line_{1}'] = (coords[f'split_width_line_{0}'][1], 148)
    coords[f'split_width_line_{2}'] = (coords[f'split_width_line_{1}'][1], 215)
    coords[f'split_width_line_{3}'] = (coords[f'split_width_line_{2}'][1], 274)
    coords[f'split_width_line_{4}'] = (coords[f'split_width_line_{3}'][1], 340)
    coords[f'split_width_line_{5}'] = (coords[f'split_width_line_{4}'][1], 384)
    coords[f'split_width_line_{6}'] = (coords[f'split_width_line_{5}'][1], 458)
    coords[f'split_width_line_{7}'] = (coords[f'split_width_line_{6}'][1], 508)
    coords[f'split_width_line_{8}'] = (coords[f'split_width_line_{7}'][1], 570)
    coords[f'split_width_line_{9}'] = (coords[f'split_width_line_{8}'][1], 640)

    # 根据字典分割视频帧
    splits = []
    for key in sorted(coords.keys()):
        start, end = coords[key]
        splits.append(cropped[:, start:end])
    return splits





if __name__ == '__main__':
    # 初始化视频流
    cap = cv2.VideoCapture(input_source)
    if not cap.isOpened():
        print("无法打开视频源")
        exit()

    # 预创建显示窗口（实时流需持久化窗口）
    for i in range(num_windows):
        cv2.namedWindow(f'Person-{i + 1}', cv2.WINDOW_AUTOSIZE)
    # for i in range(num_windows):
    #     cv2.namedWindow(f'Person-{i + 1}', cv2.WINDOW_NORMAL)
        # cv2.resizeWindow(f'Person-{i + 1}', int((cap.get(3) / num_windows) * output_scale),
        #                  int((cap.get(4) - crop_top - crop_bottom) * output_scale))

    while True:
        ret, frame = cap.read()
        if not ret:
            print("视频流结束")
            break

        # 执行处理流程
        split_frames = process_frame(frame)

        # 更新全局帧数据（深拷贝避免数据覆盖）
        for i in range(num_windows):
            current_frames[i] = split_frames[i].copy()

        # 显示所有分割画面
        for i, img in enumerate(split_frames):
            cv2.imshow(f'Person-{i + 1}', img)

        # 将存储视频写入器的属性改为列表，并在写入前逐个检测：
        for i, img in enumerate(split_frames):
            # 确保 video_writers 列表存在
            if not hasattr(process_frame, 'video_writers'):
                process_frame.video_writers = [None] * num_windows
            # 针对每个窗口，如果对应的 VideoWriter 未初始化，则初始化之，使用该分割画面的尺寸
            if process_frame.video_writers[i] is None:
                process_frame.video_writers[i] = cv2.VideoWriter(
                    rf'e:\Github\repositories\media_pipe\display\Person-{i + 1}.mp4',
                    cv2.VideoWriter_fourcc(*'mp4v'),
                    20,
                    (img.shape[1], img.shape[0])
                )
            # 写入当前帧到对应的视频文件
            process_frame.video_writers[i].write(img)

        # 退出控制（q、Q、Esc键退出）
        if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q'), 27]:  # 27 is the ASCII code for the ESC key
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()

"""
其他文件调用实时帧的方法：
1. 直接导入 current_frames 变量
   from 本文件 import current_frames
   print(current_frames[0].shape)  # 获取第一个分割画面

2. 建议使用时添加空值判断：
   if current_frames[0] is not None:
       # 处理有效帧

3. 实时性保障：循环读取时会自动更新
"""