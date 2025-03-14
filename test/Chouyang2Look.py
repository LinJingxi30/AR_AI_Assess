from j2pc import Json2PreviewClass as j2pc
import cv2
import numpy as np
from config.common_data import COLOR, POSE_CONNECTIONS
import os
# 读取 JSON 文件，所有帧存入 frames
frames = []
json_dir = r"D:\Desktop\output_poses22.json"  # 替换为你的 JSON 文件路径
j2pc.get_json_frames(frames, json_dir)

# 创建保存结果的文件夹
output_dir = r"D:\Desktop\output_frames22_black"  # 替换为你想保存的文件夹路径
os.makedirs(output_dir, exist_ok=True)  # 如果文件夹不存在，则创建

# 初始化画布
canvas_width, canvas_height = 1920, 1080  # 固定画布大小
canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255  # 白色背景

# 设置绘制参数
scale = 1.0  # 缩放比例
center_pos = (canvas_width // 2, canvas_height // 2)  # 画布中心位置
color_point = (203, 192, 255)  # 关键点颜色
color_line = (150, 100, 150)  # 连接线颜色
radius = 13  # 关键点半径
thickness = 24  # 连接线厚度

# 逐帧绘制
for frame_count, frame in enumerate(frames):
    # 清空画布
    canvas.fill(255)  # 重置为白色背景

    # 调用绘制函数
    j2pc.better_draw_pos_scale(canvas, frame, scale, center_pos, color_point, color_line, radius, thickness, POSE_CONNECTIONS)

    # 显示当前帧
    cv2.imshow("Pose Detection", canvas)

    # 保存当前帧
    output_path = os.path.join(output_dir, f"frame_{frame_count:04d}.png")  # 生成文件名
    cv2.imwrite(output_path, canvas)  # 保存图像
    print(f"Saved: {output_path}")

    # 按 'q' 退出
    if cv2.waitKey(100) == ord('q'):
        break

# 释放资源
cv2.destroyAllWindows()
