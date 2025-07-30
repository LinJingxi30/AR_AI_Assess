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
    def init__(self, camera, frame_rate=30, debug=False):
        super().__init__(camera=camera, frame_rate=frame_rate, debug=debug)
    
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
        std_overlay_paths = [str(Path(frame_path) / img_name) for img_name in std_img_names]    # 使用文件名寻址

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

    def get_scale(self,std_pose_list):
        """
        获取缩放比例
        """
        # std_pose_list 是 [33 * (x, y, z=0)]，其中左指尖、右指尖、左脚尖、右脚尖分别在 POSE_ALIGN_LANDMARKS 索引
        # 以左右指尖和左右脚尖的最大横向距离为基准，和 1100 像素做比例
        if not std_pose_list or len(std_pose_list) < max(POSE_ALIGN_LANDMARKS) + 1:
            return 0.8  # 防止异常，返回默认缩放比例

        # 获取四个关键点的 x 坐标
        x_coords = [std_pose_list[idx][1] for idx,_ in enumerate(std_pose_list)]
        # 计算最大和最小 x 坐标的距离
        pose_width = max(x_coords) - min(x_coords)
        if pose_width == 0:
            return 0.8  # 防止除零

        scale = pose_width / 600.0 
        return scale
    # 旧版：加载标准帧路径
    # @staticmethod
    # def load_std_frame_paths(frame_path) -> list[str]:
    #     # 存储目录下的所有 PNG 文件路径，按名称排序，转为字符串（ pathlib 写法）
    #     frame_paths_list = [str(p) for p in sorted(Path(frame_path).glob("*.png"))]
    #     # list[Path] -> list[str]
    #     return frame_paths_list