import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arrow, Rectangle
import random
import time
from matplotlib.backends.backend_agg import FigureCanvasAgg


class SplitScreenAnimation:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasAgg(self.fig)

        # 左右两侧的活动圆
        self.left_circle = None
        self.right_circle = None

        # 左右两侧已落地的圆(用于闪烁效果)
        self.left_landed_circles = []
        self.right_landed_circles = []

        self.speed = 0.01
        self.last_left_circle_time = time.time()
        self.last_right_circle_time = time.time()
        self.circle_interval = 1.0  # 新圆出现的间隔(秒)
        self.blink_interval = 0.2  # 闪烁间隔(秒)
        self.blink_state = False  # 闪烁状态
        self.last_blink_time = time.time()

        # 屏幕分割线位置 (0-1之间)
        self.divider_pos = 0.5
        self.divider_width = 0.01

    def generate_circle(self, is_left_side):
        # 定义四种箭头组合及其排列方式
        arrow_options = [
            ("up_down", [(0.3, 0.3, 0, 0.2), (0.7, 0.7, 0, -0.2)]),  # ↑   ↓（左右分开）
            ("down_up", [(0.3, 0.7, 0, -0.2), (0.7, 0.3, 0, 0.2)]),  # ↓   ↑（左右分开）
            ("left_right", [(0.7, 0.7, -0.2, 0), (0.3, 0.3, 0.2, 0)]),  # ← →（上下分开）
            ("right_left", [(0.3, 0.7, 0.2, 0), (0.7, 0.3, -0.2, 0)]),  # → ←（上下分开）
        ]

        choice = random.choice(arrow_options)
        direction, arrows = choice

        # 根据所在侧确定x位置范围
        if is_left_side:
            x_pos = random.uniform(0.1, self.divider_pos - 0.1)
        else:
            x_pos = random.uniform(self.divider_pos + 0.1, 0.9)

        return {
            'x': x_pos,
            'y': 1.1,  # 从屏幕上方开始
            'radius': 0.08,
            'arrows': arrows,
            'speed': random.uniform(0.005, 0.015),
            'landed': False,
            'blinking': False,
            'blink_start_time': 0,
            'visible': True,
            'is_left': is_left_side
        }

    def update_circles(self):
        current_time = time.time()

        # 更新闪烁状态
        if current_time - self.last_blink_time > self.blink_interval:
            self.blink_state = not self.blink_state
            self.last_blink_time = current_time

        # 更新左侧圆
        if self.left_circle and not self.left_circle['landed']:
            self.left_circle['y'] -= self.left_circle['speed']
            if self.left_circle['y'] - self.left_circle['radius'] <= 0:  # 检查是否落地
                self.left_circle['landed'] = True
                self.left_circle['blinking'] = True
                self.left_circle['blink_start_time'] = current_time
                self.left_landed_circles.append(self.left_circle)
                self.left_circle = None
                self.last_left_circle_time = current_time

        # 更新右侧圆
        if self.right_circle and not self.right_circle['landed']:
            self.right_circle['y'] -= self.right_circle['speed']
            if self.right_circle['y'] - self.right_circle['radius'] <= 0:  # 检查是否落地
                self.right_circle['landed'] = True
                self.right_circle['blinking'] = True
                self.right_circle['blink_start_time'] = current_time
                self.right_landed_circles.append(self.right_circle)
                self.right_circle = None
                self.last_right_circle_time = current_time

        # 处理正在闪烁的左侧圆
        for circle in self.left_landed_circles[:]:
            if current_time - circle['blink_start_time'] > self.blink_interval * 4:
                self.left_landed_circles.remove(circle)
            else:
                circle['visible'] = self.blink_state

        # 处理正在闪烁的右侧圆
        for circle in self.right_landed_circles[:]:
            if current_time - circle['blink_start_time'] > self.blink_interval * 4:
                self.right_landed_circles.remove(circle)
            else:
                circle['visible'] = self.blink_state

        # 生成新的左侧圆(如果没有活动圆且过了间隔时间)
        if self.left_circle is None and current_time - self.last_left_circle_time > self.circle_interval:
            self.left_circle = self.generate_circle(True)

        # 生成新的右侧圆(如果没有活动圆且过了间隔时间)
        if self.right_circle is None and current_time - self.last_right_circle_time > self.circle_interval:
            self.right_circle = self.generate_circle(False)

    def draw_frame(self):
        # 清空画布
        self.ax.clear()
        self.ax.axis('off')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

        # 获取摄像头帧
        ret, frame = self.cap.read()
        if ret:
            # 将OpenCV BGR格式转换为RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 调整帧大小以适应画布
            frame = cv2.resize(frame, (800, 600))
            # 显示摄像头背景
            self.ax.imshow(frame, extent=[0, 1, 0, 1], alpha=0.7)

        # 绘制分割线
        divider = Rectangle((self.divider_pos - self.divider_width / 2, 0),
                            self.divider_width, 1,
                            facecolor='white', edgecolor='black', linewidth=1)
        self.ax.add_patch(divider)

        # 绘制所有圆形和箭头(包括活动圆和正在闪烁的落地圆)
        circles_to_draw = []
        if self.left_circle:
            circles_to_draw.append(self.left_circle)
        if self.right_circle:
            circles_to_draw.append(self.right_circle)
        circles_to_draw.extend(self.left_landed_circles)
        circles_to_draw.extend(self.right_landed_circles)

        for circle in circles_to_draw:
            if not circle.get('visible', True):
                continue

            # 绘制空心圆
            circ = Circle((circle['x'], circle['y']), circle['radius'],
                          fill=False, edgecolor='black', linewidth=2)
            self.ax.add_patch(circ)

            # 绘制箭头
            for x_rel, y_rel, dx, dy in circle['arrows']:
                # 计算箭头在圆内的绝对位置
                x_abs = circle['x'] + (x_rel - 0.5) * circle['radius'] * 2
                y_abs = circle['y'] + (y_rel - 0.5) * circle['radius'] * 2
                arrow = Arrow(x_abs, y_abs,
                              dx * circle['radius'] * 4,
                              dy * circle['radius'] * 4,
                              width=circle['radius'] * 0.4,
                              color='red')
                self.ax.add_patch(arrow)

        # 渲染Matplotlib图形到numpy数组
        self.canvas.draw()
        img = np.array(self.canvas.renderer.buffer_rgba())
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

        # 水平翻转图像
        img = cv2.flip(img, 1)

        return img

    def run(self):
        try:
            while True:
                self.update_circles()
                frame = self.draw_frame()

                cv2.imshow('Split Screen Falling Circles', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            self.cap.release()
            cv2.destroyAllWindows()


# 运行动画
animation = SplitScreenAnimation()
animation.run()