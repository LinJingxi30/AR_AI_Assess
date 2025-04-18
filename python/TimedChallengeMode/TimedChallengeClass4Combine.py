import sys
from pathlib import Path
import mediapipe as mp

from anyio import sleep

MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(MEDIA_PIPE_ROOT))

import cv2
import numpy as np
from cvzone.PoseModule import PoseDetector
from Config.common_data import FPS, WIN_SIZE
from Config.paths import SPORTS_TYPE_PATH
from ProcessKit import Json2PreviewClass as j2pc
import time

from TimedChallengeMode import draw
from TimedChallengeMode.config import *
from TimedChallengeMode.fbsys import FeedbackSystem
from pygame.locals import *
from pygame import mixer

from Starter.SportSelector import get_sport_type
from ProcessKit import Draw

# 窗口参数
WIN_WIDTH, WIN_HEIGHT = WIN_SIZE
FRAME_RATE = 60


class TimedChallengeMode:
    def __init__(self, distance_threshold=50, sport_type="太极", challenge_time=60):
        self.sport_type = sport_type
        self.std_sampled_json_dir = None
        self.std_masked_frames_dir = None
        self.get_paths(sport_type=self.sport_type)

        self.std_sampled_json_dict = []
        self.std_sampled_masked_frames = []
        self.std_points = []
        self.realtime_points = []
        self.json_line_idx = 0      # 标准点
        self.std_overlay_idx = 0    # 掩膜
        self.overlay = None

        self.canvas = np.zeros((WIN_HEIGHT, WIN_WIDTH, 3), dtype=np.uint8)
        self.cap = cv2.VideoCapture(0)
        self.pose_detector = PoseDetector()
        self.mp_pose = mp.solutions.pose

        self.distance_threshold = distance_threshold
        self.condition_dict = {landmark: False for landmark in POSE_LANDMARKS.keys()}
        self.condition_overall = False

        # 初始化标准数据和摄像头
        self.load_std_data()
        self.cap_init()

        # 初始化中间变量
        self.running = True
        self.challenge_time = challenge_time
        self.match_score = 0.0
        self.final_score = 0.0
        self.pose_start_timing_flag = True
        self.pose_start_time = 0.0
        self.mode_clock = pygame.time.Clock()
        self.start_ticks = pygame.time.get_ticks()

        # 初始化 Pygame 窗口、音频、反馈系统
        self.screen = pygame.display.set_mode(WIN_SIZE, DOUBLEBUF | RESIZABLE)
        pygame.display.set_caption("Motion Coach Pro")
        # mixer.music.load("gameAssets/sounds/timed_bgm.mp3")
        mixer.music.load("gameAssets/sounds/SJTUbgm2.mp3")
        mixer.music.set_volume(0.8)
        mixer.music.play(-1)
        self.feedback_sys = FeedbackSystem()

    
    def get_paths(self, sport_type="太极"):
        """根据用户选择的运动选择路径"""
        if sport_type not in SPORTS_TYPE_PATH:
            print(f"未找到运动类型: {sport_type}，使用默认类型: 太极")
            sport_type = "太极"
        # 选择对应路径
        self.std_sampled_json_dir = SPORTS_TYPE_PATH[sport_type] / "sampled_std_frames.json"  # 抽样后的 JSON 文件路径
        self.std_masked_frames_dir = SPORTS_TYPE_PATH[sport_type] / "masked_sampled_std_frames"  # 抽样后、遮罩后帧保存路径

    
    def load_std_data(self):
        """加载标准数据"""
        # 加载标准采样数据 JSON 字典
        j2pc.get_json_frames(self.std_sampled_json_dict, self.std_sampled_json_dir)
        # print(self.std_sampled_json_dict)  # 调试
        # 加载标准采样掩膜帧
        for i in range(len(self.std_sampled_json_dict)):
            frame_idx = self.std_sampled_json_dict[i]["frame_idx"]
            frame_path = f"{self.std_masked_frames_dir}/masked_frame_{frame_idx:05d}.png"
            overlay = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
            if overlay is not None:
                overlay = cv2.resize(overlay, WIN_SIZE)
                self.std_sampled_masked_frames.append(overlay)
        # print(self.std_sampled_masked_frames)   # 调试
        # print(f"标准遮罩集长度{len(self.std_sampled_masked_frames)}")   # 调试


    def cap_init(self):
        """初始化摄像头"""
        if not self.cap.isOpened():
            print("错误：摄像头初始化失败！")
            return

    def display_pose_from_camera(self, image):
        with self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5) as pose:

            # cap = cv2.VideoCapture(0)
            # if not cap.isOpened():
            #     print("错误：摄像头初始化失败！")
            #     return
            #
            # while cap.isOpened():
            #     success, image = cap.read()
            #     if not success:
            #         break

                # 转换为RGB格式
                image = cv2.resize(image, WIN_SIZE)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = pose.process(image_rgb)

                # 创建全黑遮罩
                masked_image = np.zeros_like(image)

                if results.pose_landmarks:
                    h, w, _ = image.shape
                    print(h, w)
                    landmarks = results.pose_landmarks.landmark
                    # print(landmarks, "\n")
                    # print(type(landmarks))

                    # 获取所有关键点的坐标
                    xs = [lm.x * w for lm in landmarks]
                    ys = [lm.y * h for lm in landmarks]

                    # 计算边界框
                    x_min, x_max = int(min(xs)), int(max(xs))
                    y_min, y_max = int(min(ys)), int(max(ys))
                    print(x_min, y_min, x_max, y_max, file=sys.stderr)

                    # 添加边距（扩大一圈）
                    margin = 100  # 边距大小，可以根据需要调整
                    x_min = max(0, x_min - 20)
                    x_max = min(w, x_max + 20)
                    y_min = max(0, y_min - margin)
                    y_max = min(h, y_max + margin)

                    # 计算边界框的宽度和高度
                    bbox_width = x_max - x_min
                    bbox_height = y_max - y_min

                    # 计算画面中心坐标
                    center_x = w // 2
                    center_y = h // 2

                    # 计算新的边界框坐标（以画面中心为中心）
                    new_x_min = center_x - bbox_width // 2
                    new_x_max = center_x + bbox_width // 2
                    new_y_min = center_y - bbox_height // 2
                    new_y_max = center_y + bbox_height // 2

                    # 确保新的边界框不超出画面范围
                    new_x_min = max(0, new_x_min)
                    new_x_max = min(w, new_x_max)
                    new_y_min = max(0, new_y_min)
                    new_y_max = min(h, new_y_max)

                    # 将原始边界框区域复制到新的中心位置
                    bbox_content = image[y_min:y_max, x_min:x_max]
                    try:
                        # 调整大小以确保匹配目标区域
                        resized_bbox = cv2.resize(bbox_content, (new_x_max - new_x_min, new_y_max - new_y_min))
                        masked_image[new_y_min:new_y_max, new_x_min:new_x_max] = resized_bbox
                    except:
                        # 如果调整大小失败，使用原始内容
                        masked_image[new_y_min:new_y_max, new_x_min:new_x_max] = image[y_min:y_max, x_min:x_max]

                return masked_image
                # 显示结果（不再显示绿色边框）
            #     cv2.imshow('Centered Pose Detection', masked_image)
            #
            #     if cv2.waitKey(5) & 0xFF == ord('q'):
            #         break
            #
            # cap.release()
            # cv2.destroyAllWindows()

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
                        max(0, min(WIN_WIDTH - 1, int(poses[landmark][0]))),
                        max(0, min(WIN_HEIGHT - 1, int(poses[landmark][1])))
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
                sketList[landmark][0] * (WIN_WIDTH / cam_width),
                sketList[landmark][1] * (WIN_HEIGHT / cam_height)
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


    def update_conditioning(self, std_points=None, realtime_points=None, distance_threshold=50):
        """
        只做条件判定，
        返回 1.bool值字典；2.整体bool值 ；返回当前分数
        （也内置修改self.condition字典值，main_loop写赋值是为了易读）
        """
        total_distance = 0
        max_possible_distance = len(std_points) * distance_threshold
        if not std_points or not realtime_points:
            all_points_matched = False
            match_score = 0.0
            for key in self.condition_dict.keys():
                self.condition_dict[key] = False
        else:
            all_points_matched = True
            # 遍历
            for key, (std, real) in zip(POSE_LANDMARKS.keys(), zip(std_points, realtime_points)):
                # 计算距离
                distance = np.linalg.norm(np.array(std) - np.array(real))
                total_distance += distance
                # 判定
                if distance > distance_threshold:
                    self.condition_dict[key] = False
                    all_points_matched = False
                else:
                    self.condition_dict[key] = True
            match_score = 1.0 - (total_distance / max_possible_distance) if max_possible_distance > 0 else 1.0

        return self.condition_dict, all_points_matched, match_score
    

    def idx_update(self, condition=False):
        """
        更新掩膜帧索引和标准点索引。
        参数: condition (bool): 条件是否满足。
        返回: json_line_idx (int): 当前标准点索引；std_overlay_idx (int): 当前掩膜帧索引。
        """
        # 获取开始时刻
        if self.pose_start_timing_flag == True:
            self.pose_start_time = time.time()
            # 关闭重置时间标志位
            self.pose_start_timing_flag = False

        if time.time() - self.pose_start_time > 3.0:    # 花费时间大于3秒
            condition = 0.5

        if condition > 0.3:
            # 计算到达目标花费的时间
            time_period = time.time() - self.pose_start_time

            # 判分
            if time_period < 1.5:
                self.feedback_sys.add_feedback("perfect", 10)
            elif time_period < 2.5:
                self.feedback_sys.add_feedback("great", 5)
            else:
                self.feedback_sys.add_feedback("good", 3)
            
            # 开启重置时间标志位
            self.pose_start_timing_flag = True
            
            # 更新帧索引
            if self.json_line_idx < len(self.std_sampled_json_dict) - 1:
                self.json_line_idx += 1
                self.std_overlay_idx += 1   # 掩膜帧索引+1，是指录入集的索引，不含原本json文件的索引值
                print(f"跳转到第 {self.json_line_idx} 帧")
            else:
                # todo:: 完成所有动作序列，跳转到...
                # pass
                self.running = False
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
    
    def process_pose(self, image, use_flip=False):
        """
        使用 MediaPipe 提取关节点和轮廓信息。
        参数:
            image (ndarray): 输入图像。
            use_flip (bool): 是否翻转图像。
        返回:
            sketList (list): 骨架关节点列表。
            masked_image (ndarray): 包含轮廓的遮罩图像。
        """
        if use_flip:
            image = cv2.flip(image, 1)

        # 转换为 RGB 格式
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 使用 MediaPipe Pose 模块
        with self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5) as pose:
            results = pose.process(image_rgb)

            # 初始化骨架关节点列表和遮罩图像
            sketList = []
            masked_image = np.zeros_like(image)

            if results.pose_landmarks:
                h, w, _ = image.shape
                landmarks = results.pose_landmarks.landmark

                # 提取关节点坐标
                sketList = [
                    (int(lm.x * w), int(lm.y * h)) for lm in landmarks
                ]

                # 提取轮廓信息
                xs = [lm.x * w for lm in landmarks]
                ys = [lm.y * h for lm in landmarks]

                # 计算边界框
                x_min, x_max = int(min(xs)), int(max(xs))
                y_min, y_max = int(min(ys)), int(max(ys))

                # 添加边距（扩大一圈）
                margin = 100
                x_min = max(0, x_min - 20)
                x_max = min(w, x_max + 20)
                y_min = max(0, y_min - margin)
                y_max = min(h, y_max + margin)

                # 计算边界框的宽度和高度
                bbox_width = x_max - x_min
                bbox_height = y_max - y_min

                # 计算画面中心坐标
                center_x = w // 2
                center_y = h // 2

                # 计算新的边界框坐标（以画面中心为中心）
                new_x_min = center_x - bbox_width // 2
                new_x_max = center_x + bbox_width // 2
                new_y_min = center_y - bbox_height // 2
                new_y_max = center_y + bbox_height // 2

                # 确保新的边界框不超出画面范围
                new_x_min = max(0, new_x_min)
                new_x_max = min(w, new_x_max)
                new_y_min = max(0, new_y_min)
                new_y_max = min(h, new_y_max)

                # 将原始边界框区域复制到新的中心位置
                bbox_content = image[y_min:y_max, x_min:x_max]
                try:
                    resized_bbox = cv2.resize(bbox_content, (new_x_max - new_x_min, new_y_max - new_y_min))
                    masked_image[new_y_min:new_y_max, new_x_min:new_x_max] = resized_bbox
                except:
                    masked_image[new_y_min:new_y_max, new_x_min:new_x_max] = image[y_min:y_max, x_min:x_max]

            return sketList, masked_image


    def main_update(self):
        if self.running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    self.running = False

            # 计算剩余时间
            current_ticks = pygame.time.get_ticks()
            elapsed_seconds = (current_ticks - self.start_ticks) // 1000
            remaining_time = max(0, self.challenge_time - elapsed_seconds)
            if remaining_time == 0:
                self.running = False

            """相机采集帧"""
            # 读取实时帧
            success, image = self.cap.read()
            if not success:
                return

            """骨架提取和轮廓生成"""
            sketList, masked_image = self.process_pose(image, use_flip=True)

            """判定"""
            # 获取标准 LANDMARK 点坐标
            self.std_points = self.get_std_points()

            # 获取实时 LANDMARK 点坐标
            self.realtime_points = self.get_realtime_points(sketList)

            # self.condition布尔字典key对应 POSE_LANDMARKS 中的英文key名
            self.condition_dict, self.condition_overall, self.match_score = self.update_conditioning(
                self.std_points, self.realtime_points, self.distance_threshold
            )

            """更新"""
            # 更新掩膜索引、点索引
            self.json_line_idx, self.std_overlay_idx = self.idx_update(condition=self.match_score)

            """绘制"""
            # 画布绘制左右翻转的实时画面
            self.canvas = draw.draw_realtime_cap_only(self.canvas, masked_image)

            # 根据掩膜索引获取标准掩膜帧
            self.overlay = self.get_std_overlay(self.std_overlay_idx)

            # 画布绘制标准掩膜帧
            draw.draw_overlay_on_canvas(self.canvas, self.overlay)

            # 画布绘制标准点和实时点，以及箭头
            draw.draw_points_with_arrow(self.canvas, self.std_points, self.realtime_points, self.condition_dict)

            """显示"""
            # 转换到 Pygame 显示
            canvas_rgb = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2RGB)
            pygame_surface = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0, 1))
            self.screen.blit(pygame_surface, (0, 0))

            # 绘制界面元素
            title_surf = FONT_CONFIG["title"].render("TaiChi Practice", True, (255, 255, 255))
            title_rect = title_surf.get_rect(center=(WIN_WIDTH // 2, 30))
            self.screen.blit(title_surf, title_rect)

            time_text = FONT_CONFIG["score"].render(f"MOVE {self.std_overlay_idx}", True, (255, 215, 0))
            time_rect = time_text.get_rect(topright=(WIN_WIDTH - 20, 20))
            self.screen.blit(time_text, time_rect)

            # 更新反馈系统
            self.feedback_sys.update_feedbacks()
            self.feedback_sys.draw_feedbacks(self.screen)
            self.feedback_sys.draw_score(self.screen)

            # 刷新显示
            pygame.display.flip()
            self.mode_clock.tick(FRAME_RATE)
            surface = pygame.transform.scale(self.screen, (WIN_WIDTH, WIN_HEIGHT))
            arr = pygame.surfarray.array3d(surface)
            arr = np.swapaxes(arr, 0, 1)

            return arr


if __name__ == "__main__":
    """运动种类选择，内含发送"""
    sport = get_sport_type(sport_str = ["TaiChi", "Aerobics", "Yoga"])
    sport = "太极"  # 临时

    mode = TimedChallengeMode(sport_type=sport, challenge_time=60000000)

    cnt = 1
    while mode.running:
        frame = mode.main_update()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        """发送"""
        # 降低帧率 1/2
        # if cnt == 2:
        #     cnt = 1
        #     continue
        # cnt += 1
        
        # 所有cv2.imencode调用增加压缩参数
        _, buffer = cv2.imencode('.jpg', frame, [
            int(cv2.IMWRITE_JPEG_QUALITY), 75,  # 质量系数
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1    # 启用Huffman优化
        ])
        sys.stdout.buffer.write(buffer.tobytes())
        sys.stdout.flush()

    final_score = mode.feedback_sys.total_score
    print_green_text = lambda text: print(f"\033[92m{text}\033[0m", file=sys.stderr)
    print_green_text(f"限时挑战模式 总得分：{final_score}")
    # 清理资源
    mode.cap.release()
    mixer.music.stop()
    pygame.quit()

    """结算"""
    clock = pygame.time.Clock()
    while True:
        frame = Draw.draw_game_over(score=final_score)
        """发送三"""
        _, buffer = cv2.imencode('.jpg', frame, [
            int(cv2.IMWRITE_JPEG_QUALITY), 75,  # 质量系数
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1  # 启用Huffman优化
        ])
        sys.stdout.buffer.write(buffer.tobytes())
        sys.stdout.flush()

        cv2.imshow("Game Over", frame)
        if cv2.waitKey(50) & 0xFF == 27:
            break
        clock.tick(1)   # 1fps
    cv2.destroyAllWindows()
        
