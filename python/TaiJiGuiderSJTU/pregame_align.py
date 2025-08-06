import sys
from pathlib import Path
PY_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PY_ROOT))   # 添加 Python 根目录到模块搜索路径中
from guider import *

# 重载常量
PATHS = {
    "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "pregame_align" / "pre.json",
    "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "pregame_align",
    "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
}

PTS_PAIR_COLORS = [
    [(255, 78, 0)],    
    [(23, 210, 255)],  
    [(255, 78, 0)],    
    [(23, 210, 255)],  
    [(255, 78, 0)],    
    [(23, 210, 255)],  
    [(255, 78, 0)],    
    [(23, 210, 255)],
]

PTS_CONDITION_THRESH = [[70], [70], [150], [150],[70], [70], [150], [150]] # 对应上面的 4 个点的判定阈值

class PreAlignerPoints(Guider):
    def __init__(self, camera,uuid, _paths=PATHS, debug=False):
        super().__init__(camera=camera,uuid = uuid,scale=0, paths=_paths, debug=debug)  # 调用父类会初始化摄像头、mediapipe、pygame、加载 JSON……
        # 我们只关心这四个 landmark
        self.POSE_ALIGN_LANDMARK = None
        self.POSE_ALIGN_LANDMARKS = [[19], [20], [31], [32],[19], [20], [31], [32]]
        self.conditions = [False]

    def main_update(self, frame=None):
        # 可以从外部传实时帧
        if self.running:

            """处理 Pygame 窗口事件"""
            self.window_events()

            """帧率控制"""
            self.frame_rate_clock.tick(self.frame_rate)

            """获取实时画面帧"""
            # （已翻转）（已拉伸到窗口分辨率）
            self.real_world_frame,processed_shape = self.camera.get_camera_processed_frame(
                win_size=WIN_SIZE,
                frame=frame
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
                                 landmarks=self.POSE_ALIGN_LANDMARK,
                                 thresholds=PTS_CONDITION_THRESH, 
                                 std_lm_list=self.std_landmarks_list, 
                                 rt_lm_list=self.rt_landmarks_list)
            
            """步进跳帧"""
            if self.debug:
                self.conditions = [True] * len(POSE_ALIGN_LANDMARKS)  # 调试
            self.current_std_index = self.index_update(conditions=self.conditions, 
                                                       cur_index=self.current_std_index, 
                                                       end_index=len(self.std_pose_lists)-1)


            
            # print(self., self.)

            """分数统计"""
            self.score = self.single_posture_score_calc(max_tot_score=MAX_SCORE,
                                                        tot_score=self.score,
                                                        conditions=self.conditions,
                                                        time_range=(1, 8))    # 调整时间范围以调整判分宽松度（最佳，最差）

            """绘制 Pygame UI"""
            # 绘制已用时间、招式、实时总得分
            self.pygame_UI_render(canvas=self.canvas, CONFIGS=PYGAME_UI_CONFIG)

        return self.screen
    
    def send_voice_command(self, command: any=None):
        """
        音频提示指令发送
        逻辑写死什么时候发什么
        """
        # 只在每个 index 首次到达时发送一次指令
        if not hasattr(self, "_voice_sent"):
            self._voice_sent = set()
        if self.current_std_index == 1 and 1 not in self._voice_sent:
            DataSender.send_control("PLAY_AUDIO",flag = "语音2.mp3")
            self._voice_sent.add(1)
        if self.current_std_index == 2 and 2 not in self._voice_sent:
            DataSender.send_control("PLAY_AUDIO",flag = "语音4.mp3")
            self._voice_sent.add(2)
        if self.current_std_index == 3 and 3 not in self._voice_sent:
            DataSender.send_control("PLAY_AUDIO",flag = "语音5.mp3")
            self._voice_sent.add(3)


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

        # # 绘制标题
        # TITLE = CONFIGS["标题"]
        # # 加载字体并设置字号
        # font = pygame.font.Font(TITLE["字体"], TITLE["字号"])
        # title_surface = font.render(TITLE["文字"], True, TITLE["颜色"])
        # title_rect = title_surface.get_rect(center=TITLE["位置"])
        # self.screen.blit(title_surface, title_rect)

        # # 绘制计分
        # SCORE = CONFIGS["计分"]
        # font = pygame.font.Font(SCORE["字体"], SCORE["字号"])
        # score_surface = font.render(f"{SCORE['文字']}{int(self.score)}分", True, SCORE["颜色"])
        # score_rect = score_surface.get_rect(center=SCORE["位置"])
        # self.screen.blit(score_surface, score_rect)
    
    def canvas_render(self, rt_frame, conditions):
        """绘制实时画面帧"""
        self.canvas = rt_frame.copy()  # 复制实时画面帧到画布

        """标准对齐点加载"""
        # 防止越界
        if self.current_std_index >= len(self.POSE_ALIGN_LANDMARKS):
            self.current_std_index = len(self.POSE_ALIGN_LANDMARKS) - 1
        self.POSE_ALIGN_LANDMARK = self.POSE_ALIGN_LANDMARKS[self.current_std_index]
        self.std_pose_list = self.std_pose_lists[self.current_std_index]  # 标准完整姿态列表，从 lists 中获取 list，格式同上
        self.std_landmarks_list = self.get_landmarks_list(self.std_pose_list, landmarks=self.POSE_ALIGN_LANDMARK)   # 标准关键（对齐）点列表，格式同上
        # self.std_overlay = self.get_current_std_overlay(paths=self.std_overlay_paths, overlay_idx=self.current_std_index)  # 标准帧路径，格式为 str

        """实时对齐点获取"""
        self.rt_pose_list = self.pose_detection(self.real_world_frame)   # 实时完整姿态列表，格式为： [33 * tuple(x, y, z=0)] 或 []
        self.rt_landmarks_list = self.get_landmarks_list(self.rt_pose_list, landmarks=self.POSE_ALIGN_LANDMARK) # 实时关键（对齐）点列表，格式为： [4 * int(x, y)] 或 []

        """获取实时躯干位置；获取标准中心标点"""
        self.rt_center = self.get_center_from_points_2d(self.rt_pose_list, from_pts_idx=RT_PTS_TO_CENTER, win_size=WIN_SIZE, y_offset=STD_CENTER_Y_OFFSET)  # tuple(float, float)
        self.std_center = (self.std_pose_list[0][0] * STD_SCALE, self.std_pose_list[0][1] * STD_SCALE)  # std_pose_list 的第一个元组是标点中心点 (3d to 2d)

        """将标准对齐点吸附到用户"""
        self.align_pose_to_target_by_center_2d(self.std_landmarks_list, center=self.std_center, target=self.rt_center, scale=STD_SCALE, win_size=WIN_SIZE)
        # print(self.std_landmarks_list) # 调试

        """叠加掩膜到画布"""
        # self.canvas = (self.canvas * LIGHTNESS).astype(np.uint8)  # 调整画布亮度
        # self.canvas = draw.draw_overlay_centered(self.canvas, self.std_overlay, 
        #                                             center=self.std_center, target=self.rt_center, 
        #                                             win_size=WIN_SIZE, 
        #                                             scale=STD_SCALE, 
        #                                             opacity=STD_OVERLAY_OPACITY)  # 在画布上叠加掩膜，掩膜中心点与用户中心点对齐

        """绘制 对齐点 + 箭头 到画布"""
        pts_colors = PTS_PAIR_COLORS[self.current_std_index]
        self.canvas = draw.draw_points_and_arrows(self.canvas, 
                                                  self.std_landmarks_list, 
                                                  self.rt_landmarks_list, 
                                                  conditions,
                                                  colors=pts_colors)


        # canvas = rt_frame.copy()
        # idx = self.current_std_index                  # 当前第几帧
        # lm_idx = self.guide_landmarks[idx]            # 要演示的 landmark 索引
        # std_pose = self.std_pose_lists[idx]           # 这一帧 33 点
        # x, y, _ = std_pose[idx]                       # (注意：std_pose 的列表顺序和 guide_landmarks 对齐)
        # x, y = int(x), int(y)

        # # 大圆高亮
        # cv2.circle(canvas, (x, y), 20, (0, 255, 255), -1)

        # # 设置 std_landmarks_list & rt_landmarks_list 供 condition_check 使用
        # self.std_landmarks_list = [(x, y)]
        # full_rt = self.pose_detection(rt_frame)
        # self.rt_landmarks_list = []
        # if lm_idx < len(full_rt):
        #     rx, ry, _ = full_rt[lm_idx]
        #     self.rt_landmarks_list = [(rx, ry)]

        # self.canvas = canvas

