import sys
from pathlib import Path
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(MEDIA_PIPE_ROOT))
import cv2
import numpy as np
from cvzone.PoseModule import PoseDetector
from Config.common_data import WIN_SIZE, COLOR
from ProcessKit import Json2PreviewClass as j2pc
import draw
from draw import POSE_LANDMARKS


# 路径配置 Path(MEDIA_PIPE_ROOT) / "相对根目录路径"
std_masked_frames_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/masked_sampled_std_frames"  # 标准抽样遮罩帧保存路径
sampled_json_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/sampled_std_frames.json"  # 抽样后的 JSON 文件路径
std_masked_frames_save_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/masked_sampled_std_frames"  # 抽样后、遮罩后帧保存路径

# 窗口参数
win_width, win_height = WIN_SIZE
original_std_size = (win_width, win_height)  # 将标准视频分辨率调整为窗口大小
camera_fps = 30


def main():
    # 初始化标准数据
    std_json_frames = []
    j2pc.get_json_frames(std_json_frames, sampled_json_dir)

    # 初始化时预加载所有遮罩图像
    masked_frames = []
    for idx in range(len(std_json_frames)):
        frame_path = f"{std_masked_frames_save_dir}/masked_frame_{idx:05d}.png"
        overlay = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
        if overlay is not None:
            overlay = cv2.resize(overlay, original_std_size)
        masked_frames.append(overlay)


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
        overlay = masked_frames[std_mask_idx]  # 直接读取内存中的预加载帧
        # std_masked_frame_path = f"{std_masked_frames_save_dir}/masked_frame_{std_mask_idx:05d}.png"
        # overlay = cv2.imread(std_masked_frame_path, cv2.IMREAD_UNCHANGED)
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
            all_points_matched = Draw.draw_points_to_reach(canvas, std_points, real_points)
            if all_points_matched:  # 当所有点都匹配时跳转
                if json_line_idx < len(std_json_frames) - 1:
                    json_line_idx += 1
                    std_mask_idx = std_json_frames[json_line_idx]["frame_idx"] + 1
                else:
                    print("已完成所有动作序列！")
                    cv2.putText(canvas, "已完成所有动作序列！", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 打印实时帧率
        # fps = int(cap.get(cv2.CAP_PROP_FPS))
        # cv2.putText(canvas, f"FPS: {fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR["red"], 2)


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
