import json
import cv2
from Config.common_data import POSE_CONNECTIONS
from Config.common_data import COLOR
from ProcessKit import CenterCoordProcess as ccp

"""
Json2PreviewClass.py 库介绍

方法：
    get_json_frames(frames, json_dir)：从json文件中读取帧数据
    draw_pose_at_pos(canvas, frame, center_pos, color_point, color_line, radius, thickness, connections)：在指定位置绘制骨架
    draw_pose(canvas, frame, color_point, color_line, radius, thickness, connections)：在默认位置绘制骨架
    draw_preview_area(canvas, moving_sket_coords, do_it_sket_coords, moving_color_point, moving_color_line, moving_radius, moving_thickness, do_it_color_point, do_it_color_line, do_it_radius, do_it_thickness, connections)：绘制预览区域
类：
    CoordsGenerator：坐标生成器
    PreviewCoordsGenerator：预览坐标生成器
"""


def get_scaled_coords(pose_list, scale):
    """
    :param pose_list: 骨架坐标列表
    :param scale: 缩放比例
    :param center_pos: 中心点坐标
    :return: 缩放后的坐标列表
    """
    scaled_coords = []
    for point in pose_list:
        point[0] = int(float(point[0]) * scale)
        point[1] = int(float(point[1]) * scale)
    #     scaled_coords.append([x, y, pose_list[i + 2]])  # 添加置信度
    # return scaled_coords


# 从frame或frames中获取最大身高
def get_frame_max_height(frame):
    if frame and len(frame['poses']) > 0:
        pose = frame['poses']
        y_coords = [pose[i + 1] for i in range(0, len(pose), 3)]
        max_height = max(y_coords) - min(y_coords)
        return max_height


def get_json_frames(frames, json_dir):
    """
    从json文件中读取帧数据
    :param frames: 帧数据列表
    :param json_dir: json文件路径
    frames格式：字典列表，每个字典包含time和poses两个键值对
    frames = [
        {
            'frame_idx': 0,  # 帧索引
            'time': 0.0,  # 时间（毫秒）
            'poses': [x1, y1, c1, x2, y2, c2, ...],  # 坐标列表
        },
        ...
    ]
    """
    with open(json_dir, 'r') as f:
        for line in f:
            data = json.loads(line)
            frame_idx = int(data['ID'])
            time_ms = float(data['time_ms'])  # 转换为毫秒
            poses = [(p) for p in data['poses'] if p] #逻辑存疑
            frames.append({'frame_idx': frame_idx, 'time': time_ms, 'poses': poses})


# todo:: 坐标移动逻辑修改（使用ccp.move_coords_by_center_to_pos，先将目标与当前中心点做差，再遍历所有坐标减去这个差）（原本直接加上坐标，易出现重复位移）
def draw_pose_at_pos_in_scale(canvas, frame_type, pose, scale, at_position, color_point, color_line, radius, thickness, connections = POSE_CONNECTIONS, use_ground=False):
    """
    :param center_pos: 骨架中心指定位置
    :param connections: 骨架连接关系
    :param canvas: 画布
    :param frame: 要绘制的坐标
    :param scale: 缩放比例
    :param color_point: 节点颜色
    :param color_line:  连线颜色
    :param radius:  节点半径
    :param thickness:   连线粗细
    """
    if at_position is None:
        at_position_ = [0, 0]

    # 传入帧类型
    if frame_type == 'dict':
        # 处理字典类型
        if pose and len(pose['poses']) > 0:
            pose = pose['poses']
            pose = [pose[i:i+3] for i in range(0, len(pose), 3)]
    if pose:
        if at_position:
            # 移动骨架到指定位置，pose此时为二维列表，每个元素类似 [x, y, score]
            pose = ccp.move_coords_by_center_to_pos(pose, at_position, use_ground=use_ground)
        # 图层：先画连线，再画关键点
        for (i, j) in connections:
            if i < len(pose) and j < len(pose):
                pt1 = (int(pose[i][0] * scale), int(pose[i][1] * scale))
                pt2 = (int(pose[j][0] * scale), int(pose[j][1] * scale))
                cv2.line(canvas, pt1, pt2, color_line, thickness)

        for point in pose:
            x, y = int(point[0] * scale), int(point[1] * scale)
            cv2.circle(canvas, (x, y), radius, color_point, -1)


