import sys
import pygame
from cvzone.PoseModule import PoseDetector
from enum import Enum
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arrow, Rectangle
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties
from Config.common_data import WIN_SIZE  # 例如 WIN_SIZE = (640, 480)
import random
import time
import threading
import queue

from Starter.SportSelector import get_sport_type
from ProcessKit import Draw

DPI = 100
FONT_PATH = "gameAssets/fonts/arial_bold2.otf"  # 自定义字体路径
END_SCREEN_IMAGE_PATH = "gameAssets/images/gameover_a.png"

# 初始化pygame音效系统
pygame.init()
pygame.mixer.init()
SOUND_VOLUME = 1  # 全局音量设置

# 加载音效和背景音乐
success_sound = pygame.mixer.Sound("gameAssets/sounds/perfect2.wav")
background_music = "gameAssets/sounds/timed_bgm.mp3"

# 动作方向枚举
class Direction(Enum):
    NONE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

# 手势动作检测器类（较简单版本）
class HandMotionDetector:
    def __init__(self, window_size=7, threshold=200):
        self.window_size = window_size
        self.threshold = threshold
        self.left_hand_history = []
        self.right_hand_history = []
        self.player1_score = 0  # 左侧玩家得分
        self.player2_score = 0  # 右侧玩家得分

    def _get_direction(self, start, end):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        if abs(dy) > abs(dx):
            return "先上后下" if dy > 0 else "先下后上"
        else:
            return "先左后右" if dx > 0 else "先右后左"

    def _check_direction_change(self, history):
        if len(history) < 2:
            return None
        dir1 = self._get_direction(history[-2], history[-1])
        dir2 = None
        if len(history) >= 3:
            dir2 = self._get_direction(history[-3], history[-2])
        if dir2 is not None and dir1 != dir2:
            return dir1
        return None

    def update(self, left_hand, right_hand):
        left_action = None
        right_action = None
        if left_hand is not None:
            if len(self.left_hand_history) == 0 or ((left_hand[0] - self.left_hand_history[-1][0])**2 +
                                                    (left_hand[1] - self.left_hand_history[-1][1])**2) > self.threshold**2:
                self.left_hand_history.append(left_hand)
                if len(self.left_hand_history) > self.window_size:
                    self.left_hand_history.pop(0)
                left_action = self._check_direction_change(self.left_hand_history)
        if right_hand is not None:
            if len(self.right_hand_history) == 0 or ((right_hand[0] - self.right_hand_history[-1][0])**2 +
                                                     (right_hand[1] - self.right_hand_history[-1][1])**2) > self.threshold**2:
                self.right_hand_history.append(right_hand)
                if len(self.right_hand_history) > self.window_size:
                    self.right_hand_history.pop(0)
                right_action = self._check_direction_change(self.right_hand_history)
        return left_action, right_action

    def add_score(self, is_left):
        if is_left:
            self.player1_score += 1
        else:
            self.player2_score += 1

