# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/4/29 21:12
# @Content :
from functools import lru_cache
import json
import time
import sys
from pathlib import Path
import cv2
import pygame
import mediapipe as mp
import numpy as np

PY_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PY_ROOT))   # 添加 Python 根目录到模块搜索路径中
from TaiJiGuiderSJTU import draw
from Config import WIN_SIZE, STD_SPORTS_RESULTS_ROOT
from utils.DataSender import DataSender

"""
备注：
标准对齐关节点（4个点）获取流程：（在 self.canvas_render() 函数内实现）

- 先获取完整姿态列表 std_pose_list（33个点）
    1. JSON 每行代表1帧 -> 1帧标准姿态列表[33 * (x, y, z=0)] -> 所有帧标准姿态列表 [[33 * (x, y, z=0)], [...], ...] 内含一个视频的所有帧的标准姿态列表
    2. 1帧姿态列表叫 std_pose_list； 所有帧姿态列表叫 std_pose_lists
    3. 循环之前预加载完的是 std_pose_lists，每次进入循环获取的是 std_pose_list = std_pose_lists[current_std_index]
    4. std_pose_list[0] 是标点中心点，std_pose_list[1] 是左指尖，std_pose_list[2] 是右指尖，std_pose_list[3] 是左脚尖，std_pose_list[4] 是右脚尖

- 再获取标准对齐点列表 std_landmarks_list（4个点）
    由于完整标准姿态列表格式与实时的一致，
    所以可以直接使用 get_landmarks_list(std_pose_list, landmarks=POSE_ALIGN_LANDMARKS) 获取标准对齐点列表 std_landmarks_list
"""


WIN_WIDTH, WIN_HEIGHT = WIN_SIZE

POSE_ALIGN_LANDMARKS = [19, 20, 31, 32]  # 左指尖、右指尖、左脚尖、右脚尖
PTS_CONDITION_THRESH = [125, 125, 250, 250] # 对应上面的 4 个点的判定阈值
RT_PTS_TO_CENTER = [11, 12, 23, 24]  # 左肩、右肩、左髋、右髋

LIGHTNESS = 0.6  # 画布亮度调整系数
STD_SCALE = 0.45  # 标准对齐点/掩膜缩放系数
STD_CENTER_Y_OFFSET = -120   # 标准中心相对实时中心降低高度（像素）
STD_OVERLAY_OPACITY = 0.6  # 掩膜透明度

MAX_SCORE = 100  # 最大分数

PYGAME_UI_CONFIG = {
    "标题": {
        "文字": "太极引导助手🥋",
        "字体": str(Path(PY_ROOT) / "gameAssets" / "fonts" / "SmileySans-Oblique.ttf"),
        "字号": 60,
        "颜色": (100, 155, 255),  # RGB(100, 155, 255)
        "位置": (180, 60),
    },
    "计分": {
        "文字": "当前积分：",
        "字体": str(Path(PY_ROOT) / "gameAssets" / "fonts" / "SmileySans-Oblique.ttf"),
        "字号": 40,
        "颜色": (255, 215, 255),  # RGB(255, 215, 255) 
        "位置": (WIN_WIDTH - 160, 60),
    },
}

PATHS = {
    "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "C79-V2.1_points.json",
    "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "masked_sampled_std_frames",
    "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
}


