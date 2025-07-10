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


# 路径配置 Path(MEDIA_PIPE_ROOT) / "相对根目录路径"
std_masked_frames_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/masked_sampled_std_frames"  # 标准抽样遮罩帧保存路径
std_sampled_json_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/sampled_std_frames.json"  # 抽样后的 JSON 文件路径
std_masked_frames_save_dir = Path(MEDIA_PIPE_ROOT) / "StdProcess/masked_sampled_std_frames"  # 抽样后、遮罩后帧保存路径


# 窗口参数
win_width, win_height = WIN_SIZE
original_std_size = (win_width, win_height)  # 将标准视频分辨率调整为窗口大小
camera_fps = 30


class RealtimePractice:
    def __init__(self, distance_threshold=50):
        self.canvas = np.zeros((win_height, win_width, 3), dtype=np.uint8)
        self.pose_detector = PoseDetector()
        self.std_sampled_json_dict = []
        self.std_sampled_masked_frames = []
        self.std_points = []
        self.realtime_points = []
        self.overlay = None
        self.distance_threshold = distance_threshold
        self.condition_dict = {landmark: False for landmark in POSE_LANDMARKS.keys()}
        self.condition_overall = False
        self.cap = cv2.VideoCapture(0)
        self.load_std_data()
        self.cap_init()
        self.json_line_idx = 0      # 标准点
        self.std_overlay_idx = 0    # 掩膜
        

    def load_std_data(self):
        """加载标准数据"""
        # 加载标准采样数据 JSON 字典
        j2pc.get_json_frames(self.std_sampled_json_dict, std_sampled_json_dir)
        # print(self.std_sampled_json_dict)  # 调试
        # 加载标准采样掩膜帧
        for i in range(len(self.std_sampled_json_dict)):
            frame_idx = self.std_sampled_json_dict[i]["frame_idx"]
            frame_path = f"{std_masked_frames_save_dir}/masked_frame_{frame_idx:05d}.png"
            overlay = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
            if overlay is not None:
                overlay = cv2.resize(overlay, original_std_size)
                self.std_sampled_masked_frames.append(overlay)
        # print(self.std_sampled_masked_frames)   # 调试
        # print(f"标准遮罩集长度{len(self.std_sampled_masked_frames)}")   # 调试


    def cap_init(self):
        """初始化摄像头"""
        if not self.cap.isOpened():
            print("错误：摄像头初始化失败！")
            return
        

    def get_std_points(self):
        """
        获取标准对齐点坐标
        返回: self.std_points (list): 由 POSE_LANDMARKS字典 指定的标准对齐点坐标列表。
        """
        if self.json_line_idx < len(self.std_sampled_json_dict):
            frame_data = self.std_sampled_json_dict[self.json_line_idx]
            # print(frame_data)  # 调试
            pose_list = frame_data["poses"]
            if len(pose_list) == 33 * 3:
                poses = np.array(pose_list).reshape(33, 3)
                self.std_points = [
                    (
                        max(0, min(win_width - 1, int(poses[landmark][0] * (win_width / original_std_size[0])))),
                        max(0, min(win_height - 1, int(poses[landmark][1] * (win_height / original_std_size[1]))))
                    )
                    for landmark in POSE_LANDMARKS.values()
                ]
            else:
                # 数据长度不对，跳过或做其他处理
                pass
        return self.std_points


    def get_realtime_points(self, sketList):
        """
        获取实时对齐点坐标。
        参数: sketList (list): 骨架检测结果列表。
        返回: self.realtime_points (list): 由 POSE_LANDMARKS字典 指定的实时对齐点坐标列表。
        """
        cam_width, cam_height = self.cap.get(3), self.cap.get(4)
        self.realtime_points = [
            (
                sketList[landmark][0] * (win_width / cam_width),
                sketList[landmark][1] * (win_height / cam_height)
            )
            if landmark < len(sketList) else (0, 0)
            for landmark in POSE_LANDMARKS.values()
        ]
        return self.realtime_points


    def get_std_overlay(self, std_overlay_idx=None):
        """
        获取标准掩膜帧 (overlay)。
        参数: std_overlay_idx (int): 标准掩膜帧的索引，若未传入，则使用默认的索引。
        返回: overlay: 读取和调整大小后的标准掩膜帧。
        """
        if std_overlay_idx is None:
            std_overlay_idx = self.std_overlay_idx
        # 检查索引范围
        if std_overlay_idx < 0 or std_overlay_idx >= len(self.std_sampled_masked_frames):
            print("错误：掩膜帧索引超出范围！")
            return None
        self.overlay = self.std_sampled_masked_frames[std_overlay_idx]
        return self.overlay


    def update_conditioning(self, std_points=None, realtime_points=None, distance_threshold=None):
        """
        只做条件判定，
        返回 1.bool值字典；2.整体bool值 
        （也内置修改self.condition字典值，main_loop写赋值是为了易读）
        """
        if not self.std_points or not self.realtime_points:
            all_points_matched = False
            for key in self.condition_dict.keys():
                self.condition_dict[key] = False
        else:
            all_points_matched = True
            # 遍历
            for key, (std, real) in zip(POSE_LANDMARKS.keys(), zip(std_points, realtime_points)):
                # 计算距离
                distance = np.linalg.norm(np.array(std) - np.array(real))

                if distance > distance_threshold:
                    self.condition_dict[key] = False
                    all_points_matched = False
                else:
                    self.condition_dict[key] = True

        return self.condition_dict, all_points_matched
    

    def idx_update(self, condition=False):
        """
        更新掩膜帧索引和标准点索引。
        参数: condition (bool): 条件是否满足。
        返回: json_line_idx (int): 当前标准点索引；std_overlay_idx (int): 当前掩膜帧索引。
        """
        if condition:
            if self.json_line_idx < len(self.std_sampled_json_dict) - 1:
                self.json_line_idx += 1
                self.std_overlay_idx += 1   # 掩膜帧索引+1，是指录入集的索引，不含原本json文件的索引值
            else:
                # todo:: 完成所有动作序列，跳转到...
                pass
        return self.json_line_idx, self.std_overlay_idx
    

    def get_sket_list(self, image, use_flip=False):
        """
        获取骨架列表。
        参数: image (ndarray): 输入图像；use_flip (bool): 是否翻转图像。
        返回: sketList (list): 骨架列表。
        """
        if use_flip:
            image = cv2.flip(image, 1)
        imageSket = self.pose_detector.findPose(image, draw=False)
        sketList, _ = self.pose_detector.findPosition(imageSket, draw=False)
        return sketList
    

    def main_loop(self):
        """主循环"""
        # 降低摄像头分辨率
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # self.cap.set(cv2.CAP_PROP_FPS, 15)  # 降低帧率

        while self.cap.isOpened():
            """相机采集帧"""
            # 读取实时帧
            success, image = self.cap.read()
            if not success:
                continue

            """骨架提取"""
            # 实时骨架检测
            image = cv2.flip(image, 1)

            # 实时骨架检测
            sketList = self.get_sket_list(image, use_flip=False)

            # todo:: 滤波

            """判定"""
            # 获取标准 LANDMARK 点坐标
            self.std_points = self.get_std_points()

            # 获取实时 LANDMARK 点坐标
            self.realtime_points = self.get_realtime_points(sketList)

            # self.condition布尔字典key对应 POSE_LANDMARKS 中的英文key名
            self.condition_dict, self.condition_overall = self.update_conditioning(self.std_points, self.realtime_points, self.distance_threshold)
            
            """更新"""
            # 更新掩膜索引、点索引
            self.json_line_idx, self.std_overlay_idx = self.idx_update(self.condition_overall)
            # self.json_line_idx, self.std_overlay_idx = self.idx_update(True)  # 调试
            # print(f"掩膜帧索引：{self.std_overlay_idx}")  # 调试
            # print(f"标准点帧索引：{self.json_line_idx}")  # 调试

            """绘制"""
            # 画布绘制左右翻转的实时画面，这里必须返回接收画布
            self.canvas = draw.draw_realtime_cap_only(self.canvas, image)

            # 根据掩膜索引获取标准掩膜帧
            # print(self.std_overlay_idx) # 调试
            self.overlay = self.get_std_overlay(self.std_overlay_idx)

            # 画布绘制标准掩膜帧
            draw.draw_overlay_on_canvas(self.canvas, self.overlay)

            # 画布绘制标准点和实时点，以及箭头
            draw.draw_points_with_arrow(self.canvas, self.std_points, self.realtime_points, self.condition_dict)

            """发送"""
            _, buffer = cv2.imencode('.jpg', self.canvas)
            sys.stdout.buffer.write(buffer)
            sys.stdout.flush()

            """显示"""
            # 显示合成画面
            window_name = "Realtime Guide"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.imshow(window_name, self.canvas)

            # 按键控制
            key = cv2.waitKey(1)
            if key == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    rp = RealtimePractice()
    rp.main_loop()
