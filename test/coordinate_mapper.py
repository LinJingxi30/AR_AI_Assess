# coordinate_mapper.py
def convert_to_ar_coords(skeleton_points, camera_params):
    """
    将摄像头坐标系转换为AR显示坐标系
    :param skeleton_points: MediaPipe输出的归一化坐标(N,3)
    :param camera_params: 摄像头内参矩阵
    :return: 适用于AR眼镜的3D坐标
    """
    # 坐标系转换公式（需根据实际设备校准）
    ar_points = []
    for point in skeleton_points:
        # 假设摄像头与AR眼镜同坐标系（需实际校准）
        x = (point[0] - 0.5) * 2  # 转换为[-1,1]范围
        y = (0.5 - point[1]) * 2  # Y轴翻转
        z = point[2] * 0.5         # 缩放深度值
        ar_points.append([x, y, z])
    return np.array(ar_points)