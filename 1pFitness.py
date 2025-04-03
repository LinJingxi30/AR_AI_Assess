# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arrow, Rectangle
from matplotlib.backends.backend_agg import FigureCanvasAgg
from cvzone.PoseModule import PoseDetector
from enum import Enum
import random
import time
from matplotlib.font_manager import FontProperties
import pygame
from Config.common_data import WIN_SIZE
from Starter.SportSelector import get_sport_type

# Constants
DPI = 100
FONT_PATH = "gameAssets/fonts/arial_bold2.otf"
END_SCREEN_IMAGE_PATH = "gameAssets/images/tiaowuji_end.png"  # 游戏结束时的背景图片路径

# Direction Enum
class Direction(Enum):
    NONE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class PoseAnimationGame:
    def __init__(self, sport_type):
        self.sport_type = sport_type
        self.detector = PoseDetector()
        self.window_size = 7
        self.threshold = 200
        self.left_hand_history = []
        self.right_hand_history = []
        self.score = 0

        fig_width = WIN_SIZE[0] / DPI
        fig_height = WIN_SIZE[1] / DPI
        self.fig, self.ax = plt.subplots(figsize=(fig_width, fig_height), dpi=DPI, facecolor='black')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.canvas = FigureCanvasAgg(self.fig)

        try:
            self.custom_font = FontProperties(fname=FONT_PATH)
        except:
            print(f"Font loading failed: {FONT_PATH}, using default font")
            self.custom_font = FontProperties()

        self.score_font = {
            'fontsize': 36,
            'fontweight': 'bold',
            'color': 'white',
            'fontproperties': self.custom_font
        }
        self.background_box = {
            'facecolor': 'black',
            'alpha': 0.7,
            'pad': 10,
            'boxstyle': 'round,pad=0.3'
        }

        self.left_circle = None
        self.right_circle = None
        self.left_landed_circles = []
        self.right_landed_circles = []
        self.circle_interval = 1.0
        self.blink_interval = 0.2
        self.blink_duration = 2.0
        self.divider_pos = 0.5
        self.divider_width = 0.01
        self.last_left_circle_time = time.time()
        self.last_right_circle_time = time.time()

        self.gesture_required_map = {
            "up_down": "先上后下",
            "down_up": "先下后上",
            "left_right": "先左后右",
            "right_left": "先右后左"
        }

        # 倒计时相关
        self.start_time = time.time()
        self.duration = 60  # 60秒倒计时
        self.game_over = False

    def _get_direction(self, start, end):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        if abs(dy) > abs(dx):
            return Direction.UP if dy < 0 else Direction.DOWN
        else:
            return Direction.LEFT if dx < 0 else Direction.RIGHT

    def _check_direction_change(self, history):
        if len(history) < 2:
            return None
        dir1 = self._get_direction(history[-2], history[-1])
        dir2 = None
        if len(history) >= 3:
            dir2 = self._get_direction(history[-3], history[-2])
        if dir2 is not None and dir1 != dir2:
            if dir2 == Direction.DOWN and dir1 == Direction.UP:
                return "先下后上"
            elif dir2 == Direction.UP and dir1 == Direction.DOWN:
                return "先上后下"
            elif dir2 == Direction.RIGHT and dir1 == Direction.LEFT:
                return "先右后左"
            elif dir2 == Direction.LEFT and dir1 == Direction.RIGHT:
                return "先左后右"
        return None

    def _update_hands(self, left_hand, right_hand):
        left_action = None
        right_action = None

        if left_hand is not None:
            if len(self.left_hand_history) == 0 or \
                    ((left_hand[0] - self.left_hand_history[-1][0]) ** 2 +
                     (left_hand[1] - self.left_hand_history[-1][1]) ** 2) > self.threshold ** 2:
                self.left_hand_history.append(left_hand)
                if len(self.left_hand_history) > self.window_size:
                    self.left_hand_history.pop(0)
                left_action = self._check_direction_change(self.left_hand_history)

        if right_hand is not None:
            if len(self.right_hand_history) == 0 or \
                    ((right_hand[0] - self.right_hand_history[-1][0]) ** 2 +
                     (right_hand[1] - self.right_hand_history[-1][1]) ** 2) > self.threshold ** 2:
                self.right_hand_history.append(right_hand)
                if len(self.right_hand_history) > self.window_size:
                    self.right_hand_history.pop(0)
                right_action = self._check_direction_change(self.right_hand_history)

        return left_action, right_action

    def _generate_circle(self, is_left_side):
        arrow_options = [
            ("up_down", [(0.3, 0.3, 0, 0.2), (0.7, 0.7, 0, -0.2)]),
            ("down_up", [(0.3, 0.7, 0, -0.2), (0.7, 0.3, 0, 0.2)]),
            ("left_right", [(0.7, 0.7, -0.2, 0), (0.3, 0.3, 0.2, 0)]),
            ("right_left", [(0.3, 0.7, 0.2, 0), (0.7, 0.3, -0.2, 0)]),
        ]
        choice = random.choice(arrow_options)
        direction, arrows = choice
        x_pos = random.uniform(0.1, self.divider_pos - 0.1) if is_left_side else random.uniform(self.divider_pos + 0.1, 0.9)

        return {
            'x': x_pos,
            'y': 1.1,
            'radius': 0.06,
            'arrows': arrows,
            'speed': random.uniform(0.005, 0.015),
            'landed': False,
            'color': 'yellow',
            'gesture_required': self.gesture_required_map.get(direction, None),
            'is_left': is_left_side
        }

    def _update_circles(self, current_time):
        if self.game_over:
            return

        if self.left_circle and not self.left_circle['landed']:
            self.left_circle['y'] -= self.left_circle['speed']
            if self.left_circle['y'] - self.left_circle['radius'] <= 0:
                self.left_circle['landed'] = True
                if self.left_circle['color'] == 'yellow':
                    self.left_circle['color'] = 'red'
                self.left_circle['blink_start_time'] = current_time
                self.left_circle['blinking'] = True
                self.left_landed_circles.append(self.left_circle)
                self.left_circle = None
                self.last_left_circle_time = current_time

        if self.right_circle and not self.right_circle['landed']:
            self.right_circle['y'] -= self.right_circle['speed']
            if self.right_circle['y'] - self.right_circle['radius'] <= 0:
                self.right_circle['landed'] = True
                if self.right_circle['color'] == 'yellow':
                    self.right_circle['color'] = 'red'
                self.right_circle['blink_start_time'] = current_time
                self.right_circle['blinking'] = True
                self.right_landed_circles.append(self.right_circle)
                self.right_circle = None
                self.last_right_circle_time = current_time

        for circle in self.left_landed_circles[:]:
            if not circle.get('blinking', False):
                continue
            elapsed = current_time - circle['blink_start_time']
            if elapsed > self.blink_duration:
                self.left_landed_circles.remove(circle)
            else:
                circle['visible'] = int(elapsed / self.blink_interval) % 2 == 0

        for circle in self.right_landed_circles[:]:
            if not circle.get('blinking', False):
                continue
            elapsed = current_time - circle['blink_start_time']
            if elapsed > self.blink_duration:
                self.right_landed_circles.remove(circle)
            else:
                circle['visible'] = int(elapsed / self.blink_interval) % 2 == 0

        if self.left_circle is None and (current_time - self.last_left_circle_time > self.circle_interval):
            self.left_circle = self._generate_circle(True)

        if self.right_circle is None and (current_time - self.last_right_circle_time > self.circle_interval):
            self.right_circle = self._generate_circle(False)

    def _mark_gesture_detected(self, is_left_side, gesture):
        if self.game_over:
            return False
        circles = ([self.left_circle] if self.left_circle else []) if is_left_side else (
            [self.right_circle] if self.right_circle else [])
        circles.extend(self.left_landed_circles if is_left_side else self.right_landed_circles)
        for circle in circles:
            if not circle['landed'] and circle['gesture_required'] == gesture and circle['color'] == 'yellow':
                circle['color'] = 'green'
                return True
        return False

    def draw_game_over(self):
        """绘制游戏结束画面"""
        # 加载并显示结束画面背景
        end_screen_img = cv2.imread(END_SCREEN_IMAGE_PATH)
        if end_screen_img is not None:
            end_screen_img = cv2.cvtColor(end_screen_img, cv2.COLOR_BGR2RGB)
            end_screen_img = cv2.resize(end_screen_img, WIN_SIZE)
            self.ax.imshow(end_screen_img, extent=[0, 1, 0, 1], aspect='auto')
        else:
            # print(f"无法加载结束画面图片: {END_SCREEN_IMAGE_PATH}")
            self.ax.set_facecolor('black')  # 加载失败时使用黑色背景

        # 显示最终得分
        final_score_text = f"Final Score : {self.score}"
        self.ax.text(0.5, 0.5, final_score_text, ha='center', va='center',
                    fontsize=40, fontweight='bold', color='cyan', fontproperties=self.custom_font)

    def _draw_frame(self, background_image_rgb, current_time, left_hand, right_hand):
        self.ax.clear()
        self.ax.axis('off')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

        # 计算剩余时间
        elapsed_time = current_time - self.start_time
        remaining_time = max(0, self.duration - elapsed_time)
        if remaining_time <= 0:
            self.game_over = True

        if not self.game_over:
            # 游戏进行中，使用摄像头画面作为背景
            self.ax.imshow(background_image_rgb, extent=[0, 1, 0, 1], aspect='auto', alpha=0.8)
            if left_hand is not None:
                self.ax.scatter(left_hand[0] / frame.shape[1], 1 - left_hand[1] / frame.shape[0],
                                s=200, color='cyan', marker='o', alpha=0.7)
            if right_hand is not None:
                self.ax.scatter(right_hand[0] / frame.shape[1], 1 - right_hand[1] / frame.shape[0],
                                s=200, color='magenta', marker='o', alpha=0.7)

            # 显示分数和运动类型
            # print(self.sport_type)
            score_text = f"SCORE; {self.score} - Type; {self.sport_type}"
            self.ax.text(0.5, 0.94, score_text, ha='center', va='center',
                         bbox=dict(facecolor='black', alpha=0.8, edgecolor='white', boxstyle='round,pad=0.5'),
                         fontsize=40, fontweight='bold', color='cyan', fontproperties=self.custom_font)

            # 显示倒计时
            timer_text = f"Time Left: {int(remaining_time)}"
            self.ax.text(0.5, 0.85, timer_text, ha='center', va='center',
                         bbox=dict(facecolor='black', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.3'),
                         fontsize=28, color='yellow', fontproperties=self.custom_font)

            # 绘制进度条
            progress = remaining_time / self.duration
            progress_bar_width = 0.6 * progress
            progress_bar = Rectangle((0.2, 0.80), progress_bar_width, 0.02, facecolor='green', edgecolor='white')
            progress_bar_outline = Rectangle((0.2, 0.80), 0.6, 0.02, fill=False, edgecolor='white')
            self.ax.add_patch(progress_bar_outline)
            self.ax.add_patch(progress_bar)

            # 绘制分隔线和圆圈
            divider = Rectangle((self.divider_pos - self.divider_width / 2, 0), self.divider_width, 1, facecolor='white',
                                edgecolor='black', linewidth=1)
            self.ax.add_patch(divider)

            circles_to_draw = []
            if self.left_circle:
                circles_to_draw.append(self.left_circle)
            if self.right_circle:
                circles_to_draw.append(self.right_circle)
            circles_to_draw.extend(self.left_landed_circles)
            circles_to_draw.extend(self.right_landed_circles)

            for circle in circles_to_draw:
                if circle.get('blinking', False) and not circle.get('visible', True):
                    continue
                circ = Circle((circle['x'], circle['y']), circle['radius'], fill=False, edgecolor='black', linewidth=2)
                self.ax.add_patch(circ)
                arrow_color = 'green' if circle['color'] == 'green' else 'red' if circle['color'] == 'red' else 'yellow'
                for x_rel, y_rel, dx, dy in circle['arrows']:
                    x_abs = circle['x'] + (x_rel - 0.5) * circle['radius'] * 2
                    y_abs = circle['y'] + (y_rel - 0.5) * circle['radius'] * 2
                    arrow = Arrow(x_abs, y_abs, dx * circle['radius'] * 4, dy * circle['radius'] * 4,
                                  width=circle['radius'] * 0.4, color=arrow_color)
                    self.ax.add_patch(arrow)
        else:
            # 游戏结束时调用独立函数
            # self.draw_game_over()
            pass

        self.canvas.draw()
        img = np.array(self.canvas.renderer.buffer_rgba())
        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    def main_update(self, frame):
        current_time = time.time()
        frame = cv2.flip(frame, 1)
        frame = self.detector.findPose(frame, draw=False)
        lmList, _ = self.detector.findPosition(frame, draw=False)

        left_hand = None
        right_hand = None
        if lmList and not self.game_over:
            if len(lmList) > 16 and lmList[16]:
                left_hand = lmList[16][0:2]
            if len(lmList) > 15 and lmList[15]:
                right_hand = lmList[15][0:2]

        if not self.game_over:
            left_action, right_action = self._update_hands(left_hand, right_hand)
            if left_action and self._mark_gesture_detected(True, left_action):
                self.score += 1
                success_sound = pygame.mixer.Sound("gameAssets/sounds/perfect2.wav")
                success_sound.set_volume(1)
                success_sound.play()
            if right_action and self._mark_gesture_detected(False, right_action):
                self.score += 1
                success_sound = pygame.mixer.Sound("gameAssets/sounds/perfect2.wav")
                success_sound.set_volume(1)
                success_sound.play()

        self._update_circles(current_time)
        background_image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self._draw_frame(background_image_rgb, current_time, left_hand, right_hand)


def draw_game_over_222(img_dir=END_SCREEN_IMAGE_PATH, score=0, font=FontProperties(fname=FONT_PATH)):
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


if __name__ == "__main__":
    pygame.mixer.init()
    pygame.mixer.music.load("gameAssets/sounds/timed_bgm.mp3")
    pygame.mixer.music.set_volume(1)
    pygame.mixer.music.play(-1)

    sport_type = get_sport_type(sport_str = ["Battle Ropes", "Dumbbel", "Kettlebell"])

    if sport_type is None:
        print("未选择运动类型，程序退出")
        pygame.mixer.music.stop()
        exit()

    cap = cv2.VideoCapture(0)
    game = PoseAnimationGame(sport_type)

    while True:
        success, frame = cap.read()
        if not success:
            continue
        canvas = game.main_update(frame)
        # canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', canvas, [
            int(cv2.IMWRITE_JPEG_QUALITY), 75,  # 质量系数
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1    # 启用Huffman优化
        ])
        sys.stdout.buffer.write(buffer.tobytes())
        sys.stdout.flush()

        cv2.imshow("Pose Animation Game", canvas)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
            break
    
    # 获取成绩
    score = game.score

    pygame.mixer.music.stop()
    cap.release()
    cv2.destroyAllWindows()

    clock = pygame.time.Clock()
    while True:
        frame = draw_game_over_222(score=score, img_dir="gameAssets\images\\tiaowuji_end.png")
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