# -*- coding: utf-8 -*-
import cv2
import numpy as np
from cvzone.PoseModule import PoseDetector
from config.common_data import WIN_SIZE, POSE_CONNECTIONS, COLOR
from jsonProcessKit import Json2PreviewClass as j2pc

# 新增绘图参数配置
VISUAL_CONFIG = {
    "arrow": {
        "thickness": 4,
        "size": 20,
        "num_arrows": 3,
        "checkmark_size": 15
    },
    "gradient": {
        "max_radius": 30,
        "steps": 5,  # 减少 steps 以提高性能
        "std_color": (255, 191, 0),  # 标准点颜色
        "real_color": (72, 209, 204)  # 实时点颜色
    }
}

POSE_LANDMARKS = {
    "left_wrist": 15,
    "right_wrist": 16,
    "left_ankle": 27,
    "right_ankle": 28
}

std_masked_frames_dir = "stdProcess/masked_sampled_std_frames"  # 标准抽样遮罩帧保存路径
sampled_json_dir = "stdProcess/sampled_std_frames.json"  # 抽样后的 JSON 文件路径
std_masked_frames_save_dir = "stdProcess/masked_sampled_std_frames"  # 抽样后、遮罩后帧保存路径

win_width, win_height = WIN_SIZE
camera_fps = 30


def draw_checkmark_arrow(canvas, start_point, end_point, color, thickness, arrow_size):
    """绘制对号形状的动态箭头"""
    dx, dy = end_point[0] - start_point[0], end_point[1] - start_point[1]
    length = np.hypot(dx, dy)
    if length == 0:
        return
    dx, dy = dx / length, dy / length
    checkmark_point1 = (int(end_point[0] - arrow_size * (dx + dy)),
                        int(end_point[1] - arrow_size * (dy - dx)))
    checkmark_point2 = (int(end_point[0] - arrow_size * (dx - dy)),
                        int(end_point[1] - arrow_size * (dy + dx)))
    cv2.line(canvas, checkmark_point1, end_point, color, thickness)
    cv2.line(canvas, checkmark_point2, end_point, color, thickness)


def draw_gradient_point(canvas, center, color, max_radius=30, steps=5):
    """绘制渐变点效果"""
    overlay = canvas.copy()
    for i in range(steps):
        radius = int(max_radius * (i + 1) / steps)
        alpha = 1.0 - (i / steps)
        cv2.circle(overlay, center, radius, color, -1)
        cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)


def draw_arrows_on_path(canvas, start, end, color):
    """在路径上绘制多个动态箭头"""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = np.hypot(dx, dy)
    if length == 0:
        return

    config = VISUAL_CONFIG["arrow"]
    for i in range(1, config["num_arrows"] + 1):
        t = i / (config["num_arrows"] + 1)
        current = (
            int(start[0] + t * dx),
            int(start[1] + t * dy)
        )
        draw_checkmark_arrow(canvas, start, current, color,
                             config["thickness"], config["checkmark_size"])


def draw_points_to_reach(canvas, std_points, real_points, threshold=50):
    """优化后的指导点绘制函数"""
    if not std_points or not real_points:
        return False

    all_points_matched = True
    for (std, real), name in zip(zip(std_points, real_points), POSE_LANDMARKS.keys()):
        std_pos = (int(std[0]), int(std[1]))
        real_pos = (int(real[0]), int(real[1]))

        # 绘制渐变点
        draw_gradient_point(canvas, std_pos, VISUAL_CONFIG["gradient"]["std_color"],
                            VISUAL_CONFIG["gradient"]["max_radius"],
                            VISUAL_CONFIG["gradient"]["steps"])
        draw_gradient_point(canvas, real_pos, VISUAL_CONFIG["gradient"]["real_color"],
                            VISUAL_CONFIG["gradient"]["max_radius"] // 2,
                            VISUAL_CONFIG["gradient"]["steps"] // 2)

        # 计算距离并绘制动态路径
        distance = np.linalg.norm(np.array(std) - np.array(real))
        if distance > threshold:
            all_points_matched = False
            arrow_color = COLOR["red"]
        else:
            arrow_color = COLOR["green"]

        # 绘制动态箭头路径
        draw_arrows_on_path(canvas, real_pos, std_pos, arrow_color)

    # 如果所有点都匹配，显示完成提示
    if all_points_matched:
        cv2.putText(canvas, "所有点已匹配！", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    return all_points_matched


def main():
    # 初始化标准数据
    sampled_json_dir = "stdProcess/sampled_std_frames.json"
    std_json_frames = []
    j2pc.get_json_frames(std_json_frames, sampled_json_dir)
    original_std_size = (win_width, win_height)  # 将标准视频分辨率调整为窗口大小

    # 摄像头初始化
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：摄像头初始化失败！")
        return

    cv2.namedWindow("Realtime Guide", cv2.WINDOW_NORMAL)
    detector = PoseDetector()

    # 标准帧控制
    std_mask_idx = 0
    json_line_idx = 0

    while cap.isOpened():
        # 读取实时帧
        success, image = cap.read()
        if not success:
            continue

        # 实时骨架检测
        image = cv2.flip(image, 1)
        imageSket = detector.findPose(image, draw=False)  # 关闭内置绘图
        sketList, _ = detector.findPosition(imageSket, draw=False)

        # 创建画布
        canvas = cv2.resize(image, (win_width, win_height))  # 直接使用摄像头内容作为画布

        # 加载标准掩膜帧
        std_masked_frame_path = f"{std_masked_frames_save_dir}/masked_frame_{std_mask_idx:05d}.png"
        overlay = cv2.imread(std_masked_frame_path, cv2.IMREAD_UNCHANGED)
        if overlay is not None:
            overlay = cv2.resize(overlay, (win_width, win_height))
            if overlay.shape[2] == 4:
                alpha = overlay[:, :, 3] / 255.0
                for c in range(3):
                    canvas[:, :, c] = (overlay[:, :, c] * alpha +
                                       canvas[:, :, c] * (1 - alpha))

        # 获取标准骨架点
        std_points = []
        if json_line_idx < len(std_json_frames):
            frame_data = std_json_frames[json_line_idx]
            poses = np.array(frame_data["poses"]).reshape(33, 3)
            std_points = [
                (
                    max(0, min(win_width - 1, int(poses[landmark][0] * (win_width / original_std_size[0])))),
                    max(0, min(win_height - 1, int(poses[landmark][1] * (win_height / original_std_size[1]))))
                )
                for landmark in POSE_LANDMARKS.values()
            ]

        # 获取实时骨架点
        real_points = []
        if sketList:
            cam_width, cam_height = image.shape[1], image.shape[0]
            real_points = [
                (sketList[landmark][0] * (win_width / cam_width),
                 sketList[landmark][1] * (win_height / cam_height))
                if landmark < len(sketList) else (0, 0)
                for landmark in POSE_LANDMARKS.values()
            ]

        # 自动帧推进逻辑：完全由四个箭头都变绿控制
        if std_points and real_points:
            all_points_matched = draw_points_to_reach(canvas, std_points, real_points)
            if all_points_matched:  # 当所有点都匹配时跳转
                if json_line_idx < len(std_json_frames) - 1:
                    json_line_idx += 1
                    std_mask_idx = std_json_frames[json_line_idx]["frame_idx"]
                else:
                    print("已完成所有动作序列！")
                    cv2.putText(canvas, "已完成所有动作序列！", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 显示合成画面
        cv2.imshow("Realtime Guide", canvas)

        # 按键控制
        key = cv2.waitKey(1)
        if key == 27:  # ESC 键退出
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
