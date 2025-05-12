# align_guide.py
from functools import lru_cache
import json
import time
import sys
from pathlib import Path
import mediapipe as mp
import draw
PY_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PY_ROOT))   # 添加 Python 根目录到模块搜索路径中
from Config import WIN_SIZE, STD_SPORTS_RESULTS_ROOT
import cv2
import pygame
import numpy as np
from pathlib import Path
from guider import *
from Config import STD_SPORTS_RESULTS_ROOT, WIN_SIZE

# 重载常量
PATHS = {
    "标准 JSON 文件路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "C79-V2.1_points_align.json",
    "标准掩膜图片路径": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi" / "pregame_align",
    "背景音乐": Path(PY_ROOT) / "gameAssets" / "sounds" / "SJTUbgm.mp3",
}

PTS_PAIR_COLORS = [
    [(255, 78, 0)],    
    [(23, 210, 255)],  
    [(255, 78, 0)],    
    [(23, 210, 255)],  
]

PTS_CONDITION_THRESH = [[50], [50], [50], [50]] # 对应上面的 4 个点的判定阈值

class AlignGuider(Guider):
    def __init__(self):
        super().__init__(paths=PATHS)  # 调用父类会初始化摄像头、mediapipe、pygame、加载 JSON……
        # 我们只关心这四个 landmark
        self.POSE_ALIGN_LANDMARKS = [[19], [20], [31], [32]]
        self.conditions = [False]

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
                                 landmarks=self.POSE_ALIGN_LANDMARK,
                                 thresholds=PTS_CONDITION_THRESH, 
                                 std_lm_list=self.std_landmarks_list, 
                                 rt_lm_list=self.rt_landmarks_list)
            
            """步进跳帧"""
            # self.conditions = [True] * len(POSE_ALIGN_LANDMARKS)  # 调试
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
    
    def canvas_render(self, rt_frame, conditions):
        """绘制实时画面帧"""
        self.canvas = rt_frame.copy()  # 复制实时画面帧到画布

        """标准对齐点加载"""
        if self.current_std_index >= len(self.std_pose_lists):
            # todo:: 这里可以添加循环播放的逻辑；结束逻辑
            pass
        
        self.POSE_ALIGN_LANDMARK = self.POSE_ALIGN_LANDMARKS[self.current_std_index]
        self.std_pose_list = self.std_pose_lists[self.current_std_index]  # 标准完整姿态列表，从 lists 中获取 list，格式同上
        self.std_landmarks_list = self.get_landmarks_list(self.std_pose_list, landmarks=self.POSE_ALIGN_LANDMARK)   # 标准关键（对齐）点列表，格式同上
        self.std_overlay = self.get_current_std_overlay(paths=self.std_overlay_paths, overlay_idx=self.current_std_index)  # 标准帧路径，格式为 str

        """实时对齐点获取"""
        self.rt_pose_list = self.pose_detection(self.real_world_frame)   # 实时完整姿态列表，格式为： [33 * tuple(x, y, z=0)] 或 []
        self.rt_landmarks_list = self.get_landmarks_list(self.rt_pose_list, landmarks=self.POSE_ALIGN_LANDMARK) # 实时关键（对齐）点列表，格式为： [4 * int(x, y)] 或 []

        """获取实时躯干位置；获取标准中心标点"""
        self.rt_center = self.get_center_from_points_2d(self.rt_pose_list, from_pts_idx=RT_PTS_TO_CENTER, win_size=WIN_SIZE, y_offset=STD_CENTER_Y_OFFSET)  # tuple(float, float)
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
        pts_colors = PTS_PAIR_COLORS[self.current_std_index]
        self.canvas = draw.draw_points_and_arrows(self.canvas, 
                                                  self.std_landmarks_list, 
                                                  self.rt_landmarks_list, 
                                                  conditions,
                                                  colors=pts_colors)
        
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
            if all(conditions):
                self.running = False  # 退出
        
        return cur_index


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
    guide = AlignGuider()
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