# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/3/14 22:49
# @Content : 


def Filter(P, X, Z, jointnum, Q=0.001, R=0.0015, lpf_param=0.1):
    """
    Kalman 滤波器，用于平滑关节点数据。

    参数：
      P: 各个关节点的误差协方差列表（或数组），长度为 jointnum。
      Q: Kalman 过程噪声参数（标量）。
      R: Kalman 测量噪声参数（标量）。
      X: 上一时刻各关节点状态的估计值列表。
      Z: 当前时刻的测量值列表（即 currdata）。

    返回：
      smooth: 平滑后的关节点状态列表。
      updated_P: 更新后的误差协方差列表。
      updated_X: 更新后的状态估计值列表。
    """
    # jointnum = len(P)
    """卡尔曼滤波"""
    smooth, P, X = KalmanFilter(P, X, smooth)

    """低通滤波"""
    LowPassFilter(smooth, lpf_param=lpf_param, times=6)


def KalmanFilter(P, X, Z, jointnum, Q=0.001, R=0.0015):
    """
    Kalman 滤波器，用于平滑关节点数据。

    参数：
      P: 各个关节点的误差协方差列表（或数组），长度为 jointnum。
      Q: Kalman 过程噪声参数（标量）。
      R: Kalman 测量噪声参数（标量）。
      X: 上一时刻各关节点状态的估计值列表。
      Z: 当前时刻的测量值列表（即 currdata）。

    返回：
      smooth: 平滑后的关节点状态列表。
      updated_P: 更新后的误差协方差列表。
      updated_X: 更新后的状态估计值列表。
    """
    # jointnum = len(P)
    """卡尔曼滤波"""
    smooth = [0] * jointnum
    for i in range(jointnum):
        # 计算 Kalman 增益
        K = (P[i] + Q) / (P[i] + Q + R)
        # 更新误差协方差
        P[i] = R * (P[i] + Q) / (P[i] + Q + R)
        # 更新平滑状态
        smooth[i] = X[i] + (Z[i] - X[i]) * K
        # 存储反馈到状态X
        X[i] = smooth[i]
    return smooth, P, X


def LowPassFilter(prev, lpf_param=0.1, times=6):
    prev = prev[0]
    for i in range(1, times):
        prev[i] = prev[i] * lpf_param + prev[i - 1] * (1 - lpf_param)
    return prev[times - 1]

# @A last new line here:
