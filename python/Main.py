# from PracticeMode import RPClass
import sys
import cv2
from Config.common_data import WIN_SIZE
from TimedChallengeMode.TimedChallengeClass import TimedChallengeMode
from Starter.SportSelector import StarterClass, get_sport_type
import numpy as np


class MainApp:
    def __init__(self):
        # 初始化摄像头、初始化所有需要的模块
        self.cap = cv2.VideoCapture(0)

        # 维护当前所处状态
        self.mode = "BACKGROUND"
        self.mode_state = "SLECTING_SPORT"
        self.get_game_mode()

        # 创建实例
        self.sport_selcetor = StarterClass()
        self.tc = None
        self.ec = None  # 无尽挑战模式实例

        self.running = True

        self.out_frame = None  # 输出帧
        self.out_score = None  # 输出分数


    def get_game_mode(self):
        # self.mode = receive_from_web()
        self.mode = "TimedChallengeMode"  # 测试
        if self.mode is None:
            self.mode = "BACKGROUND"
        self.mode_state = "SLECTING_SPORT"
    
    def run(self):
        # 从前端读取模式选择
        self.get_game_mode()

        while self.running:
            # 读取摄像头图像
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)  # 镜像翻转

            # 默认背景
            if self.mode == "BACKGROUND":
                # 进入背景模式，显示深蓝色背景 (BGR格式)
                # 假设 WIN_SIZE 是一个 (width, height) 的元组
                self.out_frame = np.full((WIN_SIZE[1], WIN_SIZE[0], 3), (139, 0, 0), dtype=np.uint8)

            # 限时挑战模式
            if self.mode == "TimedChallengeMode":
                # 开始选择曲目
                if self.mode_state == "SLECTING_SPORT":
                    self.sport_selcetor.running = True  # 允许选择曲目
                    sport, self.out_frame = self.sport_selcetor.update(frame)   # 已选择：sport为非空字符串，running置False

                    if sport is not None and self.sport_selcetor.running == False:   # 说明选完了
                        self.tc = TimedChallengeMode(sport_type=sport, challenge_time=500)  # 选完再根据曲目创建运行实例
                        self.mode_state = "PLAYING"  # 进入游戏状态

                # 如果已经选择了曲目，进入游戏状态
                elif self.mode_state == "PLAYING":
                    self.out_frame = self.tc.main_update()  # 游戏中，更新帧
                    
                    # 结束，切换状态
                    if self.tc.running == False:
                        self.mode_state = "MODE_END"  # 模式结束

                # 模式结束，结算分数
                elif self.mode_state == "MODE_END": 
                    # 结算分数
                    self.out_score = self.tc.final_score
                    self.mode = None
                    self.running = False  # 结束游戏

            # 无尽挑战模式

            """统一在pygame窗口中显示"""

            """统一发送画布至前端"""
            if self.out_frame is not None:

                self.out_frame = cv2.resize(self.out_frame, WIN_SIZE) # 确保输出图像大小一致
                self.out_frame = cv2.cvtColor(self.out_frame, cv2.COLOR_BGR2RGB)  # 转换为 RGB 格式
                _, buffer = cv2.imencode('.jpg', self.out_frame) # 编码为 JPG 格式
                sys.stdout.buffer.write(buffer) # 将编码后的数据写入标准输出流
                sys.stdout.flush()  # 刷新输出流

            else:   # 不出意外的话，要出意外了
                self.out_frame = np.full((WIN_SIZE[1], WIN_SIZE[0], 3), (139, 0, 0), dtype=np.uint8)
                self.out_frame = cv2.resize(self.out_frame, WIN_SIZE)
                self.out_frame = cv2.cvtColor(self.out_frame, cv2.COLOR_BGR2RGB)  # 转换为 RGB 格式
                _, buffer = cv2.imencode('.jpg', self.out_frame) # 编码为 JPG 格式
                sys.stdout.buffer.write(buffer) # 将编码后的数据写入标准输出流
                sys.stdout.flush()  # 刷新输出流

            if self.out_score:
                # todo:: 发标志位：完成挑战，得分
                # todo::发送分数到前端
                pass  # Placeholder to avoid syntax error



if __name__ == "__main__":
    
    # 前端接口
    mode = "EndlessChallengeMode"

    """运动种类选择，内含发送"""
    sport = get_sport_type()    #! 后面这里参数控制不同的运动集

    if mode == "TimedChallengeMode":
        running_mode = TimedChallengeMode(sport_type=sport, challenge_time=500)
    elif mode == "EndlessChallengeMode":
        running_mode = EndlessChallengeMode()

    while running_mode.running:
        frame = running_mode.main_update()
        """模式统一发送"""
        _, buffer = cv2.imencode('.jpg', frame, [
            int(cv2.IMWRITE_JPEG_QUALITY), 75,  # 质量系数
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1    # 启用Huffman优化
        ])
        sys.stdout.buffer.write(buffer.tobytes())  # 将编码后的数据写入标准输出流
        sys.stdout.flush()  # 刷新输出流
    