# 分屏动画类（使用Matplotlib绘制）
class SplitScreenAnimation:
    def __init__(self, is_left_side=True):
        # 每个画布尺寸为 WIN_SIZE 宽度的一半
        fig_width = WIN_SIZE[0] / 2 / DPI
        fig_height = WIN_SIZE[1] / DPI
        self.fig, self.ax = plt.subplots(figsize=(fig_width, fig_height), dpi=DPI, facecolor='black')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.canvas = FigureCanvasAgg(self.fig)
        try:
            self.custom_font = FontProperties(fname=FONT_PATH)
        except:
            print(f"字体加载失败: {FONT_PATH}, 使用默认字体", file=sys.stderr)
            self.custom_font = FontProperties()
        self.score_font = {'fontsize': 36, 'fontweight': 'bold', 'color': 'white', 'fontproperties': self.custom_font}
        self.background_box = {'facecolor': 'black', 'alpha': 0.7, 'pad': 10, 'boxstyle': 'round,pad=0.3'}
        
        self.is_left_side = is_left_side
        self.circle = None
        self.landed_circles = []
        self.circle_interval = 1.0
        self.blink_interval = 0.2
        self.blink_duration = 2.0
        self.last_circle_time = time.time()
        
        self.gesture_required_map = {
            "up_down": "先上后下",
            "down_up": "先下后上",
            "left_right": "先左后右",
            "right_left": "先右后左"
        }

    def _generate_circle(self):
        arrow_options = [
            ("up_down", [(0.3, 0.3, 0, 0.2), (0.7, 0.7, 0, -0.2)]),
            ("down_up", [(0.3, 0.7, 0, -0.2), (0.7, 0.3, 0, 0.2)]),
            ("left_right", [(0.7, 0.7, -0.2, 0), (0.3, 0.3, 0.2, 0)]),
            ("right_left", [(0.3, 0.7, 0.2, 0), (0.7, 0.3, -0.2, 0)]),
        ]
        choice = random.choice(arrow_options)
        direction, arrows = choice
        x_pos = random.uniform(0.1, 0.9)
        return {
            'x': x_pos,
            'y': 1.1,
            'radius': 0.06,
            'arrows': arrows,
            'speed': random.uniform(0.005, 0.015),
            'landed': False,
            'color': 'yellow',
            'gesture_required': self.gesture_required_map.get(direction, None)
        }

    def _update_circles(self, current_time):
        if self.circle and not self.circle['landed']:
            self.circle['y'] -= self.circle['speed']
            if self.circle['y'] - self.circle['radius'] <= 0:
                self.circle['landed'] = True
                if self.circle['color'] == 'yellow':
                    self.circle['color'] = 'red'
                self.circle['blink_start_time'] = current_time
                self.circle['blinking'] = True
                self.landed_circles.append(self.circle)
                self.circle = None
                self.last_circle_time = current_time

        for circle in self.landed_circles[:]:
            if not circle.get('blinking', False):
                continue
            elapsed = current_time - circle['blink_start_time']
            if elapsed > self.blink_duration:
                self.landed_circles.remove(circle)
            else:
                circle['visible'] = int(elapsed / self.blink_interval) % 2 == 0

        if self.circle is None and (current_time - self.last_circle_time > self.circle_interval):
            self.circle = self._generate_circle()

    def _mark_gesture_detected(self, is_left_side, gesture):
        circles = [self.circle] if self.circle else []
        circles.extend(self.landed_circles)
        for circle in circles:
            if not circle['landed'] and circle['gesture_required'] == gesture and circle['color'] == 'yellow':
                circle['color'] = 'green'  # 触发后变为浅绿色
                return True
        return False

    def _draw_frame(self, background_image_rgb, current_time, left_hand, right_hand, score):
        self.ax.clear()
        self.ax.axis('off')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

        self.ax.imshow(background_image_rgb, extent=[0, 1, 0, 1], aspect='auto', alpha=0.8)
        # 绘制左右手检测点（假设背景图尺寸与摄像头匹配）
        h, w, _ = background_image_rgb.shape
        if left_hand is not None:
            self.ax.scatter(left_hand[0]/w, 1 - left_hand[1]/h, s=200, color='cyan', marker='o', alpha=0.7)
        if right_hand is not None:
            self.ax.scatter(right_hand[0]/w, 1 - right_hand[1]/h, s=200, color='magenta', marker='o', alpha=0.7)

        # 根据当前实例是否为左侧来显示对应玩家得分
        if self.is_left_side:
            score_text = f"PLAYER1: {score}"
        else:
            score_text = f"PLAYER2: {score}"
        self.ax.text(0.5, 0.92, score_text, ha='center', va='center',
                     bbox=self.background_box, **self.score_font)

        # 绘制中间分隔线（在整体合成时，分隔线由外部统一绘制）
        # 绘制动画圆和箭头
        circles_to_draw = []
        if self.circle:
            circles_to_draw.append(self.circle)
        circles_to_draw.extend(self.landed_circles)
        for circle in circles_to_draw:
            if circle.get('blinking', False) and not circle.get('visible', True):
                continue
            circ = Circle((circle['x'], circle['y']), circle['radius'], fill=False,
                          edgecolor='black', linewidth=3)
            self.ax.add_patch(circ)
            arrow_color = 'green' if circle['color'] == 'green' else 'red' if circle['color'] == 'red' else 'gold'
            for x_rel, y_rel, dx, dy in circle['arrows']:
                x_abs = circle['x'] + (x_rel - 0.5) * circle['radius'] * 2
                y_abs = circle['y'] + (y_rel - 0.5) * circle['radius'] * 2
                arrow = Arrow(x_abs, y_abs, dx * circle['radius'] * 4, dy * circle['radius'] * 4,
                              width=circle['radius'] * 0.4, color=arrow_color)
                self.ax.add_patch(arrow)

        self.canvas.draw()
        img = np.array(self.canvas.renderer.buffer_rgba())
        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    def update_and_draw(self, background_image_rgb, current_time, left_hand, right_hand, score):
        self._update_circles(current_time)
        return self._draw_frame(background_image_rgb, current_time, left_hand, right_hand, score)



