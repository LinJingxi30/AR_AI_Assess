import sys
from guider import Guider, POSE_ALIGN_LANDMARKS
import draw
from pathlib import Path

PY_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PY_ROOT))  # 添加 Python 根目录到模块搜索路径中
from Config import WIN_SIZE
import pygame
import cv2

WIN_WIDTH, WIN_HEIGHT = WIN_SIZE

PYGAME_SELECT_UI_CONFIG = {
    "标题": {
        "文字": "太极引导助手",
        "字体": str(Path(PY_ROOT) / "gameAssets" / "fonts" / "SmileySans-Oblique.ttf"),
        "字号": 60,
        "颜色": (100, 155, 255),  # RGB(100, 155, 255)
        "位置": (180, 60),
    },
    "计分": {
        "文字": "请选择种类！",
        "字体": str(Path(PY_ROOT) / "gameAssets" / "fonts" / "SmileySans-Oblique.ttf"),
        "字号": 40,
        "颜色": (255, 215, 255),  # RGB(255, 215, 255)
        "位置": (WIN_WIDTH - 160, 60),
    },
    # todo:: 招式得分
}

BUTTONS_CONFIG = {
    "texts": ["太极操", "八法五步", "24式太极拳"],
    "size": (100, 70),  # 按钮大小
    "color": (0, 155, 0),  # 按钮颜色
    "text_color": (255, 255, 255),  # 按钮文本颜色
    "font_scale": 0.8,
    "thickness": 4,  # 文本线宽，对中文字体无效
    "reach_threshold": 100,  # 按钮被按下的距离阈值
}

REDO_SEL_CONFIG = {
    "texts": ["重做", "继续"],
    "size": (200, 120),
    "color": (0, 120, 200),
    "text_color": (255, 255, 255),
    "font_scale": 1.2,
    "thickness": 4,
    "reach_threshold": 100,
}


