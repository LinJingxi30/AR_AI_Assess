import sys
from pathlib import Path
PY_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PY_ROOT))   # 添加 Python 根目录到模块搜索路径中
from guider import *


WIN_WIDTH, WIN_HEIGHT = WIN_SIZE

POSE_ALIGN_LANDMARKS = [19, 20, 31, 32]  # 左指尖、右指尖、左脚尖、右脚尖
# PTS_CONDITION_THRESH = [70, 70, 150, 150] # 对应上面的 4 个点的判定阈值
PTS_CONDITION_THRESH = [80, 80, 250, 250] # 对应上面的 4 个点的判定阈值
RT_PTS_TO_CENTER = [11, 12, 23, 24]  # 左肩、右肩、左髋、右髋

LIGHTNESS = 0.9  # 画布亮度调整系数
STD_SCALE = 0.7  # 标准对齐点/掩膜缩放系数
STD_CENTER_Y_OFFSET = 10   # 标准中心相对实时中心纵向偏移高度（像素）(上正下负)
STD_OVERLAY_OPACITY = 0.6  # 掩膜透明度

MAX_SCORE = 100  # 最大分数



class Video(Guider):
    def init__(self, camera,scale, frame_rate=30, debug=False):
        super().__init__(camera=camera,scale=scale ,frame_rate=frame_rate, debug=debug)
    
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

        return self.score
    
    def main_update(self, frame=None):
        # 可以从外部传实时帧
        if self.running:

            """处理 Pygame 窗口事件"""
            self.window_events()

            """帧率控制"""
            self.frame_rate_clock.tick(self.frame_rate)

            """获取、处理实时画面帧"""
            # （已翻转）（已拉伸到窗口分辨率）
            self.real_world_frame,_ = self.camera.get_camera_processed_frame(
                frame=frame,
                win_size=WIN_SIZE
            )
            # cv2.imshow("实时画面", self.real_world_frame)  # 调试：显示实时画面
            # sys.stderr.write("实时画面帧已处理\n")

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

            """保存数据"""
            # self.user_evaluation_data_save(self.conditions)

            """步进跳帧"""
            if self.debug:
                self.conditions = [True] * len(POSE_ALIGN_LANDMARKS)  # 调试
            
            if self.std_skips[self.current_std_index]:
                # 如果当前帧是自动不停播帧，跳过条件检查
                self.conditions = [True] * len(POSE_ALIGN_LANDMARKS)
            self.current_std_index = self.index_update(conditions=self.conditions,
                                                       cur_index=self.current_std_index,
                                                       end_index=len(self.std_pose_lists)-1)

            """分数统计"""
            self.score = self.single_posture_score_calc(max_tot_score=MAX_SCORE,
                                                        tot_score=self.score,
                                                        conditions=self.conditions,
                                                        time_range=(0, 2))    # 调整时间范围以调整判分宽松度（最佳，最差）

            """绘制 Pygame UI"""
            # 绘制已用时间、招式、实时总得分
            self.pygame_UI_render(canvas=self.canvas, CONFIGS=PYGAME_UI_CONFIG)

        return self.screen

    def canvas_render(self, rt_frame, conditions):
        """绘制实时画面帧"""
        self.canvas = rt_frame.copy()  # 复制实时画面帧到画布

        """标准对齐点加载"""
        self.std_pose_list = self.std_pose_lists[self.current_std_index]  # 标准完整姿态列表，从 lists 中获取 list，格式同上
        self.std_landmarks_list = self.get_landmarks_list(self.std_pose_list, landmarks=POSE_ALIGN_LANDMARKS)   # 标准关键（对齐）点列表，格式同上
        self.std_overlay = self.get_current_std_overlay(paths=self.std_overlay_paths, overlay_idx=self.current_std_index)  # 标准帧路径，格式为 str

        """实时对齐点获取"""
        self.rt_pose_list = self.pose_detection(self.real_world_frame)  # 实时完整姿态列表，格式为： [33 * tuple(x, y, z=0)] 或 []
        self.rt_landmarks_list = self.get_landmarks_list(self.rt_pose_list, landmarks=POSE_ALIGN_LANDMARKS) # 实时关键（对齐）点列表，格式为： [4 * int(x, y)] 或 []

        global STD_SCALE
        if self.current_std_index==0:
            STD_SCALE = self.get_scale(self.rt_pose_list)  # 获取缩放比例
        
        """获取实时躯干位置；获取标准中心标点"""
        self.rt_center = self.get_center_from_points_2d(self.rt_pose_list, from_pts_idx=RT_PTS_TO_CENTER, win_size=WIN_SIZE, y_offset=STD_CENTER_Y_OFFSET)  # tuple(float, float)
        # self.rt_center = (self.rt_center[0], self.rt_center[1] + BENEATH)   # 参数调整中心点位置，向下偏移 BENEATH 像素
        self.std_center = (self.std_pose_list[0][0] * STD_SCALE, self.std_pose_list[0][1] * STD_SCALE)  # std_pose_list 的第一个元组是标点中心点 (3d to 2d)

        """将标准对齐点吸附到用户"""
        self.align_pose_to_target_by_center_2d(self.std_landmarks_list, center=self.std_center, target=self.rt_center, scale=STD_SCALE, win_size=WIN_SIZE)
        # print(self.std_landmarks_list) # 调试

        """叠加掩膜到画布"""
        self.canvas = (self.canvas * LIGHTNESS).astype(np.uint8)  # 调整画布亮度
        self.canvas = draw.draw_overlay_centered(self.canvas, self.std_overlay,
                                                    center=self.std_center, target=self.rt_center,
                                                    win_size=WIN_SIZE,
                                                    scale=STD_SCALE,
                                                    opacity=0.9)  # 在画布上叠加掩膜，掩膜中心点与用户中心点对齐

    def get_scale(self, std_pose_list):
        """
        获取缩放比例
        """
        # std_pose_list 是 [33 * (x, y, z=0)]，其中左指尖、右指尖、左脚尖、右脚尖分别在 POSE_ALIGN_LANDMARKS 索引
        # 以左右指尖和左右脚尖的最大横向距离为基准，和 1100 像素做比例
        if not std_pose_list or len(std_pose_list) < max(POSE_ALIGN_LANDMARKS) + 1:
            return 0.7  # 防止异常，返回默认缩放比例

        # 获取四个关键点的 x 坐标
        y_coords = [std_pose_list[idx][1] for idx, _ in enumerate(std_pose_list)]
        # 计算最大和最小 x 坐标的距离
        pose_width = max(y_coords) - min(y_coords)
        if pose_width == 0:
            return 0.8  # 防止除零
        if self.s == 0:
            scale = pose_width / 600.0
            return scale
        if self.s == 1:
            scale = pose_width / 1600.0
            return scale
        if self.s == 2:
            scale = pose_width / 2000.0
            return scale
        # """绘制 对齐点 + 箭头 到画布"""
        # self.canvas = draw.draw_points_and_arrows(self.canvas,
        #                                           self.std_landmarks_list,
        #                                           self.rt_landmarks_list,
        #                                           conditions)

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


    @staticmethod
    def load_std_pose_lists(json_path, landmarks=None) -> list[list[tuple]]:
        # 嵌套列表 [[33 * tuple(x, y, z=0)], ..., ] len(json)
        std_full_pose_lists = []
        std_skips = []
        std_img_names = []
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

                # 自动不停播列表（bool）
                # 尝试获取 frame_dict["points"] 字典中的 "skip" 键，如果不存在则返回默认值 False，
                # 因此即使 JSON 中缺少 "skip" 键，也不会报错。
                # std_skips.append(frame_dict["points"].get("skip", False))   # 标签程序写不好，嵌套在points里了
                std_skips.append(True)
                std_img_names.append(frame_dict["image"])  # 新增：记录图片名，后续按照图片名进行匹配

        # [[33 * tuple(x, y, z=0)], ..., ] len(json)
        return std_full_pose_lists, std_skips, std_img_names
        # return std_full_pose_lists

    # 旧版：加载标准帧路径
    # @staticmethod
    # def load_std_frame_paths(frame_path) -> list[str]:
    #     # 存储目录下的所有 PNG 文件路径，按名称排序，转为字符串（ pathlib 写法）
    #     frame_paths_list = [str(p) for p in sorted(Path(frame_path).glob("*.png"))]
    #     # list[Path] -> list[str]
    #     return frame_paths_list


