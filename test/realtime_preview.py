import cv2
import mediapipe as mp
import numpy as np
from j2pc import Json2PreviewClass as j2pc
from config.common_data import COLOR, POSE_CONNECTIONS

def main():
    # 初始化MediaPipe
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)

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
        canvas = np.zeros((win_height, win_width, 3), dtype=np.uint8)
        
        # MediaPipe处理
        image.flags.writeable = False
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        if results.pose_landmarks:
            # 绘制实时骨架
            for connection in POSE_CONNECTIONS:
                start_idx = connection[0]
                end_idx = connection[1]
                
                start_point = results.pose_landmarks.landmark[start_idx]
                end_point = results.pose_landmarks.landmark[end_idx]
                
                x1, y1 = int(start_point.x * win_width), int(start_point.y * win_height)
                x2, y2 = int(end_point.x * win_width), int(end_point.y * win_height)
                
                cv2.line(canvas, (x1, y1), (x2, y2), COLOR['red'], 5)
                cv2.circle(canvas, (x1, y1), 8, COLOR['green'], -1)
                cv2.circle(canvas, (x2, y2), 8, COLOR['green'], -1)

        # 绘制预览区域
        moving_sket_coords, do_it_sket_coords = get_coords.get_preview_coords_only(current_idx)
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

        # 显示
        cv2.imshow('Realtime Preview', canvas)
        current_idx = (current_idx + 1) % len(frames)

        # 按键控制
        key = cv2.waitKey(int(1000/camera_fps))
        if key == 27 or key == ord('q') or key == ord('Q'):
            break
        elif key == ord(' '):
            cv2.waitKey(0)

    pose.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