def draw_game_over(img_dir=END_SCREEN_IMAGE_PATH, score=0, font=FontProperties(fname=FONT_PATH)):
    """绘制游戏结束画面"""
    WIN_WIDTH, WIN_HEIGHT = WIN_SIZE
    fig, axes = plt.subplots(figsize=(WIN_WIDTH/100, WIN_HEIGHT/100), dpi=100)  # 按实际窗口尺寸设置
    canvas = FigureCanvasAgg(fig)
    axes.axis('off')  # 关闭坐标轴
    axes.set_xlim(0, 1)
    # 去白边
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    end_screen_img = cv2.imread(img_dir)
    # 加载并显示结束画面背景
    if end_screen_img is not None:
        end_screen_img = cv2.resize(end_screen_img, WIN_SIZE)
        end_screen_img = cv2.cvtColor(end_screen_img, cv2.COLOR_BGR2RGB)
        end_screen_img = cv2.resize(end_screen_img, WIN_SIZE)
        axes.imshow(end_screen_img, extent=[0, 1, 0, 1], aspect='auto')
    else:
        # print(f"无法加载结束画面图片: {END_SCREEN_IMAGE_PATH}")
        axes.set_facecolor('black')  # 加载失败时使用黑色背景

    # 显示最终得分
    final_score_text = f"Final Score ; {score}"
    axes.text(0.5, 0.5, final_score_text, ha='center', va='center',
                     bbox=dict(facecolor='black', alpha=0.8, edgecolor='white', boxstyle='round,pad=0.5'),
                     fontsize=40, fontweight='bold', color='cyan', fontproperties=font)
    # 转为cv2格式
    canvas.draw()
    img = np.array(canvas.buffer_rgba())
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    return img