class pre_clip(Guider):
    def __init__(self, camera, uuid,scale, paths=PATHS, debug=False):
        # config 配置
        win_topic = "AR太极拳助手" + uuid
        self.frame_rate = 60

        self.uuid = uuid
        self.s = scale
        # path 路径
        self.std_json_path = paths["标准 JSON 文件路径"]
        self.std_frame_path = paths["标准掩膜图片路径"]
        win_bgm_path = paths["背景音乐"]
        self.differences_json_path = paths["标准 JSON 文件路径"] / ".." / "differences.json"
        self.user_replay_json_path = paths["标准 JSON 文件路径"] / ".." / "user_replay.json"

        # utils 工具
        self.camera = camera
        self.pose_detector = None
        self.frame_rate_clock = None

        # resource 资源
        self.std_pose_lists = None
        self.std_overlay_paths = None
        self.std_skips = None  # 自动不停播列表（bool）, length = len(std_pose_lists)
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
        self.pose_detector_init()
        self.pygame_init(win_topic=win_topic, win_bgm_path=str(win_bgm_path))

        # load 初始化加载资源
        self.clear_difference_json()
        # self.std_pose_lists, self.std_overlay_paths = self.load_std_resources(self.std_json_path, self.std_frame_path)
        self.std_pose_lists, self.std_skips, self.std_overlay_paths = self.load_std_resources(self.std_json_path,self.std_frame_path)

        # state 状态
        self.current_std_index = 0
        self.timer = None
        self.conditions = [False] * len(POSE_ALIGN_LANDMARKS)
        self.score = 0
        self.debug = debug
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

        return self.score

    def main_loop_with_voice(self):
        while self.running:
            # 渲染 .screen
            self.main_update()
            # 获取 JPEG 字节数据
            frame_to_web = self.get_transmit_frame(self.screen)
            # 发送 JPEG 数据
            if not self.debug:
                self.send_jpeg_data(frame_to_web)
            # 更新窗口显示
            pygame.display.flip()

            # 发送音频提示指令
            self.send_voice_command()

        return self.score

    def main_update(self, frame=None):
        # 可以从外部传实时帧

        if self.running and (not Config.IS_PAUSE):

            """处理 Pygame 窗口事件"""
            self.window_events()

            """帧率控制"""
            self.frame_rate_clock.tick(self.frame_rate)

            """获取、处理实时画面帧"""
            # （已翻转）（已拉伸到窗口分辨率）
            self.real_world_frame, _ = self.camera.get_camera_processed_frame(
                frame=frame,
                win_size=WIN_SIZE
            )
            # cv2.imshow("实时画面", self.real_world_frame)  # 调试：显示实时画面
            # sys.stderr.write("实时画面帧已处理\n")

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

            """保存数据"""
            # self.user_evaluation_data_save(self.conditions)

            """步进跳帧"""
            if self.debug:
                self.conditions = [True] * len(POSE_ALIGN_LANDMARKS)  # 调试

            if self.std_skips[self.current_std_index]:
                # 如果当前帧是自动不停播帧，跳过条件检查
                self.conditions = [True] * len(POSE_ALIGN_LANDMARKS)
            self.current_std_index = self.index_update(conditions=self.conditions,
                                                       cur_index=self.current_std_index,
                                                       end_index=len(self.std_pose_lists) - 1)

            """分数统计"""
            self.score = self.single_posture_score_calc(max_tot_score=MAX_SCORE,
                                                        tot_score=self.score,
                                                        conditions=self.conditions,
                                                        time_range=(0, 2))  # 调整时间范围以调整判分宽松度（最佳，最差）

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
            cv2.IMWRITE_JPEG_QUALITY, 90,  # 压缩质量
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

    def index_update(self, conditions, cur_index, end_index):
        """
        根据条件，步进跳帧
        """
        if cur_index < end_index:
            if all(conditions):
                # 如果所有条件都满足，跳到下一帧
                cur_index += 1
                # elif 三秒
        else:
            # print("最后一帧：",cur_index)   # 调试
            if all(conditions):
                self.running = False  # 退出

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
        """绘制实时画面帧，新增各步骤耗时统计"""
        # start_total = time.time()  # 总耗时起点
        self.canvas = rt_frame  # 复制实时画面帧到画布
        # end_std_load = time.time()
        # sys.stderr.write(f"canvas copy: {end_std_load - start_total:.6f} 秒\n")

        # ---- 标准对齐点加载 步骤计时 ----
        # start_std_load = time.time()
        self.std_pose_list = self.std_pose_lists[self.current_std_index]
        self.std_landmarks_list = self.get_landmarks_list(self.std_pose_list, landmarks=POSE_ALIGN_LANDMARKS)
        self.std_overlay = self.get_current_std_overlay(paths=self.std_overlay_paths,
                                                        overlay_idx=self.current_std_index)
        # end_std_load = time.time()
        # sys.stderr.write(f"std points: {end_std_load - start_std_load:.6f} 秒\n")

        # ---- 实时对齐点获取 步骤计时 ----
        # start_rt_load = time.time()
        self.rt_pose_list = self.pose_detection(self.real_world_frame)
        self.rt_landmarks_list = self.get_landmarks_list(self.rt_pose_list, landmarks=POSE_ALIGN_LANDMARKS)
        # end_rt_load = time.time()
        # sys.stderr.write(f"real time points: {end_rt_load - start_rt_load:.6f} 秒\n")

        global STD_SCALE
        if self.current_std_index == 0:
            STD_SCALE = self.get_scale(self.rt_pose_list)  # 获取缩放比例

        """获取实时躯干位置；获取标准中心标点"""
        self.rt_center = self.get_center_from_points_2d(self.rt_pose_list, from_pts_idx=RT_PTS_TO_CENTER,
                                                        win_size=WIN_SIZE,
                                                        y_offset=STD_CENTER_Y_OFFSET)  # tuple(float, float)
        # self.rt_center = (self.rt_center[0], self.rt_center[1] + BENEATH)   # 参数调整中心点位置，向下偏移 BENEATH 像素
        self.std_center = (self.std_pose_list[0][0] * STD_SCALE,
                           self.std_pose_list[0][1] * STD_SCALE)  # std_pose_list 的第一个元组是标点中心点 (3d to 2d)

        # # ---- 获取实时/标准中心 步骤计时 ----
        # self.rt_center = self.get_center_from_points_2d(self.rt_pose_list, from_pts_idx=RT_PTS_TO_CENTER, win_size=WIN_SIZE, y_offset=STD_CENTER_Y_OFFSET)
        # self.std_center = (self.std_pose_list[0][0] * STD_SCALE, self.std_pose_list[0][1] * STD_SCALE)

        # ---- 对齐点吸附 步骤计时 ----
        self.align_pose_to_target_by_center_2d(self.std_landmarks_list, center=self.std_center, target=self.rt_center,
                                               scale=STD_SCALE, win_size=WIN_SIZE)

        # ---- 画布亮度调整 + 掩膜叠加 步骤计时 ----
        # start_canvas = time.time()
        # self.canvas = (self.canvas * LIGHTNESS).astype(np.uint8)
        # end_canvas = time.time()
        # sys.stderr.write(f"canvas change brightness: {end_canvas - start_canvas:.6f} 秒\n")
        # start_canvas = time.time()
        self.canvas = draw.draw_overlay_centered(self.canvas, self.std_overlay,
                                                 center=self.std_center, target=self.rt_center,
                                                 win_size=WIN_SIZE,
                                                 scale=STD_SCALE,
                                                 opacity=STD_OVERLAY_OPACITY)
        end_canvas = time.time()
        # sys.stderr.write(f"mask total time: {end_canvas - start_canvas:.6f} 秒\n")

        # ---- 绘制点和箭头 步骤计时 ----
        # start_draw = time.time()
        self.canvas = draw.draw_points_and_arrows(self.canvas,
                                                  self.std_landmarks_list,
                                                  self.rt_landmarks_list,
                                                  conditions)
        # end_draw = time.time()
        # sys.stderr.write(f"Point and arrow: {end_draw - start_draw:.6f} 秒\n")

        # end_total = time.time()
        # sys.stderr.write(f"canvas_render total cost: {end_total - start_total:.6f} 秒\n\n")

    def get_scale(self, std_pose_list):
        """
        获取缩放比例
        """
        # std_pose_list 是 [33 * (x, y, z=0)]，其中左指尖、右指尖、左脚尖、右脚尖分别在 POSE_ALIGN_LANDMARKS 索引
        # 以左右指尖和左右脚尖的最大横向距离为基准，和 1100 像素做比例
        if not std_pose_list or len(std_pose_list) < max(POSE_ALIGN_LANDMARKS) + 1:
            return 0.7  # 防止异常，返回默认缩放比例

        # 获取四个关键点的 x 坐标
        y_coords = [std_pose_list[idx][1] for idx, _ in enumerate(std_pose_list)]
        # 计算最大和最小 x 坐标的距离
        pose_width = max(y_coords) - min(y_coords)
        if pose_width == 0:
            return 0.8  # 防止除零
        if self.s == 0:
            scale = pose_width / 600.0
            return scale
        if  self.s ==1:
            scale = pose_width / 1600.0
            return scale
        if self.s ==2:
            scale = pose_width / 2000.0
            return scale

    def window_events(self):
        """
        窗口事件：
        退出：Esc
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                # 按 Esc 退出当前播片实例。
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                # 按 q 直接退出程序。
                raise RuntimeError("已手动终止程序。")
        return self.running

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

    def pygame_init(self, win_bgm_path=None, win_topic="AR太极拳助手"):
        """
        初始化 Pygame
        窗口、音频、反馈系统
        """
        # 初始化 pygame 及混音器
        pygame.init()
        pygame.mixer.init()

        # 加载背景音乐 bgm
        if win_bgm_path:
            pygame.mixer.music.load(win_bgm_path)
            pygame.mixer.music.set_volume(1)  # 音量范围 0.0 - 1.0
            pygame.mixer.music.play(-1)  # -1 表示循环播放

        # 初始化窗口
        self.screen = pygame.display.set_mode(WIN_SIZE)
        pygame.display.set_caption(win_topic)  # 窗口标题
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
        std_pose_lists, std_skips, std_img_names = self.load_std_pose_lists(json_path, landmarks=POSE_ALIGN_LANDMARKS)
        # std_pose_lists = self.load_std_pose_lists(json_path, landmarks=POSE_ALIGN_LANDMARKS)

        # 标准帧路径合集列表
        # [str(path), str, ...]
        # std_overlay_paths = self.load_std_frame_paths(frame_path)
        std_overlay_paths = [str(Path(frame_path) / img_name) for img_name in std_img_names]  # 使用文件名寻址

        # 标准姿态 列表列表；标准帧路径 列表
        return std_pose_lists, std_skips, std_overlay_paths
        # return std_pose_lists, std_overlay_paths

    @staticmethod
    def load_std_pose_lists(json_path, landmarks=None) -> list[list[tuple]]:
        # 嵌套列表 [[33 * tuple(x, y, z=0)], ..., ] len(json)
        std_full_pose_lists = []
        std_skips = []
        std_img_names = []
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
                    *((0, 0, 0) for _ in range(landmarks[0] - 1)),
                    (
                        frame_dict["points"]["left_h"][0],
                        frame_dict["points"]["left_h"][1],
                        0
                    ),  # poes_list[i] 是第 i+1 个，前有 i 个 (0, 0, 0)
                    *((0, 0, 0) for _ in range(landmarks[1] - landmarks[0] - 1)),
                    (
                        frame_dict["points"]["right_h"][0],
                        frame_dict["points"]["right_h"][1],
                        0
                    ),  # 索引对应
                    *((0, 0, 0) for _ in range(landmarks[2] - landmarks[1] - 1)),
                    (
                        frame_dict["points"]["left_f"][0],
                        frame_dict["points"]["left_f"][1],
                        0
                    ),  # 索引对应
                    *((0, 0, 0) for _ in range(landmarks[3] - landmarks[2] - 1)),
                    (
                        frame_dict["points"]["right_f"][0],
                        frame_dict["points"]["right_f"][1],
                        0
                    ),  # 索引对应
                    *((0, 0, 0) for _ in range(LAST_IDX - landmarks[3] - 1)),
                ]

                # 存储到嵌套列表中
                std_full_pose_lists.append(pose_list)

                # 自动不停播列表（bool）
                # 尝试获取 frame_dict["points"] 字典中的 "skip" 键，如果不存在则返回默认值 False，
                # 因此即使 JSON 中缺少 "skip" 键，也不会报错。
                # std_skips.append(False)   # 标签程序写不好，嵌套在points里了
                std_skips.append(frame_dict["points"].get("skip", False))
                std_img_names.append(frame_dict["image"])  # 新增：记录图片名，后续按照图片名进行匹配

        # [[33 * tuple(x, y, z=0)], ..., ] len(json)
        return std_full_pose_lists, std_skips, std_img_names
        # return std_full_pose_lists

    # 旧版：加载标准帧路径
    # @staticmethod
    # def load_std_frame_paths(frame_path) -> list[str]:
    #     # 存储目录下的所有 PNG 文件路径，按名称排序，转为字符串（ pathlib 写法）
    #     frame_paths_list = [str(p) for p in sorted(Path(frame_path).glob("*.png"))]
    #     # list[Path] -> list[str]
    #     return frame_paths_list

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
            print(f"出错了！paths长度：{len(paths)}, 掩膜索引: {overlay_idx}，应为长度-1")
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
    def align_pose_to_target_by_center_2d(std_landmarks_list, center, target, scale=1.0, win_size=WIN_SIZE):
        """
        将标准对齐点列表 std_landmarks_list 根据中心点 center，吸附到目标点 target 上
        """
        if not std_landmarks_list:
            return
        if not target:
            # 如果没有目标点，则使用窗口中心点作为目标
            target = (win_size[0] // 2, win_size[1] // 2)

        if not center:
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

    def send_voice_command(self, command: any = None):
        """默认是无语音的，等待重载"""
        pass

    def clear_difference_json(self):
        """
        清空 JSON 文件内容，如果文件不存在则创建新文件
        """
        # 直接以写入模式打开，不管文件是否存在，都会创建或清空
        with open(self.differences_json_path, 'w') as f:
            pass  # 打开后立即关闭即可清空内容或创建文件
        with open(self.user_replay_json_path, 'w') as f:
            pass

    def user_evaluation_data_save(self, conditions):
        """
        当 conditions 的四个标准点全为 True 时，计算 std_landmarks_list 和 rt_landmarks_list 的差值，
        并逐帧写入 JSON 文件，标记为左手、右手、左脚、右脚的坐标。
        """
        if all(conditions):

            # Replay 实时重映
            with open(self.user_replay_json_path, 'a') as f:
                rt_pose_lists = [list(pt) for pt in self.rt_pose_list]
                # [[x, y, z], ...*33]
                json.dump({"full_pose_3d": rt_pose_lists}, f, ensure_ascii=False)
                f.write("\n")

            # 确保 std_landmarks_list 和 rt_landmarks_list 都存在且长度一致
            if self.std_landmarks_list and self.rt_landmarks_list and len(self.std_landmarks_list) == len(
                    self.rt_landmarks_list):
                # 计算差值
                differences = {
                    "left_h": {"x": self.std_landmarks_list[0][0] - self.rt_landmarks_list[0][0],
                               "y": self.std_landmarks_list[0][1] - self.rt_landmarks_list[0][1]},
                    "right_h": {"x": self.std_landmarks_list[1][0] - self.rt_landmarks_list[1][0],
                                "y": self.std_landmarks_list[1][1] - self.rt_landmarks_list[1][1]},
                    "left_f": {"x": self.std_landmarks_list[2][0] - self.rt_landmarks_list[2][0],
                               "y": self.std_landmarks_list[2][1] - self.rt_landmarks_list[2][1]},
                    "right_f": {"x": self.std_landmarks_list[3][0] - self.rt_landmarks_list[3][0],
                                "y": self.std_landmarks_list[3][1] - self.rt_landmarks_list[3][1]}
                }

                # 将当前帧的差值追加到 JSON 文件中
                with open(self.differences_json_path, 'a') as f:
                    json.dump(differences, f, ensure_ascii=False)
                    f.write("\n")  # 每帧数据占一行

                print(f"差值已追加到 {self.differences_json_path}", file=sys.stderr)
            else:
                print("无法保存差值：std_landmarks_list 和 rt_landmarks_list 不匹配或为空。", file=sys.stderr)
                # raise ValueError("无法保存差值：std_landmarks_list 和 rt_landmarks_list 不匹配或为空。")