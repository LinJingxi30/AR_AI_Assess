import sys
from pathlib import Path
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(MEDIA_PIPE_ROOT))

import cv2
import numpy as np
from cvzone.PoseModule import PoseDetector
from Config.common_data import FPS, WIN_SIZE
from Config.paths import SPORTS_TYPE_PATH
from ProcessKit import Draw, Json2PreviewClass as j2pc
import time

from EndlessChallengeMode import draw
from EndlessChallengeMode.config import *
from EndlessChallengeMode.fbsys import FeedbackSystem
from pygame.locals import *
from pygame import mixer

from Starter.SportSelector import get_sport_type


# 窗口参数
WIN_WIDTH, WIN_HEIGHT = WIN_SIZE
FRAME_RATE = 60


class EndlessChallengeMode:
    def __init__(self, distance_threshold=50, sport_type="太极", round_duration=TIMER_CONFIG["round_duration"]):
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

        self.distance_threshold = distance_threshold
        self.condition_dict = {landmark: False for landmark in POSE_LANDMARKS.keys()}
        self.condition_overall = False

        # 初始化标准数据和摄像头
        self.load_std_data()
        self.cap_init()

        # 初始化中间变量
        self.running = True
        self.player_HP = TIMER_CONFIG["max_lives"]
        self.match_score = 0.0
        self.final_score = 0.0
        self.pose_start_timing_flag = True
        self.pose_start_time = 0.0
        self.mode_clock = pygame.time.Clock()
        self.round_duration = round_duration
        self.round_start_time = time.time()
        self.round_elapsed_time = 0.0   # 回合已走时间（仅为整齐，可以求差得出，不用定义类成员）
        self.round_remaining_time = self.round_duration # TIMER_CONFIG["round_duration"]  # 初始化为默认回合时长
        self.lastround_ended_flag = False

        # 初始化 Pygame 变量： 窗口、音频、反馈系统
        self.screen = pygame.display.set_mode(WIN_SIZE, DOUBLEBUF | RESIZABLE)
        
        pygame.display.set_caption("Motion Coach Pro")
        mixer.music.load("gameAssets/sounds/timed_bgm.mp3")
        mixer.music.set_volume(0.3)
        mixer.music.play(-1)
        self.feedback_sys = FeedbackSystem()
        self.heart_icon = VISUAL_CONFIG["heart_icon"]   # 生命图标

    
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
        todo::
        ! all points matched 与 match_score 功能重复
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
    

    def state_update(self, condition=False):
        """
        更新：索引、姿态分数、游戏总生命值、回合计时、反馈
        """

        # 获取计时开始时刻
        if self.pose_start_timing_flag == True:
            self.pose_start_time = time.time()
            # 关闭重置计时标志位
            self.pose_start_timing_flag = False

        if condition > 0.3: # 并不是有匹配度就判定为成功，而要达到阈值0.3
            # 计算到达目标花费的时间
            time_period = time.time() - self.pose_start_time

            # 判分
            if time_period < 1.5:
                self.feedback_sys.add_feedback("perfect", 10)
            elif time_period < 2.5:
                self.feedback_sys.add_feedback("great", 5)
            else:
                self.feedback_sys.add_feedback("good", 3)
            
            # 开启重置计时标志位
            self.pose_start_timing_flag = True

            # 本轮次结束
            # self.lastround_ended_flag = True
            
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


    def round_timing(self):
        """处理回合时间"""
        current_time = time.time()                  # 当前标准时刻

        if self.lastround_ended_flag:               # 若上一轮次结束
            self.lastround_ended_flag = False       # 重置上一轮次结束标志位
            self.round_start_time = current_time    # 重置回合开始时间

        self.round_elapsed_time = current_time - self.round_start_time                              # 计算回合已用时间
        self.round_remaining_time = self.round_duration - self.round_elapsed_time        # 计算回合剩余时间（可能为负数）
        # self.round_remaining_time = TIMER_CONFIG["round_duration"] - self.round_elapsed_time        # 计算回合剩余时间（可能为负数）

        if self.round_remaining_time < 0:  # 判定回合耗时超限
            # 强制结束回合
            self.lastround_ended_flag = True
            # 造成伤害
            return True     
        
        elif self.match_score > 0.3:        # 判定达到更新回合的条件
            # 自然结束回合
            self.lastround_ended_flag = True
            # 不造成伤害
            return False
        
        return False

    def main_update(self):
        if self.running:

            """回合计时"""
            harm = self.round_timing()

            """血量控制"""
            if harm:
                self.player_HP -= 1
                # self.feedback_sys.add_feedback("ouch", 0)   # 模式 HP 与反馈统计的得分无关 todo
            if self.player_HP <= 0:
                self.running = False    # 生命值小于等于0，游戏结束
            
            """手动中断"""
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    self.running = False

            """相机采集帧"""
            # 读取实时帧
            success, image = self.cap.read()
            if not success:
                pass

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
            self.condition_dict, _, self.match_score = self.update_conditioning(self.std_points,
                                                                                self.realtime_points,
                                                                                self.distance_threshold)

            """更新"""
            # 更新掩膜索引、点索引
            self.json_line_idx, self.std_overlay_idx = self.state_update(condition=self.match_score)
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
            draw.draw_points_with_arrow(self.canvas, self.std_points, self.realtime_points,
                                        self.condition_dict)  # 需传入每个选定点的布尔字典，以控制单独的箭头颜色

            """UI绘制"""
            # 转换到Pygame显示
            canvas_rgb = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2RGB)
            pygame_surface = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0, 1))
            self.screen.blit(pygame_surface, (0, 0))

            # 绘制界面元素
            # 显示"Timed Mode"标题
            title_surf = FONT_CONFIG["title"].render("Endless Challenge Mode", True, (255, 255, 255))
            title_rect = title_surf.get_rect(center=(WIN_WIDTH // 2, 30))
            self.screen.blit(title_surf, title_rect)

            # 绘制读条底衬
            bar_bg_rect = pygame.Rect(
                WIN_WIDTH - TIMER_CONFIG["bar_width"] - 20, 
                20,
                TIMER_CONFIG["bar_width"],
                TIMER_CONFIG["bar_height"]
            )
            pygame.draw.rect(self.screen, (50, 50, 50), bar_bg_rect)

            # 绘制进度条
            progress_width = int(TIMER_CONFIG["bar_width"] * (self.round_remaining_time / self.round_duration))
            progress_rect = pygame.Rect(
                WIN_WIDTH - TIMER_CONFIG["bar_width"] - 20 + (TIMER_CONFIG["bar_width"] - progress_width),
                20,
                progress_width,
                TIMER_CONFIG["bar_height"]
            )
            pygame.draw.rect(self.screen, (255, 87, 51) if self.round_remaining_time < 2 else (0, 191, 255), progress_rect) #todo

            # 绘制生命值
            for i in range(self.player_HP):
                heart_pos = (
                    WIN_WIDTH - 40 - i * 35,    #todo
                    60
                )
                self.screen.blit(self.heart_icon, heart_pos)    # todo if round_remaining_time < 2 改成显示红的icon or 闪烁
            
            """反馈"""
            self.feedback_sys.update_feedbacks()
            self.feedback_sys.draw_feedbacks(self.screen)
            self.feedback_sys.draw_score(self.screen)

            """显示"""
            pygame.display.flip()
            self.mode_clock.tick(FRAME_RATE)
            arr = pygame.surfarray.array3d(self.screen)   # shape: (width, height, 3)
            arr = np.swapaxes(arr, 0, 1)                  # shape: (height, width, 3)
    
        return arr


if __name__ == "__main__":
    """运动种类选择，内含发送"""
    sport = get_sport_type(sport_str = ["TaiChi", "Aerobics", "Yoga"])
    sport = "太极"  # 临时

    mode = EndlessChallengeMode(sport_type=sport, round_duration=15)

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
        frame = Draw.draw_game_over(score=final_score, img_dir="gameAssets\images\challenge_end.png")
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