# 主程序：双人模式——左右画面分别采集右手（均使用关键点索引16），左右拼接显示
def main(time_duration=30):
    cv2.namedWindow("Hand Tracking and Animation", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Hand Tracking and Animation", WIN_SIZE[0], WIN_SIZE[1])
    
    pygame.mixer.music.load(background_music)
    pygame.mixer.music.set_volume(SOUND_VOLUME)
    pygame.mixer.music.play(-1)
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIN_SIZE[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WIN_SIZE[1])
    
    # 初始化左右分别的PoseDetector和动画模块，以及共用的手势检测器
    detector_left = PoseDetector()
    detector_right = PoseDetector()
    animation_left = SplitScreenAnimation(is_left_side=True)
    animation_right = SplitScreenAnimation(is_left_side=False)
    motion_detector = HandMotionDetector()
    
    start_time = time.time()

    while True:
        current_time = time.time()

        time_spend = current_time - start_time
        if time_spend >= time_duration:
            break

        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        mid = w // 2
        
        # 分割左右画面
        left_frame = frame[:, :mid].copy()
        right_frame = frame[:, mid:].copy()
        
        # 左侧处理：使用 detector_left 检测姿态，提取右手（假设右手关键点索引为16）
        left_frame = detector_left.findPose(left_frame, draw=False)
        left_lmList, _ = detector_left.findPosition(left_frame, draw=False)
        left_hand = None
        if left_lmList is not None and len(left_lmList) > 16:
            left_hand = left_lmList[15][0:2]
            cv2.circle(left_frame, (int(left_hand[0]), int(left_hand[1])), 10, (0, 255, 0), -1)
        
        # 右侧处理：使用 detector_right 检测姿态，提取右手（同样使用关键点索引16）
        right_frame = detector_right.findPose(right_frame, draw=False)
        right_lmList, _ = detector_right.findPosition(right_frame, draw=False)
        right_hand = None
        if right_lmList is not None and len(right_lmList) > 16:
            right_hand = right_lmList[15][0:2]
            cv2.circle(right_frame, (int(right_hand[0]), int(right_hand[1])), 10, (0, 255, 0), -1)
        
        # 更新手势检测（左右分别更新）
        left_action, _ = motion_detector.update(left_hand, None)
        _, right_action = motion_detector.update(None, right_hand)
        
        if left_action:
            print(f"左侧检测到动作: {left_action}", file=sys.stderr)
            if animation_left._mark_gesture_detected(True, left_action):
                motion_detector.add_score(True)
                success_sound.set_volume(SOUND_VOLUME)
                success_sound.play()
        if right_action:
            print(f"右侧检测到动作: {right_action}", file=sys.stderr)
            if animation_right._mark_gesture_detected(False, right_action):
                motion_detector.add_score(False)
                success_sound.set_volume(SOUND_VOLUME)
                success_sound.play()
        
        # 将左右画面转换为RGB，用于Matplotlib渲染
        left_rgb = cv2.cvtColor(left_frame, cv2.COLOR_BGR2RGB)
        right_rgb = cv2.cvtColor(right_frame, cv2.COLOR_BGR2RGB)
        
        left_anim_frame = animation_left.update_and_draw(left_rgb, current_time, left_hand, None, motion_detector.player1_score)
        right_anim_frame = animation_right.update_and_draw(right_rgb, current_time, None, right_hand, motion_detector.player2_score)
        
        # 拼接左右动画帧为一个整体，并在中间绘制分隔线
        combined_frame = cv2.hconcat([left_anim_frame, right_anim_frame])
        mid_x = combined_frame.shape[1] // 2
        cv2.line(combined_frame, (mid_x, 0), (mid_x, combined_frame.shape[0]), (255, 255, 255), 3)

        # 显示剩余时间
        remain_time = int(time_duration - time_spend)
        cv2.putText(combined_frame, f"remain time: {remain_time}s", (combined_frame.shape[1]//2 - 100, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        """发送"""
        # frame = cv2.cvtColor(combined_frame, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', combined_frame, [
            int(cv2.IMWRITE_JPEG_QUALITY), 75,  # 质量系数
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1    # 启用Huffman优化
        ])
        sys.stdout.buffer.write(buffer.tobytes())
        sys.stdout.flush()

        cv2.imshow("Hand Tracking and Animation", combined_frame)
        cv2.resizeWindow("Hand Tracking and Animation", WIN_SIZE[0], WIN_SIZE[1])
        
        if cv2.waitKey(1) & 0xFF == 27:
            break

    final_score = motion_detector.player1_score, motion_detector.player2_score
    pygame.mixer.music.stop()
    cap.release()
    cv2.destroyAllWindows()
    return final_score




if __name__ == "__main__":
    """选运动器材"""
    sport = get_sport_type(sport_str = ["Battle Ropes", "Dumbbel", "Kettlebell"])

    """主"""
    final_score = main()

    """结算"""
    clock = pygame.time.Clock()
    # 获取成绩
    scores_str = f"\nPlayer 1: {final_score[0]}pts;\n Player 2: {final_score[1]}pts !"
    



    while True:
        frame = draw_game_over(score=scores_str, img_dir="gameAssets\images\\tiaowuji_end.png")
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