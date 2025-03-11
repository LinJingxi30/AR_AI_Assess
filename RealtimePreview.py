"""
测试实时相机+preview的效果
"""
import cv2
import numpy as np
from cvzone.PoseModule import PoseDetector

from CenterCoordProcess import coord_relativize
from j2pc import Json2PreviewClass as j2pc
from config.common_data import COLOR, POSE_CONNECTIONS
from drawSkeleton import draw

def main():
    # 初始化cvzone PoseDetector
    detector = PoseDetector()

    # 读取json文件
    frames = []
    json_dir = 'savedjsons/relatetest.json'
    j2pc.get_json_frames(frames, json_dir)

    # 基础设置
    camera_fps = 30
    cap = cv2.VideoCapture(0)
    win_width, win_height = 1920, 1080
    cv2.namedWindow('Realtime Preview', cv2.WINDOW_NORMAL)

    # 预览坐标生成器初始化
    get_coords = j2pc.PreviewCoordsGenerator(
        preview_start_center_pos=(1900, 800),
        preview_end_center_pos=(1300, 800),
        preview_time=0.8,
        fps=camera_fps,
        current_idx=0,
        frames=frames,
        scale=0.9)

    current_idx = 0
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        # 创建画布
        # canvas = np.zeros((win_height, win_width, 3), dtype=np.uint8)
        canvas = np.ones((win_height, win_width, 3), dtype=np.uint8) * 255
        
        # cvzone处理
        image = detector.findPose(image)
        lmList, bboxInfo = detector.findPosition(image)

        

        # 以指定坐标为中心点，指定缩放绘制：实时骨架
        if lmList:
            # 调用方法coord_relativize 使用脚底坐标作为中心点（相对坐标转换）
            lmList = coord_relativize(lmList, use_ground=True)
            frame = {"poses": np.reshape(lmList, -1)}
            j2pc.better_draw_pos_scale(canvas,  # 画布
                                            frame,  # 当前帧
                                            scale=0.5,  # 缩放比例
                                            center_pos=(350, 900),  # 骨架中心指定位置
                                            color_point=COLOR['red'],  # 节点颜色
                                            color_line=COLOR['green'],  # 连线颜色
                                            radius=8,  # 节点半径
                                            thickness=5,  # 连线粗细
                                            connections=POSE_CONNECTIONS)  # 骨架连接关系（默认为data.py中的connections）

            # 绘制预览区域
            moving_sket_coords, do_it_sket_coords = get_coords.get_preview_coords_only(current_idx, frame)
            j2pc.draw_preview_area(canvas,
                                moving_sket_coords,
                                do_it_sket_coords,
                                moving_color_point=COLOR['blue'],
                                moving_color_line=COLOR['babyblue'],
                                moving_radius=12,
                                moving_thickness=10,
                                do_it_color_point=COLOR['yellow'],
                                do_it_color_line=COLOR['lightyellow'],
                                do_it_radius=12,
                                do_it_thickness=10)
        else:
            canvas = image

        # 显示
        cv2.imshow('Realtime Preview', canvas)
        current_idx = (current_idx + 1) % len(frames)

        # 按键控制
        key = cv2.waitKey(int(1000/camera_fps))
        if key == 27 or key == ord('q') or key == ord('Q'):
            break
        elif key == ord(' '):
            cv2.waitKey(0)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
