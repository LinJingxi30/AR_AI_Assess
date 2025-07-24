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
            self.user_evaluation_data_save(self.conditions)

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
        self.rt_pose_list = []   # 实时完整姿态列表，格式为： [33 * tuple(x, y, z=0)] 或 []
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
