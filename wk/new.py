from cvzone.PoseModule import PoseDetector
from enum import Enum
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arrow, Rectangle
import random
import time
from matplotlib.backends.backend_agg import FigureCanvasAgg

# 动作方向枚举
class Direction(Enum):
    NONE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

# 手势动作检测器类
class HandMotionDetector:
    def __init__(self, window_size=7, threshold=200):
        self.window_size = window_size
        self.threshold = threshold
        self.left_hand_history = []  # 左手坐标历史
        self.right_hand_history = []  # 右手坐标历史
        self.score = 0  # 初始化得分

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

    def update(self, left_hand, right_hand):
        left_action = None
        right_action = None

        # 更新左手历史
        if left_hand is not None:
            if len(self.left_hand_history) == 0 or \
                    ((left_hand[0] - self.left_hand_history[-1][0]) ** 2 +
                     (left_hand[1] - self.left_hand_history[-1][1]) ** 2) > self.threshold ** 2:
                self.left_hand_history.append(left_hand)
                if len(self.left_hand_history) > self.window_size:
                    self.left_hand_history.pop(0)
                # 检测动作
                left_action = self._check_direction_change(self.left_hand_history)

        # 更新右手历史
        if right_hand is not None:
            if len(self.right_hand_history) == 0 or \
                    ((right_hand[0] - self.right_hand_history[-1][0]) ** 2 +
                     (right_hand[1] - self.right_hand_history[-1][1]) ** 2) > self.threshold ** 2:
                self.right_hand_history.append(right_hand)
                if len(self.right_hand_history) > self.window_size:
                    self.right_hand_history.pop(0)
                # 检测动作
                right_action = self._check_direction_change(self.right_hand_history)

        return left_action, right_action

    def add_score(self):
        self.score += 1  # 增加得分

# 分屏动画类
class SplitScreenAnimation:
    def __init__(self, divider_pos=0.5, divider_width=0.01):
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasAgg(self.fig)

        self.left_circle = None
        self.right_circle = None
        self.left_landed_circles = []
        self.right_landed_circles = []

        self.circle_interval = 1.0
        self.blink_interval = 0.2
        self.blink_duration = 2.0

        self.divider_pos = divider_pos
        self.divider_width = divider_width

        self.last_left_circle_time = time.time()
        self.last_right_circle_time = time.time()

        self.gesture_required_map = {
            "up_down": "先上后下",
            "down_up": "先下后上",
            "left_right": "先左后右",
            "right_left": "先右后左"
        }

    def generate_circle(self, is_left_side):
        arrow_options = [
            ("up_down", [(0.3, 0.3, 0, 0.2), (0.7, 0.7, 0, -0.2)]),
            ("down_up", [(0.3, 0.7, 0, -0.2), (0.7, 0.3, 0, 0.2)]),
            ("left_right", [(0.7, 0.7, -0.2, 0), (0.3, 0.3, 0.2, 0)]),
            ("right_left", [(0.3, 0.7, 0.2, 0), (0.7, 0.3, -0.2, 0)]),
        ]

        choice = random.choice(arrow_options)
        direction, arrows = choice

        if is_left_side:
            x_pos = random.uniform(0.1, self.divider_pos - 0.1)
        else:
            x_pos = random.uniform(self.divider_pos + 0.1, 0.9)

        return {
            'x': x_pos,
            'y': 1.1,
            'radius': 0.08,
            'arrows': arrows,
            'speed': random.uniform(0.005, 0.015),
            'landed': False,
            'color': 'yellow',
            'gesture_required': self.gesture_required_map.get(direction, None),
            'is_left': is_left_side
        }

    def update_circles(self, current_time):
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
            self.left_circle = self.generate_circle(True)

        if self.right_circle is None and (current_time - self.last_right_circle_time > self.circle_interval):
            self.right_circle = self.generate_circle(False)

    def mark_gesture_detected(self, is_left_side, gesture):
        if is_left_side:
            circles = [self.left_circle] if self.left_circle else []
            circles.extend(self.left_landed_circles)
        else:
            circles = [self.right_circle] if self.right_circle else []
            circles.extend(self.right_landed_circles)

        for circle in circles:
            if not circle['landed'] and circle['gesture_required'] == gesture and circle['color'] == 'yellow':
                circle['color'] = 'green'  # 变为绿色
                return True  # 返回True表示检测到有效手势
        return False  # 返回False表示未检测到有效手势

    def draw_frame(self, background_image_rgb, current_time, score):
        self.ax.clear()
        self.ax.axis('off')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

        self.ax.imshow(background_image_rgb, extent=[0, 1, 0, 1], alpha=0.7)

        # 显示得分
        self.ax.text(0.5, 0.95, f"score: {score}", fontsize=15, ha='center', color='black')

        divider = Rectangle((self.divider_pos - self.divider_width / 2, 0),
                            self.divider_width, 1,
                            facecolor='white', edgecolor='black', linewidth=1)
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

            circ = Circle((circle['x'], circle['y']), circle['radius'],
                          fill=False, edgecolor='black', linewidth=2)
            self.ax.add_patch(circ)

            arrow_color = 'green' if circle['color'] == 'green' else 'red' if circle['color'] == 'red' else 'yellow'

            for x_rel, y_rel, dx, dy in circle['arrows']:
                x_abs = circle['x'] + (x_rel - 0.5) * circle['radius'] * 2
                y_abs = circle['y'] + (y_rel - 0.5) * circle['radius'] * 2
                arrow = Arrow(x_abs, y_abs,
                              dx * circle['radius'] * 4,
                              dy * circle['radius'] * 4,
                              width=circle['radius'] * 0.4,
                              color=arrow_color)
                self.ax.add_patch(arrow)

        self.canvas.draw()
        img = np.array(self.canvas.renderer.buffer_rgba())
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

        return img_bgr

    def update_and_draw(self, background_image_rgb, current_time, score):
        self.update_circles(current_time)
        return self.draw_frame(background_image_rgb, current_time, score)

