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
from config import POSE_LANDMARKS

from multiprocessing import Process, Queue
from queue import Empty


# 路径配置 Path(MEDIA_PIPE_ROOT) / "相对根目录路径"
std_masked_frames_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/masked_sampled_std_frames"  # 标准抽样遮罩帧保存路径
std_sampled_json_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/sampled_std_frames.json"  # 抽样后的 JSON 文件路径
std_masked_frames_save_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/masked_sampled_std_frames"  # 抽样后、遮罩后帧保存路径

# 窗口参数
win_width, win_height = WIN_SIZE
original_std_size = (win_width, win_height)  # 将标准视频分辨率调整为窗口大小
camera_fps = 30




# 定义骨架检测进程（worker）
def skeleton_detector_worker(frame_queue, result_queue, use_flip=False):
    from cvzone.PoseModule import PoseDetector
    import cv2
    detector = PoseDetector()
    while True:
        frame = frame_queue.get()
        if frame is None:
            break  # 退出信号
        if use_flip:
            frame = cv2.flip(frame, 1)
        imageSket = detector.findPose(frame, draw=False)
        sketList, _ = detector.findPosition(imageSket, draw=False)
        result_queue.put(sketList)

# 定义条件判断进程（worker）
def condition_checker_worker(cond_input_queue, cond_result_queue, distance_threshold):
    import numpy as np
    from config import POSE_LANDMARKS
    while True:
        data = cond_input_queue.get()
        if data is None:
            break
        std_points, realtime_points = data
        condition_dict = {}
        overall = True
        if not std_points or not realtime_points:
            overall = False
            for key in POSE_LANDMARKS.keys():
                condition_dict[key] = False
        else:
            for key, (std, real) in zip(POSE_LANDMARKS.keys(), zip(std_points, realtime_points)):
                distance = np.linalg.norm(np.array(std) - np.array(real))
                if distance > distance_threshold:
                    condition_dict[key] = False
                    overall = False
                else:
                    condition_dict[key] = True
        cond_result_queue.put((condition_dict, overall))

