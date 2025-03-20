from ProcessKit import Json2PreviewClass as j2pc
import cv2
import numpy as np
from Config.common_data import COLOR, POSE_CONNECTIONS, WIN_SIZE, clear_directory
import os
from tqdm import tqdm
import shutil

def get_img_from_json(json_dir, 
                      save_dir,
                      direct_copy_from_std_frame_dir=False,
                      fps=30,
                      scale=1,
                      color_point=0,
                      color_line=0,
                      radius=13,
                      thickness=24, 
                      at_position=False,
                      display_sket=False, 
                      canvas_size=WIN_SIZE):

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    clear_directory(save_dir)  # 清空保存目录
    
    print("Json2Images: 开始从 JSON 文件生成图片...")
    # 读取json文件到frames列表
    frames = []
    j2pc.get_json_frames(frames, json_dir)

    if direct_copy_from_std_frame_dir:
        std_dir = direct_copy_from_std_frame_dir
        # 直接从标准帧目录复制图片
        for frame in tqdm(frames, total=len(frames), desc="直接从标准图片集内拷贝抽样帧"):
            frame_idx = frame['frame_idx'] + 1
            std_img = os.path.join(std_dir, f"frame_{frame_idx:05d}.png")
            if not os.path.exists(std_img):
                raise FileNotFoundError("没有找到抽样帧，请将v2j.get_std_json的save_frames设为True")
            std_img = os.path.join(std_dir, f"frame_{frame_idx:05d}.png")
            dest_img = os.path.join(save_dir, f"frame_{frame_idx:05d}.png")
            shutil.copy(std_img, dest_img)
        print(f"Json2Images: 已从标准帧目录 {std_dir} 转存采样帧到 {save_dir}！", "\n")


    if not direct_copy_from_std_frame_dir:
        # 逐帧绘制，加入 tqdm 进度条
        for frame in tqdm(frames, total=len(frames), desc="处理图片帧"):

            # 初始化画布
            canvas_width, canvas_height = canvas_size
            canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255  # 白色背景

            # 调用绘制函数
            # ! 注意：to_position 慎重，否则json文件的坐标和绘制火柴人坐标不一致，保存的图片与json文件不匹配
            # 现在：不使用to_position
            j2pc.better_draw_pos_scale(canvas, pose=frame, frame_type='dict', scale=scale, at_position=at_position, radius=radius, thickness=thickness, connections=POSE_CONNECTIONS, use_ground=False, color_point=color_point, color_line=color_line)

            if display_sket:
                # 显示当前帧
                cv2.imshow("Pose Detection", canvas)

            # 获取当前帧索引
            frame_idx = frame['frame_idx'] + 1

            # 保存当前帧
            img_dir = os.path.join(save_dir, f"frame_{frame_idx:05d}.png")  # 生成文件名
            cv2.imwrite(img_dir, canvas)  # 保存图像

            # 按键控制窗口
            key = cv2.waitKey(int(1000/fps))  # 等待指定时间
            if key == 27 or key == ord('q') or key == ord('Q'):
                break
            elif key == ord(' '):
                cv2.waitKey(0)
        print(f"Json2Images: 已保存采样帧到 {save_dir}！", "\n")

    # 释放资源
    cv2.destroyAllWindows()