def main():
    animation = SplitScreenAnimation()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：摄像头初始化失败！")
        return

    detector = PoseDetector()
    motion_detector = HandMotionDetector(window_size=7, threshold=200)
    cv2.namedWindow("Hand Tracking and Animation", cv2.WINDOW_NORMAL)

    while True:
        current_time = time.time()
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        image = detector.findPose(image, draw=False)
        lmList, _ = detector.findPosition(image, draw=False)

        left_wrist_idx = 18  # 根据实际情况调整
        right_wrist_idx = 17  # 根据实际情况调整

        left_hand = None
        right_hand = None

        if lmList:
            if len(lmList) > left_wrist_idx and lmList[left_wrist_idx]:
                left_hand = lmList[left_wrist_idx][0:2]
                cv2.circle(image, (int(left_hand[0]), int(left_hand[1])), 10, (0, 255, 0), -1)

            if len(lmList) > right_wrist_idx and lmList[right_wrist_idx]:
                right_hand = lmList[right_wrist_idx][0:2]
                cv2.circle(image, (int(right_hand[0]), int(right_hand[1])), 10, (0, 0, 255), -1)

        left_action, right_action = motion_detector.update(left_hand, right_hand)

        if left_action:
            print(f"左手检测到动作: {left_action}")
            if animation.mark_gesture_detected(True, left_action):
                motion_detector.add_score()  # 增加得分

        if right_action:
            print(f"右手检测到动作: {right_action}")
            if animation.mark_gesture_detected(False, right_action):
                motion_detector.add_score()  # 增加得分

        background_image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        animation_frame = animation.update_and_draw(background_image_rgb, current_time, motion_detector.score)
        cv2.imshow("Hand Tracking and Animation", animation_frame)

        key = cv2.waitKey(1)
        if key == 27:  # ESC 键退出
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