if __name__ == "__main__":
    guide = PreAlignerPoints()
    guide.running = True
    while guide.running:
        # 复用父类的 main_update：它会依次调用 window_events、camera_capture、canvas_render、condition_check、index_update、pygame_UI_render
        guide.main_update()
        # 获取 JPEG 字节数据
        frame_to_web = guide.get_transmit_frame(guide.screen)
        # 发送 JPEG 数据
        # guide.send_jpeg_data(frame_to_web)
        # 更新窗口显示
        pygame.display.flip()
    guide.camera.release()
    pygame.quit()






# from guider import *

# class Align(Guider):
#     def __init__(self):
#         super.__init__(self, Guider)
#         # path 路径
#         self.std_json_path = Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "C79-V2.1_points.json"
#         self.std_frame_path = Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "masked_sampled_std_frames"




# 每张图给一个点传到draw_points_and_arrows(canvas, std_landmarks_list, rt_landmarks_list, condition):
# 每次只有一个false

# 结束逻辑改这个函数
# def index_update(conditions, cur_index, end_index):
#         """
#         根据条件，步进跳帧
#         """
#         if cur_index < end_index - 1:
#             if all(conditions):
#                 # 如果所有条件都满足，跳到下一帧
#                 cur_index += 1
#                 # elif 三秒
#         else:
#             cur_index = 0  # 循环播放
        
#         return cur_index                     
# 要结束时else:
#             TaiJiAligner.running = False  # 停止程序


# self.std_json_path = Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "C79-V2.1_points.json"
# self.std_frame_path = Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "masked_sampled_std_frames"
# 路径改为一个新的文件夹，其中只有四张图片