def better_draw_pos_scale(canvas, frame_type, pose, scale, at_position, color_point, color_line, radius, thickness, connections=POSE_CONNECTIONS, use_ground=True):
    # 定义关键点与连接规则
    key_points = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 31, 32]
    connections = [
        (11, 12), (11, 23), (11, 13),  # 11与12、23、13相连
        (13, 15),  # 13与15相连
        (12, 24), (12, 14),  # 12与11、24、14相连
        (16, 14),  # 16与14相连
        (23, 24), (23, 25),  # 23与24、25相连
        (24, 26),  # 24与23、26相连
        (26, 28),  # 26与28相连
        (23, 25),  # 23与25相连
        (25, 27),  # 25与27相连
        (31, 27),  # 31与27相连
        (32, 28)   # 32与28相连
    ]

    # 传入帧类型
    if frame_type == 'dict':
        # 处理字典类型
        if len(pose['poses']) > 0:
            pose = pose['poses']
            pose = [pose[i:i+3] for i in range(0, len(pose), 3)]

    if pose:
        # at_position 决定是否使用指定位置绘制
        if at_position:
            # 先移动整个骨架到指定位置
            pose = ccp.move_coords_by_center_to_pos(pose, at_position, use_ground=use_ground)

        # 步骤2：绘制连接线
        for (start_idx, end_idx) in connections:
            if start_idx < len(pose) and end_idx < len(pose):
                # 先对坐标进行缩放
                scaled_start_x = pose[start_idx][0] * scale
                scaled_start_y = pose[start_idx][1] * scale
                scaled_end_x   = pose[end_idx][0] * scale
                scaled_end_y   = pose[end_idx][1] * scale

                cv2.line(canvas,
                         (int(scaled_start_x), int(scaled_start_y)),
                         (int(scaled_end_x), int(scaled_end_y)),
                         (0, 0, 0), thickness)

        # 连接关键点0与关键点11和12中点（先缩放）
        if len(pose) > 12:
            scaled_pt0  = (pose[0][0] * scale,  pose[0][1] * scale)
            scaled_pt11 = (pose[11][0] * scale, pose[11][1] * scale)
            scaled_pt12 = (pose[12][0] * scale, pose[12][1] * scale)
            mid_x = int((scaled_pt11[0] + scaled_pt12[0]) / 2)
            mid_y = int((scaled_pt11[1] + scaled_pt12[1]) / 2)
            cv2.line(canvas,
                     (int(scaled_pt0[0]), int(scaled_pt0[1])),
                     (mid_x, mid_y),
                     (0, 0, 0), thickness)

        # 绘制关键点（不同部位设置不同样式）
        for idx in key_points:
            if idx < len(pose):
                # 先缩放
                scaled_x = pose[idx][0] * scale
                scaled_y = pose[idx][1] * scale
                x, y = int(scaled_x), int(scaled_y)
                if idx == 0:  # 头部
                    cv2.circle(canvas, (x, y), 25, (0, 0, 0), -1)
                elif idx in [15, 16]:  # 双手
                    cv2.circle(canvas, (x, y), 13, (0, 0, 0), -1)
                elif idx in [27, 28, 31, 32]:  # 双脚及新增点
                    cv2.circle(canvas, (x, y), 13, (0, 0, 0), -1)
                else:  # 其他节点
                    cv2.circle(canvas, (x, y), radius, (0, 0, 0), -1)


def draw_pose_at_pos(canvas, frame, center_pos, color_point, color_line, radius, thickness, connections = POSE_CONNECTIONS):
    """
    :param connections: 骨架连接关系
    :param canvas: 画布
    :param frame: 要绘制的坐标
    :param color_point: 节点颜色
    :param color_line:  连线颜色
    :param radius:  节点半径
    :param thickness:   连线粗细
    :param center_pos:  骨架中心指定位置
    """
    if frame and len(frame['poses']) > 0:
        pose = frame['poses']
        # 图层：先画线，再画点
        for (i, j) in connections:
            if i * 3 + 2 < len(pose) and j * 3 + 2 < len(pose):
                pt1 = (int(pose[i * 3] + center_pos[0]), int(pose[i * 3 + 1] + center_pos[1]))
                pt2 = (int(pose[j * 3] + center_pos[0]), int(pose[j * 3 + 1] + center_pos[1]))
                cv2.line(canvas, pt1, pt2, color_line, thickness)

        for i in range(0, len(pose), 3):
            x, y = int(pose[i] + center_pos[0]), int(pose[i + 1] + center_pos[1])
            cv2.circle(canvas, (x, y), radius, color_point, -1)


def draw_pose(canvas, frame, color_point, color_line, radius, thickness, connections = POSE_CONNECTIONS):
    """
    :param connections: 骨架连接关系
    :param canvas: 画布
    :param frame: 要绘制的坐标
    :param color_point: 节点颜色
    :param color_line:  连线颜色
    :param radius:  节点半径
    :param thickness:   连线粗细
    """
    if frame['poses']is not None and len(frame['poses']) > 0:
        pose = frame['poses']
        # 图层：先画线，再画点
        for (i, j) in connections:
            if i * 3 + 2 < len(pose) and j * 3 + 2 < len(pose):
                pt1 = (int(pose[i * 3]), int(pose[i * 3 + 1]))
                pt2 = (int(pose[j * 3]), int(pose[j * 3 + 1]))
                cv2.line(canvas, pt1, pt2, color_line, thickness)

        for i in range(0, len(pose), 3):
            x, y = int(pose[i]), int(pose[i + 1])
            cv2.circle(canvas, (x, y), radius, color_point, -1)


# scale或许可以移动到draw_pose函数中
def draw_preview_area(canvas,
                      moving_sket_coords,
                      do_it_sket_coords,
                      moving_color_point = COLOR['blue'],
                      moving_color_line = COLOR['babyblue'],
                      moving_radius = 8,
                      moving_thickness = 5,
                      do_it_color_point = COLOR['yellow'],
                      do_it_color_line = COLOR['lightyellow'],
                      do_it_radius = 8,
                      do_it_thickness = 5,
                      connections = POSE_CONNECTIONS):
    draw_pose(canvas, moving_sket_coords, moving_color_point, moving_color_line, moving_radius, moving_thickness, connections)
    draw_pose(canvas, do_it_sket_coords, do_it_color_point, do_it_color_line, do_it_radius, do_it_thickness, connections)
    
    # frames = []
    # get_json_frames(frames)


class CoordsGenerator:
    def __init__(self, center_pos_start, center_pos_end, s_frame_num):
        self.center_pos_start = center_pos_start
        self.center_pos_end = center_pos_end
        self.x_prog = 0
        self.y_prog = 0
        self.x_speed = (center_pos_end[0] - center_pos_start[0]) / s_frame_num
        self.y_speed = (center_pos_end[1] - center_pos_start[1]) / s_frame_num

    def get_sket_coords(self, frame, scale):
        if frame and len(frame['poses']) > 0:
            pose = frame['poses'].copy()  # 创建副本避免污染原始数据
            for i in range(0, len(pose), 3):
                # x
                pose[i] = int(pose[i] * scale + self.center_pos_start[0])
                pose[i] += int(self.x_prog)
                # y
                pose[i + 1] = int(pose[i + 1] * scale + self.center_pos_start[1])
                pose[i + 1] += int(self.y_prog)

            self.x_prog += self.x_speed
            self.y_prog += self.y_speed

            return pose

    def reset(self):
        self.x_prog = 0
        self.y_prog = 0


class PreviewCoordsGenerator:

    def __init__(self, preview_start_center_pos, preview_end_center_pos, preview_time, fps, current_idx, frames, scale=1):
        self.moving_sket_coords = {'poses': []}
        self.do_it_sket_coords = {'poses': []}
        self.moving_frame = None
        self.do_it_frame = None
        self.frames = frames
        self.current_idx = current_idx
        self.preview_time = preview_time
        self.fps = fps
        self.scale = scale
        self.s_frame_num = int(self.preview_time * self.fps)
        self.moving_sket_coords_generator = CoordsGenerator(preview_start_center_pos, preview_end_center_pos, self.s_frame_num)
        self.do_it_sket_coords_generator = CoordsGenerator(preview_end_center_pos, preview_end_center_pos, 1)
        self.max_height_json = 0
        self.max_height_current = 0


    def get_preview_coords_only(self, current_idx, current_frame):   # current_frame改由外部传入
        future_s_idx = min((current_idx + self.s_frame_num), len(self.frames) - 1)    # 未来s秒的帧索引
        
        # current_frame = self.frames[current_idx]
        future_s_frame = self.frames[future_s_idx]

        # 获取预览坐标最大身高
        const_height = 300
        self.max_height_json = max(get_frame_max_height(future_s_frame), self.max_height_json)
        self.max_height_current = max(get_frame_max_height(current_frame), self.max_height_current)
        scale_json = const_height / self.max_height_json
        scale_current = const_height / self.max_height_current
        

        # 每隔 s_frame_num 帧采样一次（也就是每隔preview秒）
        if current_idx % self.s_frame_num == 0:
            # 只在采样时更新帧
            self.moving_frame = future_s_frame
            self.do_it_frame = current_frame
            self.moving_sket_coords_generator.reset()  # 重置状态（prog）

        # 滑动的预览小人（小蓝） 坐标处理
        # 小蓝的帧即为采样的未来帧
        self.moving_sket_coords['poses'] = self.moving_sket_coords_generator.get_sket_coords(self.moving_frame, scale_json)

        # “你做出了这个动作！”（小黄） 坐标处理
        # 小黄的帧即为采样的当前帧
        self.do_it_sket_coords['poses'] = self.do_it_sket_coords_generator.get_sket_coords(self.do_it_frame, scale_current)

        return self.moving_sket_coords, self.do_it_sket_coords


