import sys
import cv2
import socket
import numpy as np

class CameraUtil:
    def __init__(self, source=0, resolution=(1280, 720)):
        """
        初始化摄像头或UDP流
        """
        self.is_udp = False
        self.camera = None
        self.udp_sock = None
        self.resolution = resolution

        if isinstance(source, str) and source.upper().startswith("UDP://"):
            addr = source[6:]
            if ':' not in addr:
                raise ValueError("UDP源格式错误，应为 UDP://ip:port")
            ip, port = addr.split(':')
            port = int(port)
            self.udp_sock = self.camera_init_udp(host=ip, port=port)
            self.is_udp = True
        elif isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
            self.camera = self.camera_init(source=int(source), resolution=resolution)
            self.is_udp = False
        else:
            self.camera = self.camera_init(source=source, resolution=resolution)
            self.is_udp = False

    def camera_init(self, source=0, resolution=(1280, 720)):
        camera = cv2.VideoCapture(source)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if w != resolution[0] or h != resolution[1]:
            print(f"摄像头分辨率设置失败，当前分辨率：{w}x{h}", file=sys.stderr)
        if not camera.isOpened():
            raise RuntimeError("摄像头初始化失败")
        return camera

    def camera_init_udp(self, host='0.0.0.0', port=5000, bufsize=65536):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, bufsize)
        return sock

    def get_camera_processed_frame(self, frame=None, win_size=None):
        if frame is None:
            if self.is_udp and self.udp_sock is not None:
                frame = self.camera_capture_udp(sock=self.udp_sock)
            else:
                frame = self.camera_capture(camera=self.camera)
        processed_frame = self.camera_frame_process(frame=frame, target_reso=win_size)
        if processed_frame is None:
            raise ValueError("实时画面处理失败！")
        return processed_frame

    def camera_capture(self, camera=None):
        if camera is None:
            camera = self.camera
        if camera is not None:
            success, frame = camera.read()
            if not success:
                print("获取实时画面失败：实时帧读取不成功", file=sys.stderr)
                return None
        else:
            print("获取实时画面失败：相机为空", file=sys.stderr)
            return None
        return frame

    def camera_capture_udp(self, sock=None, max_packet_size=65536, timeout=2.0):
        if sock is None:
            sock = self.udp_sock
        sock.settimeout(timeout)
        try:
            data, _ = sock.recvfrom(max_packet_size)
            np_data = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
            if frame is None:
                print("UDP流帧解码失败", file=sys.stderr)
            return frame
        except socket.timeout:
            print("UDP流接收超时", file=sys.stderr)
            return None

    def camera_frame_process(self, target_reso=None, frame=None):
        if frame is None:
            raise ValueError("实时帧不能为空")
        if target_reso is None:
            raise ValueError("目标分辨率不能为空")
        processed_frame = cv2.flip(frame, 1)
        h, w = processed_frame.shape[:2]
        target_w, target_h = target_reso
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(processed_frame, (new_w, new_h))
        top = (target_h - new_h) // 2
        bottom = target_h - new_h - top
        left = (target_w - new_w) // 2
        right = target_w - new_w - left
        bordered = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        return bordered