class Guider:
    def __init__(self, paths=PATHS):
        # config 配置
        win_topic = "AR太极拳助手"
        self.frame_rate = 60

        # path 路径
        self.std_json_path = paths["标准 JSON 文件路径"]
        self.std_frame_path = paths["标准掩膜图片路径"]
        win_bgm_path = paths["背景音乐"]

        # utils 工具
        self.camera = None
        self.pose_detector = None
        self.frame_rate_clock = None

        # resource 资源
        self.std_pose_lists = None
        self.std_overlay_paths = None
        self.real_world_frame = None
        self.rt_pose_list = None
        self.std_pose_list = None
        self.rt_landmarks_list = None
        self.std_landmarks_list = None
        self.rt_center = None
        self.std_center = None
        self.std_overlay = None
        self.canvas = None  # cv2 画布
        self.pygame_surface = None  # pygame 画布
        self.screen = None  # pygame 窗口

        # init 初始化工具
        self.camera_init(resolution=(1280, 720))
        self.pose_detector_init()
        self.pygame_init(win_topic=win_topic, win_bgm_path=str(win_bgm_path))

        # load 初始化加载资源
        self.std_pose_lists, self.std_overlay_paths = self.load_std_resources(self.std_json_path, self.std_frame_path)

        # state 状态
        self.current_std_index = 0
        self.timer = None
        self.conditions = [False] * len(POSE_ALIGN_LANDMARKS)
        self.score = 0
        self.running = True

    def main_loop(self):
        while self.running:
            # 渲染 .screen
            self.main_update()
            # 获取 JPEG 字节数据
            frame_to_web = self.get_transmit_frame(self.screen)
            # 发送 JPEG 数据
            self.send_jpeg_data(frame_to_web)
            # 更新窗口显示
            pygame.display.flip()
        self.camera.release()

    def main_update(self, frame=None):
        # 可以从外部传实时帧
        if self.running:

            """处理 Pygame 窗口事件"""
            self.window_events()

            """帧率控制"""
            self.frame_rate_clock.tick(self.frame_rate)

            """获取实时画面帧"""
            if frame is None:
                # 外部未传帧
                self.real_world_frame = self.camera_capture(camera=self.camera)  # 拍摄实时画面，已经拉伸到窗口大小并左右翻转
            else:
                # 外部传帧
                self.real_world_frame = self.camera_capture(frame=frame)    # 拉伸到窗口大小并左右翻转
            # 检查实时帧是否获取成功
            if self.real_world_frame is None:
                return None
            
            """主画布渲染"""
            # 获取对齐点列表 std_landmarks_list 和 rt_landmarks_list；
            # 渲染标点、箭头、掩膜到画布
            self.canvas_render(rt_frame=self.real_world_frame, 
                               conditions=self.conditions)

            """条件判定"""
            # 检查条件是否满足，更新 condition 列表
            self.condition_check(conditions=self.conditions, 
                                 landmarks=POSE_ALIGN_LANDMARKS,
                                 thresholds=PTS_CONDITION_THRESH, 
                                 std_lm_list=self.std_landmarks_list, 
                                 rt_lm_list=self.rt_landmarks_list)
            
            """步进跳帧"""
            # self.conditions = [True] * len(POSE_ALIGN_LANDMARKS)  # 调试
            self.current_std_index = self.index_update(conditions=self.conditions, 
                                                       cur_index=self.current_std_index, 
                                                       end_index=len(self.std_pose_lists))
            
            """分数统计"""
            self.score = self.single_posture_score_calc(max_tot_score=MAX_SCORE,
                                                        tot_score=self.score,
                                                        conditions=self.conditions,
                                                        time_range=(1, 8))    # 调整时间范围以调整判分宽松度（最佳，最差）

            """绘制 Pygame UI"""
            # 绘制已用时间、招式、实时总得分
            self.pygame_UI_render(canvas=self.canvas, CONFIGS=PYGAME_UI_CONFIG)

        return self.screen

    @staticmethod
    def get_transmit_frame(surface: pygame.Surface) -> bytes:
        """
        将 Pygame 窗口转换为可发送格式
        """
        # 将 Pygame Surface 转换为 NumPy 数组，形状（w, h, c=3）
        frame = pygame.surfarray.array3d(surface)

        # 改变形状（交换轴）得到（h, w, c=3）
        frame = np.transpose(frame, (1, 0, 2))

        # 转换为 BGR 格式
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # 使用 JPEG 压缩
        _, buffer = cv2.imencode('.jpg', frame, [
            cv2.IMWRITE_JPEG_QUALITY, 90,   # 压缩质量
            cv2.IMWRITE_JPEG_OPTIMIZE, 1,  # 霍夫曼优化
        ])

        # 转换为字节流
        jpeg_data = buffer.tobytes()

        return jpeg_data


    def pygame_UI_render(self, canvas, CONFIGS):
        """
        绘制 Pygame UI
        """
        # 源：BGR 格式的 cv2 画布
        # 转换为 RGB 格式
        canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        # 转换为 Pygame Surface 格式
        self.pygame_surface = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0, 1))
        # 绘制到 Pygame 窗口
        self.screen.blit(self.pygame_surface, (0, 0))

        # 绘制标题
        TITLE = CONFIGS["标题"]
        # 加载字体并设置字号
        font = pygame.font.Font(TITLE["字体"], TITLE["字号"])
        title_surface = font.render(TITLE["文字"], True, TITLE["颜色"])
        title_rect = title_surface.get_rect(center=TITLE["位置"])
        self.screen.blit(title_surface, title_rect)

        # 绘制计分
        SCORE = CONFIGS["计分"]
        font = pygame.font.Font(SCORE["字体"], SCORE["字号"])
        score_surface = font.render(f"{SCORE['文字']}{int(self.score)}分", True, SCORE["颜色"])
        score_rect = score_surface.get_rect(center=SCORE["位置"])
        self.screen.blit(score_surface, score_rect)


    
    def single_posture_score_calc(self, max_tot_score, tot_score, conditions, time_range):
        """
        针对 “一式” 的时间基准的分数计算
        """
        # 获取本次达成条件所用时间
        time_used = self.get_time_used(conditions)

        if time_used is not None:
            # 计算每帧分数上限（总分 / 标准帧数）
            if self.std_pose_lists:
                per_max_score = max_tot_score / len(self.std_pose_lists)
            else:
                per_max_score = 1  # 防止除零

            # 得到当前帧分数范围
            cur_score_range = (0, per_max_score)

            # 计算当前帧分数
            cur_score = self.single_frame_score_calc(time_used, cur_score_range, time_range)
            
            # 更新总分
            tot_score += cur_score

            # 限制总分不超过上限
            if tot_score > max_tot_score:
                tot_score = max_tot_score

        return tot_score

    def get_time_used(self, conditions):
        """
        获取当前条件满足所用时间
        """
        if all(conditions):
            if self.timer is not None:
                # 结束计时
                time_used = time.time() - self.timer
                # 只有在满足条件时才重置计时器
                self.timer = None
                # 返回所花时间
                return time_used
            else:
                # 一开始就满足条件，所花时间为 0s
                return 0
        else:
            if self.timer is None:
                # 开始时刻
                self.timer = time.time()
            return None

    @staticmethod
    def single_frame_score_calc(time_used, cur_score_range, time_range):
        """
        每帧得分计算：根据用时计算分数，时间越短分数越高
        """
        min_score, max_score = cur_score_range
        best_time, worst_time = time_range

        # 不能取等，0s 直接满分
        if time_used < 0:
            return 0
        # 时间上下限，大于w直接按w算分，小于b直接按b算分
        if time_used <= best_time:
            return max_score
        elif time_used >= worst_time:
            return min_score
        else:
            # 将分数归一化到 [min_score, max_score]
            # 所花时间越少，分数越高
            return max_score - (max_score - min_score) * ((time_used - best_time) / (worst_time - best_time))

    @staticmethod
    def index_update(conditions, cur_index, end_index):
        """
        根据条件，步进跳帧
        """
        if cur_index < end_index - 1:
            if all(conditions):
                # 如果所有条件都满足，跳到下一帧
                cur_index += 1
                # elif 三秒
        else:
            cur_index = 0  # 循环播放
        
        return cur_index
    
    @staticmethod
    def condition_check(conditions, landmarks, thresholds, std_lm_list, rt_lm_list):
        """
        检查条件是否满足，更新 condition 列表
        """
        if not std_lm_list or not rt_lm_list:
            # 如果没有标准或实时数据，条件不满足
            conditions[:] = [False] * len(landmarks)
            return
        
        for idx, (std_pt, rt_pt) in enumerate(zip(std_lm_list, rt_lm_list)):
            # 计算距离
            distance = np.linalg.norm(np.array(std_pt) - np.array(rt_pt))
            
            # 更新条件列表
            if distance < thresholds[idx]:
                # 满足距离小于阈值条件
                conditions[idx] = True
            else:
                # 不满足也一样要更新
                conditions[idx] = False

    def canvas_render(self, rt_frame, conditions):
        """绘制实时画面帧"""
        self.canvas = rt_frame.copy()  # 复制实时画面帧到画布

        """标准对齐点加载"""
        if self.current_std_index >= len(self.std_pose_lists):
            # todo:: 这里可以添加循环播放的逻辑；结束逻辑
            pass
        
        self.std_pose_list = self.std_pose_lists[self.current_std_index]  # 标准完整姿态列表，从 lists 中获取 list，格式同上
        self.std_landmarks_list = self.get_landmarks_list(self.std_pose_list, landmarks=POSE_ALIGN_LANDMARKS)   # 标准关键（对齐）点列表，格式同上
        self.std_overlay = self.get_current_std_overlay(paths=self.std_overlay_paths, overlay_idx=self.current_std_index)  # 标准帧路径，格式为 str

        """实时对齐点获取"""
        self.rt_pose_list = self.pose_detection(self.real_world_frame)   # 实时完整姿态列表，格式为： [33 * tuple(x, y, z=0)] 或 []
        self.rt_landmarks_list = self.get_landmarks_list(self.rt_pose_list, landmarks=POSE_ALIGN_LANDMARKS) # 实时关键（对齐）点列表，格式为： [4 * int(x, y)] 或 []

        """获取实时躯干位置；获取标准中心标点"""
        self.rt_center = self.get_center_from_points_2d(self.rt_pose_list, from_pts_idx=RT_PTS_TO_CENTER, win_size=WIN_SIZE, y_offset=STD_CENTER_Y_OFFSET)  # tuple(float, float)
        # self.rt_center = (self.rt_center[0], self.rt_center[1] + BENEATH)   # 参数调整中心点位置，向下偏移 BENEATH 像素
        self.std_center = (self.std_pose_list[0][0] * STD_SCALE, self.std_pose_list[0][1] * STD_SCALE)  # std_pose_list 的第一个元组是标点中心点 (3d to 2d)

        """将标准对齐点吸附到用户"""
        self.align_pose_to_target_by_center_2d(self.std_landmarks_list, center=self.std_center, target=self.rt_center, scale=STD_SCALE)
        # print(self.std_landmarks_list) # 调试

        """叠加掩膜到画布"""
        self.canvas = (self.canvas * LIGHTNESS).astype(np.uint8)  # 调整画布亮度
        self.canvas = draw.draw_overlay_centered(self.canvas, self.std_overlay, 
                                                    center=self.std_center, target=self.rt_center, 
                                                    win_size=WIN_SIZE, 
                                                    scale=STD_SCALE, 
                                                    opacity=STD_OVERLAY_OPACITY)  # 在画布上叠加掩膜，掩膜中心点与用户中心点对齐

        """绘制 对齐点 + 箭头 到画布"""
        self.canvas = draw.draw_points_and_arrows(self.canvas, 
                                                  self.std_landmarks_list, 
                                                  self.rt_landmarks_list, 
                                                  conditions)
        
        # 调试：绘制较大的实时中心点（橙色）
        # cv2.circle(self.canvas, (int(self.rt_center[0]), int(self.rt_center[1])), 15, (0, 165, 255), -1)

    def window_events(self):
        """
        窗口事件：
        退出：Esc
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                self.running = False

    def camera_init(self, resolution=(1280, 720)):
        """
        初始化摄像头
        """
        # 获取摄像头 0
        self.camera = cv2.VideoCapture(0)
        
        # 尝试设置分辨率
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        # 检查分辨率设置是否成功（分辨率不是随意取值，必须按照使用相机的几个固定的分辨率进行选择）
        w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if w != resolution[0] or h != resolution[1]:
            print(f"摄像头分辨率设置失败，当前分辨率：{w}x{h}", file=sys.stderr)

        # 检查摄像头是否打开
        if not self.camera.isOpened():
            raise RuntimeError("摄像头初始化失败")

    def pose_detector_init(self):
        """
        初始化姿势检测模型
        """
        self.pose_detector = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def pygame_init(self, win_bgm_path, win_topic):
        """
        初始化 Pygame
        窗口、音频、反馈系统
        """
        # 初始化 pygame 及混音器
        pygame.init()
        pygame.mixer.init()

        # 加载背景音乐 bgm
        pygame.mixer.music.load(win_bgm_path)
        pygame.mixer.music.set_volume(1)        # 音量范围 0.0 - 1.0
        pygame.mixer.music.play(-1)             # -1 表示循环播放

        # 初始化窗口
        self.screen = pygame.display.set_mode(WIN_SIZE)
        pygame.display.set_caption(win_topic)   # 窗口标题
        # pygame.display.set_icon(pygame.image.load("gameAssets/images/icon.png"))    # 窗口图标

        # 初始化时钟
        self.frame_rate_clock = pygame.time.Clock()

        # 初始化反馈系统
        # self.feedback_sys = FeedbackSystem()

    def pose_detection(self, frame_bgr) -> list[tuple]:
        """
        使用 self.pose_detector 进行姿态检测，返回1帧完整姿态列表
        self.pose_detector 使用的是 Mediapipe 的 Pose 模型
        """
        # 转为 RGB 格式以便 Mediapipe 处理
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Mediapipe 进行检测
        results = self.pose_detector.process(frame_rgb)

        # 生成格式化的姿态列表
        pose_list = []
        if results.pose_landmarks:
            # 提取关键点坐标（lm.x, lm.y）为归一化结果∈[0, 1]，需要乘以图像宽高
            h, w = frame_bgr.shape[:2]
            # 归一化坐标转换为实际坐标，忽略 z 轴（其因子是肩宽）
            pose_list = [(lm.x * w, lm.y * h, 0) for lm in results.pose_landmarks.landmark]
        
        # 返回 [33 * tuple(x, y, z=0)] 或 []
        return pose_list

    @staticmethod
    def get_landmarks_list(full_pose_list, landmarks=None) -> list[tuple]:
        """
        完整姿态列表 -> 关键点坐标列表
        """
        if not full_pose_list or not landmarks:
            return []
        
        landmarks_list = []
        # 获取关键（对齐）点坐标列表
        if full_pose_list:
            landmarks_list = [
                (full_pose_list[lm][0], full_pose_list[lm][1])
                # 遍历列表 POSE_ALIGN_LANDMARKS 中的存储的关键点索引，存储对应完整列表里的坐标
                for lm in landmarks if lm < len(full_pose_list)
            ]

        # [4 * int(x, y)]
        return landmarks_list

    def load_std_resources(self, json_path, frame_path) -> tuple[list[list[tuple]], list[str]]:
        """
        加载标准资源
        """
        # 加载标准 JSON 数据 -> 标准姿态合集列表
        # [[33 * tuple(x, y, z=0)], [...], ..., ]
        std_pose_lists = self.load_std_pose_lists(json_path, landmarks=POSE_ALIGN_LANDMARKS)
        
        # 标准帧路径合集列表
        # [str(path), str, ...]
        std_overlay_paths = self.load_std_frame_paths(frame_path)

        # 标准姿态 列表列表；标准帧路径 列表
        return std_pose_lists, std_overlay_paths

    # todo:: 存疑：我现在不管 std_pose_lists 是在哪个分辨率下得到的，而统一到最后再进行缩放
    def load_std_pose_lists(self, json_path, landmarks=None) -> list[list[tuple]]:
        # 嵌套列表 [[33 * tuple(x, y, z=0)], ..., ] len(json)
        std_full_pose_lists = []
        # 只读模式打开 JSON 文件
        with open(json_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    break

                # 一帧 <- 一行
                frame_dict = json.loads(line)

                # 读取这一帧（行）的标准姿态列表 [33 * tuple(x, y, z=0)]
                LAST_IDX = 32  # 33 个点，索引从 0 开始
                pose_list = [
                    # 先放标点中心
                    (
                        frame_dict["points"]["center"][0],
                        frame_dict["points"]["center"][1],
                        0
                    ),
                    # 用 * 解包 len 个 (0, 0, 0)
                    *((0, 0, 0) for _ in range(landmarks[0]-1)),
                    (
                        frame_dict["points"]["left_h"][0],
                        frame_dict["points"]["left_h"][1],
                        0
                    ),  # poes_list[i] 是第 i+1 个，前有 i 个 (0, 0, 0)
                    *((0, 0, 0) for _ in range(landmarks[1]-landmarks[0]-1)),
                    (
                        frame_dict["points"]["right_h"][0],
                        frame_dict["points"]["right_h"][1],
                        0
                    ),  # 索引对应
                    *((0, 0, 0) for _ in range(landmarks[2]-landmarks[1]-1)),
                    (
                        frame_dict["points"]["left_f"][0],
                        frame_dict["points"]["left_f"][1],
                        0
                    ),  # 索引对应
                    *((0, 0, 0) for _ in range(landmarks[3]-landmarks[2]-1)),
                    (
                        frame_dict["points"]["right_f"][0],
                        frame_dict["points"]["right_f"][1],
                        0
                    ),  # 索引对应
                    *((0, 0, 0) for _ in range(LAST_IDX-landmarks[3]-1)),
                ]

                # 存储到嵌套列表中
                std_full_pose_lists.append(pose_list)

        # [[33 * tuple(x, y, z=0)], ..., ] len(json)
        return std_full_pose_lists

    @staticmethod
    def load_std_frame_paths(frame_path) -> list[str]:

        # 存储目录下的所有 PNG 文件路径，按名称排序，转为字符串（ pathlib 写法）
        frame_paths_list = [str(p) for p in sorted(Path(frame_path).glob("*.png"))]

        # list[Path] -> list[str]
        return frame_paths_list

    @staticmethod
    def camera_capture(camera=None, frame=None) -> None | cv2.Mat | np.ndarray:
        """
        获取并处理现实实时画面，赋值到 self.real_world_frame
        """
        # 获取实时帧
        if frame is None:
            # 外部无统一传帧，从相机获取
            if camera is not None:
                success, frame = camera.read()
                if not success:
                    print("获取实时画面失败：实时帧读取不成功", file=sys.stderr)
                    return None
            else:
                print("获取实时画面失败：相机为空", file=sys.stderr)
                return None
        else:
            # 外部统一传帧
            pass

        # 左右翻转画面，存储实时帧资源
        real_world_frame = cv2.flip(frame, 1)

        # 将画面拉伸到窗口大小，！后续都基于这个分辨率！
        real_world_frame = cv2.resize(real_world_frame, (WIN_WIDTH, WIN_HEIGHT))

        return real_world_frame

    @staticmethod
    def get_center_from_points_2d(full_pose_list, from_pts_idx, win_size, y_offset) -> tuple[float, float]:
        # 默认中心点为窗口中心
        if not from_pts_idx or not full_pose_list:
            return win_size[0] / 2, win_size[1] / 2
        
        # 计算指定点的平均值作为中心点
        x_sum = sum(full_pose_list[idx][0] for idx in from_pts_idx)
        y_sum = sum(full_pose_list[idx][1] for idx in from_pts_idx)

        center_x = x_sum / len(from_pts_idx)
        center_y = y_sum / len(from_pts_idx) - y_offset

        center_2d = (center_x, center_y)

        # 存疑
        # if center_x < 0 or center_y < 0 or center_x > win_size[0] or center_y > win_size[1]:
        #     # 如果中心点超出窗口范围，则返回窗口中心
        #     center_2d = (win_size[0] / 2, win_size[1] / 2)

        return center_2d

    def get_current_std_overlay(self, paths, overlay_idx):
        if overlay_idx < 0 or overlay_idx >= len(paths):
            raise IndexError("错误：掩膜索引超出范围！")
        return self._load_std_overlay(paths[overlay_idx])
        
    @lru_cache(maxsize=10)
    def _load_std_overlay(self, path):
        """
        内部缓存最近 10 帧的掩膜图像
        """
        overlay = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        
        if overlay is None:
            raise FileNotFoundError(f"错误：无法缓存掩膜图像 {path}，找不到文件！")
        
        return overlay

    @staticmethod
    def align_pose_to_target_by_center_2d(std_landmarks_list, center, target, scale=1.0):
        """
        将标准对齐点列表 std_landmarks_list 根据中心点 center，吸附到目标点 target 上
        """
        if not std_landmarks_list:
            return
        if not target:
            # todo:: 这里没能保持传参
            target = (WIN_WIDTH // 2, WIN_HEIGHT // 2)

        if not center:
            # todo::自行计算中心点
            # center = self.get_center_from_points_2d(std_landmarks_list, from_pts_idx=POSE_ALIGN_LANDMARKS, win_size=WIN_SIZE)
            return
        
        # 计算偏移量
        offset_x = target[0] - center[0]
        offset_y = target[1] - center[1]

        # 对每个坐标点进行偏移，直接修改 std_landmarks_list
        for i in range(len(std_landmarks_list)):
            # 元组无法直接修改，所以需要先转换为列表
            x, y = std_landmarks_list[i]
            # 平移之前先缩放
            x *= scale
            y *= scale
            # 进行平移
            std_landmarks_list[i] = (x + offset_x, y + offset_y)

        # return std_landmarks_list

    @staticmethod
    def send_jpeg_data(data):
        """
        发送 JPEG 数据：打印在标准输出流
        """
        DataSender.send_frame(data)


# @A last new line here:

if __name__ == "__main__":
    
    # 创建 Guider 实例
    TaiJiGuider = Guider()
    DataSender.send_control("PLAY_AUDIO",flag = 1)
    # 开始运行
    TaiJiGuider.running = True
    # 渲染循环
    while TaiJiGuider.running:
        # 渲染 .screen
        TaiJiGuider.main_update()
        # 获取 JPEG 字节数据
        frame_to_web = TaiJiGuider.get_transmit_frame(TaiJiGuider.screen)
        # 发送 JPEG 数据
        TaiJiGuider.send_jpeg_data(frame_to_web)
        # 更新窗口显示
        pygame.display.flip()
    # 清理资源
    TaiJiGuider.camera.release()
    pygame.quit()