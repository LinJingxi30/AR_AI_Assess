import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arrow
import random


def draw_circle_with_arrows():
    fig, ax = plt.subplots(figsize=(6, 6))

    # 绘制空心圆
    circle = Circle((0.5, 0.5), 0.4, fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(circle)

    # 定义四种箭头组合及其排列方式
    arrow_options = [
        ("up_down", [(0.4, 0.4, 0, 0.2), (0.6, 0.6, 0, -0.2)]),  # ↑   ↓（左右分开）
        ("down_up", [(0.4, 0.6, 0, -0.2), (0.6, 0.4, 0, 0.2)]),  # ↓   ↑（左右分开）
        ("left_right", [(0.6, 0.6, -0.2, 0), (0.4, 0.4, 0.2, 0)]),  # ←
        # →（上下分开）
        ("right_left", [(0.4, 0.6, 0.2, 0), (0.6, 0.4, -0.2, 0)]),  # →
        # ←（上下分开）
    ]

    # 随机选择一组
    choice = random.choice(arrow_options)
    direction, arrows = choice

    # 绘制两个箭头
    for x, y, dx, dy in arrows:
        arrow = Arrow(x, y, dx, dy, width=0.05, color='red')
        ax.add_patch(arrow)

    # 设置坐标轴
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')

    plt.show()


draw_circle_with_arrows()