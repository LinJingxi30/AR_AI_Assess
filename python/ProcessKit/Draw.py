import cv2, numpy as np

import sys, os
from pathlib import Path
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(MEDIA_PIPE_ROOT))
os.chdir(str(MEDIA_PIPE_ROOT))

from Config.common_data import DRAW_SKET_OVERALL_CONFIG, COLOR, WIN_SIZE
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_agg import FigureCanvasAgg

FONT_PATH = "gameAssets/fonts/arial_bold2.otf"
END_SCREEN_IMAGE_PATH = "gameAssets/images/gameover.png"

def convert_frame_to_list(frame):    # to 3*33
    if frame is not None:
        if isinstance(frame, list):
            return frame
        elif isinstance(frame, dict):
            sketList = frame.get("poses", [])
            # 转为 3*33 的列表
            sketList = [sketList[i:i + 3] for i in range(0, len(sketList), 3)]  # 左开右闭
            return sketList
        else:
            raise TypeError("不支持的数据类型！请使用 list 或 dict。")
        

def get_body_part_coord_dict(sketList, keypoints): # from 3*33 to dict
    sketDict = {}
    if list is not None:
        for keyname, keypoint in keypoints.items():
            """样式：sketDict["头部"] = [100, 132] """
            sketDict[keyname] = sketList[keypoint][0:2]  # 部位对应坐标，仅取2d (x, y)
        """自定义部位"""
        sketDict["脖子根"] = (int((sketDict["左肩"][0] + sketDict["右肩"][0]) / 2),
                            int((sketDict["左肩"][1] + sketDict["右肩"][1]) / 2))  # 颈部坐标

        sketDict["左手心"] = (int((sketDict["左手掌"][0] + sketDict["左食指"][0] + sketDict["左小指"][0]) / 3),
                            int((sketDict["左手掌"][1] + sketDict["左食指"][1] + sketDict["左小指"][1]) / 3))  # 计算左手心坐标

        sketDict["右手心"] = (int((sketDict["右手掌"][0] + sketDict["右食指"][0] + sketDict["右小指"][0]) / 3),
                            int((sketDict["右手掌"][1] + sketDict["右食指"][1] + sketDict["右小指"][1]) / 3))
                            
    return sketDict


def draw_connections(canvas, sketDict, connections, color_line, thickness=24):
    if connections and sketDict is not None:
        thickness = int(thickness)  # 确保线条粗细为整数
        for connection in connections.values():     # "脖子": ("头部", "脖子根")
            start_point = tuple(map(int, sketDict[connection[0]]))   # sp = sketDict["头部"]
            end_point = tuple(map(int, sketDict[connection[1]]))     # ep = sketDict["脖子根"]
            cv2.line(canvas, start_point, end_point, color_line, thickness)
    return canvas


def draw_head(canvas, coord, color, radius=64, eye_color=COLOR["white"], mouth_color=COLOR["lightyellow"]):
    radius = int(radius)  # 确保半径为整数
    # 画头部，转换坐标为整数类型
    int_coord = tuple(map(int, coord))
    cv2.circle(canvas, int_coord, radius, color, -1)  # -1表示填充圆形
    # 画眼睛
    eye_radius = int(radius / 4)
    left_eye = (int(coord[0] - eye_radius), int(coord[1] - eye_radius))
    right_eye = (int(coord[0] + eye_radius), int(coord[1] - eye_radius))
    cv2.circle(canvas, left_eye, eye_radius, eye_color, -1)  # 左眼
    cv2.circle(canvas, right_eye, eye_radius, eye_color, -1)  # 右眼
    # 画嘴巴
    mouth_width = int(radius / 2)
    mouth_height = int(radius / 4)
    mouth_center = (int(coord[0]), int(coord[1] + mouth_height))
    cv2.ellipse(canvas, mouth_center, (mouth_width, mouth_height), 0, 0, 180, mouth_color, -1)  # 嘴巴

    return canvas


def draw_key_points(canvas, sketDict, color_point=COLOR["black"], color_head=COLOR["black"], radius=32, radius_head=64):
    if sketDict is not None:
        radius = int(radius)  # 确保半径为整数
        radius_head = int(radius_head)  # 确保头部半径为整数
        for keyname, coord in sketDict.items():
            if keyname == "脖子根" or keyname == "左食指" or keyname == "右食指" or keyname == "左小指" or keyname == "右小指":
                continue
            elif keyname == "左手心" or keyname == "右手心":
                coord = tuple(map(int, coord))
                cv2.circle(canvas, coord, radius, color_point, -1)
            elif keyname == "头部":
                canvas = draw_head(canvas, coord, color=color_head, radius=radius_head)
            else:
                coord = tuple(map(int, coord))  # 转换坐标为整数类型元组
                cv2.circle(canvas, coord, radius, color_point, -1)
    return canvas


def draw_fill_connections(canvas, sketDict, connections, color_fill=COLOR["black"]):
    if connections and sketDict is not None:
        # 遍历待填充块
        for connected_area in connections.values(): # "躯干"
            # 获取连接部位的坐标集
            points = [sketDict[body_part_key] for body_part_key in connected_area]  # ["左肩", "右肩", "左髋", "右髋"]
            # 封闭顶点要按顺逆时针排序
            points_sorted = sorted(points, key=lambda p: (p[0], p[1]))  # 按 x 坐标排序，再按 y 坐标排序
            # 转换为 NumPy 数组
            points_np = np.array(points_sorted, dtype=np.int32)  
            # 填充多边形
            cv2.fillConvexPoly(canvas, points_np, color_fill)  
    return canvas


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

def draw_skeleton(canvas, sket, custom_config=DRAW_SKET_OVERALL_CONFIG):
    # 解析配置
    color_head = custom_config["color_head"]
    color_point = custom_config["color_point"]
    color_line = custom_config["color_line"]
    color_fill = custom_config["color_fill"]
    radius = custom_config["radius"]
    radius_head = custom_config["radius_head"]
    thickness = custom_config["thickness"]
    connections = custom_config["connections"]
    fill_connections = custom_config["fill_connections"]
    key_points = custom_config["key_points"]
    
    # 确保 sket 为 list(3*33)
    sket = convert_frame_to_list(sket)

    # 获取部位坐标字典
    sketDict = get_body_part_coord_dict(sket, keypoints=key_points)

    """绘制填充"""
    canvas = draw_fill_connections(canvas, sketDict, connections=fill_connections, color_fill=color_fill)

    """绘制连接线"""
    canvas = draw_connections(canvas, sketDict, connections=connections, color_line=color_line, thickness=thickness)

    """绘制关键点"""
    canvas = draw_key_points(canvas, sketDict, color_point=color_point, color_head=color_head, radius=radius, radius_head=radius_head)

    return canvas


if __name__ == "__main__":
    while True:
        frame = draw_game_over(score=666)

        cv2.imshow("Game Over", frame)
        if cv2.waitKey(50) & 0xFF == 27:
            break
    cv2.destroyAllWindows()
    