class Selector(Guider):

    # 不调用父类的构造函数，直接写Selector自己的初始化逻辑
    def __init__(self, camera,uuid, win_size=WIN_SIZE, buttons_config=BUTTONS_CONFIG, debug=False):
        # config 配置
        win_topic = "AR太极拳助手"+uuid
        self.win_size = win_size  # 窗口分辨率
        self.frame_rate = 60
        self.buttons_config = buttons_config  # 按钮配置字典

        # path 路径
        # self.std_json_path = paths["标准 JSON 文件路径"]
        # self.std_frame_path = paths["标准掩膜图片路径"]
        # win_bgm_path = paths["背景音乐"]
        # self.differences_json_path = paths["标准 JSON 文件路径"] / ".." / "differences.json"
        # self.user_replay_json_path = paths["标准 JSON 文件路径"] / ".." / "user_replay.json"

        # utils 工具
        self.camera = camera
        self.pose_detector = None
        self.frame_rate_clock = None

        # resource 资源
        # self.std_pose_lists = None
        # self.std_overlay_paths = None
        # self.std_skips = None   # 自动不停播列表（bool）, length = len(std_pose_lists)
        self.real_world_frame = None
        self.rt_pose_list = None
        # self.std_pose_list = None
        # self.rt_landmarks_list = None
        # self.std_landmarks_list = None
        # self.rt_center = None
        # self.std_center = None
        # self.std_overlay = None
        self.canvas = None  # cv2 画布
        self.pygame_surface = None  # pygame 画布
        self.screen = None  # pygame 窗口

        # init 初始化工具
        self.pose_detector_init()
        self.pygame_init(win_topic=win_topic)  # 没有bgm
        self.real_world_frame,real_shape = self.camera.get_camera_processed_frame(
                frame=None,
                win_size=WIN_SIZE
            )
        self.get_buttons_positions(num=len(self.buttons_config["texts"]),real_shape = real_shape)

        # load 初始化加载资源
        # self.clear_difference_json()
        # self.std_pose_lists, self.std_skips, self.std_overlay_paths = self.load_std_resources(self.std_json_path, self.std_frame_path)

        # state 状态
        self.current_std_index = 0
        self.timer = None
        self.conditions = [False] * len(self.buttons_config["texts"])  # 按钮状态列表，是否被按下
        self.selection = None
        self.debug = debug
        self.running = True

    def get_buttons_positions(self, num,real_shape):
        """获取按钮位置"""
        self.buttons_positions = []
        # 按钮水平均分排列，垂直居中
        button_width, button_height = self.buttons_config["size"]
        num_buttons = num
        spacing = real_shape[0] // (num_buttons)
        y = real_shape[1] // 4
        for i in range(num_buttons):
            x = self.win_size[0]//2 - real_shape[0]//2 + (i + 0.5) * spacing 
            self.buttons_positions.append((x, y))

    def main_update(self, frame=None):
        if self.running:

            """处理 Pygame 窗口事件"""
            self.window_events()

            """帧率控制"""
            self.frame_rate_clock.tick(self.frame_rate)

            if self.debug:
                # !测试用，改为 cv2 相机读取帧
                ret, frame = self.camera.read()
                if not ret:
                    self.real_world_frame = None
                else:
                    frame = cv2.resize(frame, self.win_size)
                    self.real_world_frame = cv2.flip(frame, 1)  # 水平翻转
            else:
                """获取、处理实时画面帧"""
                # （已翻转）（已拉伸到窗口分辨率）
                self.real_world_frame,processed_shape = self.camera.get_camera_processed_frame(
                    frame=frame,
                    win_size=self.win_size
                )

            # cv2.imshow("实时画面", self.real_world_frame)  # 调试：显示实时画面
            # sys.stderr.write("实时画面帧已处理\n")

            """主画布渲染"""
            # 获取对齐点列表 std_landmarks_list 和 rt_landmarks_list；
            # 渲染标点、箭头、掩膜到画布
            self.canvas_render(rt_frame=self.real_world_frame,
                               conditions=self.conditions,real_shape = processed_shape)

            """条件判定"""
            # 检查条件是否满足，更新 condition 列表
            self.selection = self.condition_check(conditions=self.conditions,
                                                  button_num=len(self.buttons_config["texts"]),
                                                  button_pos_list=self.buttons_positions,
                                                  threshold=self.buttons_config["reach_threshold"],
                                                  rt_lm_list=self.rt_landmarks_list)

            """绘制 Pygame UI"""
            # 绘制已用时间、招式、实时总得分
            self.pygame_UI_render(canvas=self.canvas, CONFIGS=PYGAME_SELECT_UI_CONFIG)

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

    def main_loop_with_voice(self):
        while self.running:

            if self.selection is not None:
                self.running = False
                # 如果有按钮被按下，跳出循环
                return self.selection

            # 渲染 .screen
            self.main_update()
            # 获取 JPEG 字节数据
            frame_to_web = self.get_transmit_frame(self.screen)
            # 发送 JPEG 数据
            if not self.debug:
                self.send_jpeg_data(frame_to_web)
            # 更新窗口显示
            pygame.display.flip()

            # todo:: 重载：发送音频提示指令
            self.send_voice_command()

    def condition_check(self, conditions, button_num, button_pos_list, threshold, rt_lm_list):
        """
        检查条件是否满足，更新 condition 列表
        :param conditions: 按钮状态列表，是否被按下
        :param button_num: 按钮数量
        :param button_pos_list: 按钮位置列表
        :param threshold: 按钮被按下的距离阈值
        :param rt_lm_list: 实时帧关键点列表
        :return: 按钮索引（如有），否则返回None
        """
        if not rt_lm_list or not button_pos_list:
            conditions[:] = [False] * button_num
            return

        # 遍历每个按钮
        for btn_idx, btn_pos in enumerate(button_pos_list):
            conditions[btn_idx] = False  # 默认未按下
            # 遍历每个关键点
            for lm in rt_lm_list:
                # 计算欧氏距离
                dx = lm[0] - btn_pos[0]
                dy = lm[1] - btn_pos[1]

                distance = (dx ** 2 + dy ** 2) ** 0.5

                if distance <= threshold:
                    conditions[btn_idx] = True
                    # 一旦有关键点满足条件，立即跳出循环
                    break

        # 返回第一个被按下的按钮索引（如有），否则返回None
        for idx, cond in enumerate(conditions):
            if cond:
                return idx
        return None

    def canvas_render(self, rt_frame, conditions,real_shape = None):
        """渲染画布"""
        self.canvas = rt_frame.copy()

        """标准对齐点加载"""
        # self.std_pose_list = self.std_pose_lists[self.current_std_index]  # 标准完整姿态列表，从 lists 中获取 list，格式同上
        # self.std_landmarks_list = self.get_landmarks_list(self.std_pose_list, landmarks=POSE_ALIGN_LANDMARKS)   # 标准关键（对齐）点列表，格式同上
        # self.std_overlay = self.get_current_std_overlay(paths=self.std_overlay_paths, overlay_idx=self.current_std_index)  # 标准帧路径，格式为 str

        """实时对齐点获取"""
        self.rt_pose_list = self.pose_detection(self.real_world_frame)  # 实时完整姿态列表，格式为： [33 * tuple(x, y, z=0)] 或 []
        self.rt_landmarks_list = self.get_landmarks_list(self.rt_pose_list,
                                                         landmarks=POSE_ALIGN_LANDMARKS)  # 实时关键（对齐）点列表，格式为： [4 * int(x, y)] 或 []

        """获取实时躯干位置；获取标准中心标点"""
        # self.rt_center = self.get_center_from_points_2d(self.rt_pose_list, from_pts_idx=RT_PTS_TO_CENTER, win_size=WIN_SIZE, y_offset=STD_CENTER_Y_OFFSET)  # tuple(float, float)
        # self.rt_center = (self.rt_center[0], self.rt_center[1] + BENEATH)   # 参数调整中心点位置，向下偏移 BENEATH 像素
        # self.std_center = (self.std_pose_list[0][0] * STD_SCALE, self.std_pose_list[0][1] * STD_SCALE)  # std_pose_list 的第一个元组是标点中心点 (3d to 2d)

        """将标准对齐点吸附到用户"""
        # self.align_pose_to_target_by_center_2d(self.std_landmarks_list, center=self.std_center, target=self.rt_center, scale=STD_SCALE, win_size=WIN_SIZE)
        # print(self.std_landmarks_list) # 调试

        """叠加掩膜到画布"""
        # self.canvas = (self.canvas * LIGHTNESS).astype(np.uint8)  # 调整画布亮度
        # self.canvas = draw.draw_overlay_centered(self.canvas, self.std_overlay,
        #                                             center=self.std_center, target=self.rt_center,
        #                                             win_size=WIN_SIZE,
        #                                             scale=STD_SCALE,
        #                                             opacity=STD_OVERLAY_OPACITY)  # 在画布上叠加掩膜，掩膜中心点与用户中心点对齐

        """绘制 对齐点 + 按钮 到画布"""
        self.canvas = draw.draw_pose_with_buttons(self.canvas,
                                                  buttons_config=self.buttons_config,
                                                  rt_landmarks_list=self.rt_landmarks_list,
                                                  condition=conditions,real_shape = real_shape)


if __name__ == "__main__":
    import cv2

    camera = cv2.VideoCapture(0)  # 使用 OpenCV 打开摄像头
    selector = Selector(camera=camera, win_size=(1280, 720), debug=1)
    selector.main_loop_with_voice()
    # selector.main_loop()  # 调试：不使用音频提示
    camera.release()
    print(f"选择了{BUTTONS_CONFIG['texts'][selector.selection]}")  # 打印选择的按钮文本