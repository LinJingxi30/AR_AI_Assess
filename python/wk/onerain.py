import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arrow
import random
import time
from matplotlib.backends.backend_agg import FigureCanvasAgg


class FallingCircleAnimation:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasAgg(self.fig)
        self.circles = []
        self.speed = 0.01
        self.last_circle_time = time.time()
        self.circle_interval = 1.0  # 新圆出现的间隔(秒)
        self.active_circle = None  # 当前活动的圆
        self.blink_state = False  # 闪烁状态
        self.last_blink_time = time.time()
        self.blink_interval = 0.2  # 闪烁间隔(秒)
        self.blink_count = 0  # 闪烁计数

    def generate_circle(self):
        # 定义四种箭头组合及其排列方式
        arrow_options = [
            ("up_down", [(0.3, 0.3, 0, 0.2), (0.7, 0.7, 0, -0.2)]),  # ↑   ↓（左右分开）
            ("down_up", [(0.3, 0.7, 0, -0.2), (0.7, 0.3, 0, 0.2)]),  # ↓   ↑（左右分开）
            ("left_right", [(0.7, 0.7, -0.2, 0), (0.3, 0.3, 0.2, 0)]),  # ← →（上下分开）
            ("right_left", [(0.3, 0.7, 0.2, 0), (0.7, 0.3, -0.2, 0)]),  # → ←（上下分开）
        ]

        choice = random.choice(arrow_options)
        direction, arrows = choice

        # 随机x位置(0.1到0.9之间)
        x_pos = random.uniform(0.1, 0.9)

        return {
            'x': x_pos,
            'y': 1.1,  # 从屏幕上方开始
            'radius': 0.1,
            'arrows': arrows,
            'speed': random.uniform(0.005, 0.015),
            'landed': False,
            'blinking': False,
            'blink_times': 0
        }

    def update_circles(self):
        current_time = time.time()

        # 更新闪烁状态
        if current_time - self.last_blink_time > self.blink_interval:
            self.blink_state = not self.blink_state
            self.last_blink_time = current_time

        # 如果有活动圆，更新它的位置
        if self.active_circle is not None and not self.active_circle['landed']:
            self.active_circle['y'] -= self.active_circle['speed']

            # 检查是否落地
            if self.active_circle['y'] - self.active_circle['radius'] <= 0:
                self.active_circle['landed'] = True
                self.active_circle['blinking'] = True
                self.active_circle['blink_start_time'] = current_time

        # 处理正在闪烁的圆
        for circle in self.circles[:]:
            if circle['blinking']:
                if current_time - circle['blink_start_time'] > self.blink_interval * 4:  # 闪烁两次(开闭各算一次)
                    if circle == self.active_circle:
                        self.active_circle = None
                    self.circles.remove(circle)
                    self.last_circle_time = current_time  # 重置计时器
                elif self.blink_state:
                    circle['visible'] = True
                else:
                    circle['visible'] = False

        # 如果没有活动圆且过了间隔时间，生成新圆
        if self.active_circle is None and current_time - self.last_circle_time > self.circle_interval:
            self.active_circle = self.generate_circle()
            self.active_circle['visible'] = True
            self.circles.append(self.active_circle)
            self.last_circle_time = current_time

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

        # 绘制所有圆和箭头
        for circle in self.circles:
            if not circle.get('visible', True):  # 如果不可见则跳过绘制
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
                arrow = Arrow(x_abs, y_abs, dx * circle['radius'] * 4, dy * circle['radius'] * 4,
                              width=circle['radius'] * 0.4, color='red')
                self.ax.add_patch(arrow)

        # 渲染Matplotlib图形到numpy数组
        self.canvas.draw()
        img = np.array(self.canvas.renderer.buffer_rgba())
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

        return img

    def run(self):
        try:
            while True:
                self.update_circles()
                frame = self.draw_frame()

                cv2.imshow('Falling Circles with Arrows', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            self.cap.release()
            cv2.destroyAllWindows()


# 运行动画
animation = FallingCircleAnimation()
animation.run()