class RealtimePractice:
    def __init__(self, distance_threshold=50):
        import numpy as np
        from Config.common_data import WIN_SIZE
        self.canvas = np.zeros((WIN_SIZE[1], WIN_SIZE[0], 3), dtype=np.uint8)
        self.pose_detector = None  # 骨架检测将在进程中初始化
        self.std_sampled_json_dict = []
        self.std_sampled_masked_frames = []
        self.std_points = []
        self.realtime_points = []
        self.overlay = None
        self.distance_threshold = distance_threshold
        from config import POSE_LANDMARKS
        self.condition_dict = {landmark: False for landmark in POSE_LANDMARKS.keys()}
        self.condition_overall = False
        import cv2
        self.cap = cv2.VideoCapture(0)
        self.load_std_data()
        self.cap_init()
        self.json_line_idx = 0      # 标准点索引
        self.std_overlay_idx = 0    # 掩膜索引

    def load_std_data(self):
        from ProcessKit import Json2PreviewClass as j2pc
        from pathlib import Path
        from Config.common_data import WIN_SIZE
        MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent
        std_sampled_json_dir = MEDIA_PIPE_ROOT / "StdProcess/sampled_std_frames.json"
        std_masked_frames_save_dir = MEDIA_PIPE_ROOT / "StdProcess/masked_sampled_std_frames"
        j2pc.get_json_frames(self.std_sampled_json_dict, std_sampled_json_dir)
        for idx in range(len(self.std_sampled_json_dict)):
            frame_path = f"{std_masked_frames_save_dir}/masked_frame_{idx:05d}.png"
            import cv2
            overlay = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
            if overlay is not None:
                from Config.common_data import WIN_SIZE
                overlay = cv2.resize(overlay, (WIN_SIZE[0], WIN_SIZE[1]))
            self.std_sampled_masked_frames.append(overlay)

    def cap_init(self):
        if not self.cap.isOpened():
            print("错误：摄像头初始化失败！")
            return

    def get_std_points(self):
        from config import POSE_LANDMARKS
        from Config.common_data import WIN_SIZE
        win_width, win_height = WIN_SIZE
        original_std_size = (win_width, win_height)
        if self.json_line_idx < len(self.std_sampled_json_dict):
            frame_data = self.std_sampled_json_dict[self.json_line_idx]
            import numpy as np
            poses = np.array(frame_data["poses"]).reshape(33, 3)
            self.std_points = [
                (
                    max(0, min(win_width - 1, int(poses[landmark][0] * (win_width / original_std_size[0])))),
                    max(0, min(win_height - 1, int(poses[landmark][1] * (win_height / original_std_size[1]))))
                )
                for landmark in POSE_LANDMARKS.values()
            ]
        return self.std_points

    def get_realtime_points(self, sketList):
        import cv2
        cam_width, cam_height = self.cap.get(3), self.cap.get(4)
        from config import POSE_LANDMARKS
        self.realtime_points = [
            (
                sketList[landmark][0] * (cv2.getTrackbarPos("win_width", "Realtime Guide") / cam_width) if cam_width > 0 else 0,
                sketList[landmark][1] * (cv2.getTrackbarPos("win_height", "Realtime Guide") / cam_height) if cam_height > 0 else 0
            )
            if landmark < len(sketList) else (0, 0)
            for landmark in POSE_LANDMARKS.values()
        ]
        return self.realtime_points

    def get_std_overlay(self, std_overlay_idx=None):
        self.overlay = self.std_sampled_masked_frames[std_overlay_idx]
        return self.overlay

    def update_conditioning(self, std_points=None, realtime_points=None, distance_threshold=None):
        from config import POSE_LANDMARKS
        if not self.std_points or not self.realtime_points:
            all_points_matched = False
            for key in self.condition_dict.keys():
                self.condition_dict[key] = False
        else:
            all_points_matched = True
            import numpy as np
            for key, (std, real) in zip(POSE_LANDMARKS.keys(), zip(std_points, realtime_points)):
                distance = np.linalg.norm(np.array(std) - np.array(real))
                if distance > distance_threshold:
                    self.condition_dict[key] = False
                    all_points_matched = False
                else:
                    self.condition_dict[key] = True
        return self.condition_dict, all_points_matched

    def idx_update(self, condition=False):
        if condition:
            if self.json_line_idx < len(self.std_sampled_json_dict) - 1:
                self.json_line_idx += 1
                self.std_overlay_idx = self.std_sampled_json_dict[self.json_line_idx]["frame_idx"] + 1
            else:
                # todo:: 完成所有动作序列
                pass
        return self.json_line_idx, self.std_overlay_idx

    def get_sket_list(self, image, use_flip=False):
        # 这里不再使用同步检测（仅作为备用），实际使用多进程结果
        if use_flip:
            import cv2
            image = cv2.flip(image, 1)
        imageSket = self.pose_detector.findPose(image, draw=False) if self.pose_detector else image
        sketList, _ = self.pose_detector.findPosition(imageSket, draw=False) if self.pose_detector else ([], None)
        return sketList

    def main_loop(self):
        import cv2
        from Config.common_data import WIN_SIZE
        win_width, win_height = WIN_SIZE

        # 创建多进程队列
        frame_queue = Queue()
        sket_result_queue = Queue()
        cond_input_queue = Queue()
        cond_result_queue = Queue()

        # 启动骨架检测进程和条件判断进程
        sket_process = Process(target=skeleton_detector_worker, args=(frame_queue, sket_result_queue, False))
        cond_process = Process(target=condition_checker_worker, args=(cond_input_queue, cond_result_queue, self.distance_threshold))
        sket_process.start()
        cond_process.start()

        # 设置摄像头参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 15)

        # 使用缓存保存上一次检测结果（防止队列暂时无新数据）
        cached_sketList = None
        cached_condition = (self.condition_dict, self.condition_overall)

        while self.cap.isOpened():
            success, image = self.cap.read()
            if not success:
                continue

            # 翻转图像并发送到骨架检测进程（绘图部分可以并行处理，不阻塞）
            image = cv2.flip(image, 1)
            frame_queue.put(image)

            # 尝试非阻塞获取骨架检测结果
            try:
                cached_sketList = sket_result_queue.get_nowait()
            except Empty:
                pass
            # 如果没有新结果，则使用上一次的结果，若都没有则可以采用同步检测（作为后备）
            if cached_sketList is None:
                sketList = self.get_sket_list(image, use_flip=False)
            else:
                sketList = cached_sketList

            # 绘制实时摄像头画面及叠加标准掩膜
            self.canvas = Draw.draw_realtime_cap_only(self.canvas, image)
            Draw.draw_overlay_on_canvas(self.canvas, self.overlay)

            # 获取标准与实时 LANDMARK 坐标
            self.std_points = self.get_std_points()
            self.realtime_points = self.get_realtime_points(sketList)

            # 将检测数据发送给条件判断进程
            cond_input_queue.put((self.std_points, self.realtime_points))
            try:
                cached_condition = cond_result_queue.get_nowait()
            except Empty:
                pass
            self.condition_dict, self.condition_overall = cached_condition

            # 更新掩膜/点索引
            self.json_line_idx, self.std_overlay_idx = self.idx_update(self.condition_overall)
            self.overlay = self.get_std_overlay(self.std_overlay_idx)

            # 绘制标准与实时点以及箭头
            Draw.draw_points_with_arrow(self.canvas, self.std_points, self.realtime_points, self.condition_dict)

            # 显示最终合成的画面
            cv2.imshow("Realtime Guide", self.canvas)
            key = cv2.waitKey(1)
            if key == 27:
                break

        # 退出前发送终止信号并等待子进程结束
        frame_queue.put(None)
        cond_input_queue.put(None)
        sket_process.join()
        cond_process.join()
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    rp = RealtimePractice()
    rp.main_loop()