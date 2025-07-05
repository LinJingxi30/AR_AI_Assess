import sys
import cv2

def camera_init(source = 0,resolution=(1280, 720)):
    """
    初始化摄像头
    """
    # 获取摄像头 0
    camera = cv2.VideoCapture(source)
    
    # 尝试设置分辨率
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    # 检查分辨率设置是否成功（分辨率不是随意取值，必须按照使用相机的几个固定的分辨率进行选择）
    w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if w != resolution[0] or h != resolution[1]:
        print(f"摄像头分辨率设置失败，当前分辨率：{w}x{h}", file=sys.stderr)

    # 检查摄像头是否打开
    if not camera.isOpened():
        raise RuntimeError("摄像头初始化失败")
    
    return camera

def get_camera_processed_frame(camera=None, frame=None, win_size=None):
    # 外部未传帧
    if frame is None:
        # 拍摄实时画面
        frame = camera_capture(camera=camera)
    # 拉伸到窗口大小并左右翻转
    processed_frame = camera_frame_process(frame=frame, target_reso=win_size)

    if processed_frame is None:
        raise ValueError("实时画面处理失败！")

    return processed_frame

def camera_capture(camera=None):
    """
    获取实时画面帧
    返回实时画面帧
    """
    if camera is not None:
        success, frame = camera.read()
        if not success:
            print("获取实时画面失败：实时帧读取不成功", file=sys.stderr)
            return None
    else:
        print("获取实时画面失败：相机为空", file=sys.stderr)
        return None
    
    return frame

def camera_frame_process(target_reso=None, frame=None):
    """
    处理实时画面帧：翻转 + 等比缩放填充到指定分辨率（contain模式）
    """
    if frame is None:
        raise ValueError("实时帧不能为空")
    if target_reso is None:
        raise ValueError("目标分辨率不能为空")
    
    # 左右翻转画面
    processed_frame = cv2.flip(frame, 1)

    # 获取原始和目标尺寸
    h, w = processed_frame.shape[:2]
    target_w, target_h = target_reso

    # 计算缩放比例，保持比例
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)

    # 等比缩放
    resized = cv2.resize(processed_frame, (new_w, new_h))

    # 计算填充边界
    top = (target_h - new_h) // 2
    bottom = target_h - new_h - top
    left = (target_w - new_w) // 2
    right = target_w - new_w - left

    # 填充黑边
    bordered = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])

    return bordered