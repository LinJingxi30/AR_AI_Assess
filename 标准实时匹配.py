# -*- coding: utf-8 -*-            
# @Author :
# @Time : 2025/3/16 20:36
# @Content : 

import cv2
import numpy as np
from cvzone.PoseModule import PoseDetector
from config.common_data import WIN_SIZE, POSE_CONNECTIONS, COLOR
from jsonProcessKit import Json2PreviewClass as j2pc


std_masked_frames_dir = "stdProcess/masked_sampled_std_frames"  # 标准抽样遮罩帧保存路径
sampled_json_dir = "stdProcess/sampled_std_frames.json" # 抽样后的 JSON 文件路径
std_masked_frames_save_dir = "stdProcess/masked_sampled_std_frames"  # 抽样后、遮罩后帧保存路径

win_width, win_height = WIN_SIZE
camera_fps = 30


def draw_mask(canvas, mask_idx):
    pass



# def draw_points_to_reach(canvas, std_spd_msk_frame, points_set, color=COLOR["blue"], radius=10):
#     """根据需要画的部位points_set，画出对应的点。"""

def main():
    # 从 JSON 文件读取标准抽样遮罩帧-字典
    std_json_frames = []
    j2pc.get_json_frames(std_json_frames, sampled_json_dir)

    cap = cv2.VideoCapture(0)   # 帧来源：摄像头0
    if not cap.isOpened():
        print("错误：摄像头初始化失败！")
        return
    else:
        print("摄像头初始化成功！开始进行姿态检测...")
    cv2.namedWindow("Realtime Guide", cv2.WINDOW_NORMAL)

    # 初始化姿态检测器
    detector = PoseDetector()

    # 初始化标准帧索引
    std_mask_idx = 0
    json_line_idx = 0
    condition = 0
    while cap.isOpened():
        condition += 1

        # 读取实时帧 image
        success, image = cap.read()
        if not success:
            continue    # 实时读取帧要求不中断

        # 获取实时骨架
        imageSket = detector.findPose(image, draw=True) # 画骨架
        sketList, bndboxInfo = detector.findPosition(imageSket, draw=False) # 不画bndbox

        # 创建画布
        canvas = np.ones((win_height, win_width, 3), dtype=np.uint8) * 255

        # 将检测到的实时骨架图拉伸到画布的尺寸，并绘制在画布上
        resizedImage = cv2.resize(imageSket, (win_width, win_height))
        canvas[:, :] = cv2.flip(resizedImage, 1)

        # 绘制骨架
        # if sketList:
        #     # todo:: 骨架整体横坐标不在摄像头正中央；左右颠倒，需镜像对称
        #     j2pc.draw_pose_at_pos_in_scale(canvas, frame_type='list', pose=sketList, scale=1, at_position=False, color_point=COLOR["blue"], color_line=COLOR["lightyellow"], radius=10, thickness=8, connections = POSE_CONNECTIONS)
        # else:
        #     print("未检测到骨架！")


        # 若达到范围要求，指针后移
        if condition % 30 == 0:  # 每30帧更新一次
            if json_line_idx < len(std_json_frames) - 1:  # 判断是否到达最后一帧
                # 指向 JSON 读取字典的下一行
                json_line_idx += 1
                # 更新抽样索引
                std_mask_idx = std_json_frames[json_line_idx]["frame_idx"] + 1
            else:
                print("已到达最后一帧！")
                break

        # 从 std_masked_frames_save_dir 获取当前帧的标准抽样遮罩帧
        # 通过 std_mask_idx 进行文件名查找
        std_masked_frame_path = f"{std_masked_frames_save_dir}\\masked_frame_{std_mask_idx:05d}.png"

        # 将遮罩帧png图像绘制到画布上
        overlay = cv2.imread(std_masked_frame_path, cv2.IMREAD_UNCHANGED)
        if overlay is None:
            print("无法加载图像:", std_masked_frame_path)
        else:
            overlay = cv2.resize(overlay, (win_width, win_height))
            if overlay.shape[2] == 4:
                bgr_overlay = overlay[:, :, :3]
                alpha = overlay[:, :, 3] / 255.0
                alpha = alpha[:, :, None]
                canvas[:] = (bgr_overlay * alpha + canvas * (1 - alpha)).astype(np.uint8)
            else:
                canvas[:] = overlay

        # 绘制实时画面
        cv2.imshow("Realtime Guide", canvas)

        # 按键控制
        key = cv2.waitKey(int(1000/camera_fps))
        if key == 27 or key == ord('q') or key == ord('Q'):
            break
        elif key == ord(' '):
            cv2.waitKey(0)
    
    cap.release()
    cv2.destroyAllWindows()
    print("停止姿态检测！")

if __name__ == "__main__":
    main()


# @A last new line here:
