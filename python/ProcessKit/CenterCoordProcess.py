# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/3/7 14:27
# @Content :
# todo:: 添加以左脚为原点的坐标系？人移动怎么办呢

def move_coords_by_center_to_pos(Pose, to_position, use_ground=True):
    """
    将骨架以中心为基准移动到指定位置
    先将目标与当前中心点做差，再遍历所有坐标减去这个差
    参数：
      Pose: 骨架坐标系，33个关节点的坐标。
      to_position: 移动到的目标位置。
      use_ground: 是否使用脚底坐标作为中心点。

    返回：
      Pose: 移动后的骨架坐标系。
    """
    if use_ground:
        # 使用脚底坐标作为中心点
        center_pos = get_ground_pos(Pose)
    else:
        # 使用骨架躯干作为中心点
        center_pos = get_center_pos(Pose)
    
    # 计算移动距离
    move_x = to_position[0] - center_pos[0]
    move_y = to_position[1] - center_pos[1]
    # move_z = to_position[2] - center_pos[2]
    
    # 对每个关节坐标加上移动距离
    for i in range(len(Pose)):
        Pose[i][0] += move_x
        Pose[i][1] += move_y
        # Pose[i][2] += move_z

    return Pose

def move_coords_by_center_to_pos_set_pts(Pose, pts, to_position, extern_center=None):
    """
    """
    if extern_center is None:
        # 使用规定点集pts计算中心点
        center_pos = get_center_pos_from_pts(pts=pts, Pose=Pose)
        # print("center_pos:", center_pos)
    else:
        # 使用传入的中心点
        center_pos = extern_center

    # 计算移动距离
    move_x = to_position[0] - center_pos[0]
    move_y = to_position[1] - center_pos[1]
    # move_z = to_position[2] - center_pos[2]
    
    # 对每个关节坐标加上移动距离
    for i in range(len(Pose)):
        Pose[i][0] += move_x
        Pose[i][1] += move_y

    return Pose


def get_center_pos_from_pts(pts, Pose):
    count = len(pts)
    # for idx in pts:
        # print("idx:", idx, "Pose[idx]:", Pose[idx])
    sum_x = sum(Pose[idx][0] for idx in pts)
    sum_y = sum(Pose[idx][1] for idx in pts)
    # sum_z = sum(Pose[idx][2] for idx in pts)
    return (sum_x / count, sum_y / count)


def get_center_pos(finalPose):
    # 大致在躯干位置
    # 左髋关节，右髋关节 = 23, 24
    # 左肩关节，右肩关节 = 11, 12
    center_pos = (finalPose[23][0] + finalPose[24][0] + finalPose[11][0] + finalPose[12][0]) / 4, \
                (finalPose[23][1] + finalPose[24][1] + finalPose[11][1] + finalPose[12][1]) / 4
    return center_pos

def get_center_pos3d(finalPose):
    # 大致在躯干位置
    # 左髋关节，右髋关节 = 23, 24
    # 左肩关节，右肩关节 = 11, 12
    center_pos = (finalPose[23][0] + finalPose[24][0] + finalPose[11][0] + finalPose[12][0]) / 4, \
                (finalPose[23][1] + finalPose[24][1] + finalPose[11][1] + finalPose[12][1]) / 4, \
                (finalPose[23][2] + finalPose[24][2] + finalPose[11][2] + finalPose[12][2]) / 4
    return center_pos

def get_ground_pos(finalPose):
    # 两脚中间
    # 左右脚 = 27, 28
    ground_pos = (finalPose[27][0] + finalPose[28][0]) / 2, \
                (finalPose[27][1] + finalPose[28][1]) / 2, \
                (finalPose[27][2] + finalPose[28][2]) / 2
    return ground_pos

def get_Lfoot_pos(finalPose):
    # 左脚
    Lfoot_pos = finalPose[27][0], finalPose[27][1], finalPose[27][2]
    return Lfoot_pos

def coord_relativize(finalPose, use_ground=True):
    if use_ground:
        # 使用脚底坐标作为中心点
        center_pos = get_ground_pos(finalPose)
    else:
        # 使用骨架躯干作为中心点
        center_pos = get_center_pos(finalPose)
    
    # 对每个关节坐标减去中心点坐标, 使骨架中心点为(0, 0, 0)
    for i in range(33):
        finalPose[i][0] -= center_pos[0]
        finalPose[i][1] -= center_pos[1]
        finalPose[i][2] -= center_pos[2]

    # 不用返回center_pos, 因为必为(0, 0, 0)
    return finalPose

# @A last new line here:
