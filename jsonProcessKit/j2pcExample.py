from jsonProcessKit import Json2PreviewClass as j2pc
import cv2
import numpy as np
from config.common_data import COLOR, POSE_CONNECTIONS

"""
Json2PreviewClass.py 库使用说明 (as jsonProcessKit)

0. 读取json文件，所有帧存入frames：
    使用 jsonProcessKit.get_json_frames(...) 方法

1. 指定坐标位置绘制骨架：
    jsonProcessKit.draw_pose_at_pos(...)

2. 指定起始终止坐标位置、提前多少秒，生成预览坐标：
    先初始化预览坐标生成器：get_coords = jsonProcessKit.PreviewCoordsGenerator(...) 使用get_coords接方法
    然后在主循环中使用 get_coords.get_preview_coords_only(...) 获取预览坐标，返回值为两个骨架的坐标
    最后使用 jsonProcessKit.draw_preview_area(...) 绘制预览区域
"""

# 读取json文件，所有帧存入frames
frames = []
json_dir = "D:\Desktop\output_poses.json"
j2pc.get_json_frames(frames, json_dir)
print(frames)

# 摄像头帧率
camera_fps = 30

# 窗口大小
win_width, win_height = 1920, 1080
cv2.namedWindow('Motion Preview', cv2.WINDOW_NORMAL)

# 预览坐标生成器初始化
get_coords = j2pc.PreviewCoordsGenerator(preview_start_center_pos = (1900, 800),    # 骨架平移起始位置
                                         preview_end_center_pos = (1300, 800),       # 结束位置
                                         preview_time = 0.8,                          # 提前几秒
                                         fps = camera_fps,                          # 摄像头帧率
                                         current_idx = 0,                           # 当前帧索引
                                         frames = frames,                           # 所有帧
                                         scale=0.9)                                 # 骨架缩放比例（关节点半径、连线粗细不受此参数影响）

if __name__ == "__main__":
    # 主循环
    for current_idx in range(len(frames)):

        # 创建画布
        canvas = np.zeros((win_height, win_width, 3), dtype=np.uint8)

        """主骨架区"""
        # 使用draw_pose_at_pos绘制主骨架（小红）
        # TODO:: 怎么按时间戳或者帧索引做到与视频同步？与预览同步？
        j2pc.draw_pose_at_pos(canvas,  # 画布
                              frames[current_idx],  # 当前帧
                              center_pos=(400,500),  # 骨架中心指定位置
                              color_point=COLOR['red'],  # 节点颜色
                              color_line=COLOR['green'],  # 连线颜色
                              radius=8,  # 节点半径
                              thickness=5,  # 连线粗细
                              connections=POSE_CONNECTIONS)                      # 骨架连接关系（默认为data.py中的connections）

        """预览区"""
        # 获取预览坐标（小蓝、小黄）
        moving_sket_coords, do_it_sket_coords = get_coords.get_preview_coords_only(current_idx,frames[current_idx])
        # 绘制预览区域
        j2pc.draw_preview_area(canvas,
                               moving_sket_coords,  # 小蓝
                               do_it_sket_coords,  # 小黄
                               moving_color_point = COLOR['blue'],
                               moving_color_line = COLOR['babyblue'],
                               moving_radius = 12,  # 小蓝的节点半径
                               moving_thickness = 10,  # 小蓝的连线粗细
                               do_it_color_point = COLOR['yellow'],
                               do_it_color_line = COLOR['lightyellow'],
                               do_it_radius = 12,  # 小黄的节点半径
                               do_it_thickness = 10,  # 小黄的连线粗细
                               connections = POSE_CONNECTIONS)                  # 骨架连接关系（默认为data.py中的connections）
        # 显示
        cv2.imshow('Motion Preview', canvas)

        # 控制播放速度
        key = cv2.waitKey(int(1000/camera_fps))                 # fps在循环外定义
        # 按键控制
        if key == 27 or key == ord('q') or key == ord('Q'):     # ESC、q、Q退出
            break
        elif key == ord(' '):                                   # 空格暂停
            cv2.waitKey(0)

    # 释放窗口
    cv2.destroyAllWindows()