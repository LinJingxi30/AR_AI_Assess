# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/3/7 14:27
# @Content :

def get_center_pos(finalPose):
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
