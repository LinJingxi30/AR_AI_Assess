import sys
import cv2
import socket
import numpy as np
import struct
import collections
import time
import threading

class CameraUtil:
    def __init__(self, source=0, resolution=(1280, 720)):
        """
        初始化摄像头或UDP流
        """
        self.is_udp = False
        self.camera = None
        self.udp_sock = None
        self.resolution = resolution
        self._udp_frame_buffer = collections.deque(maxlen=5)
        self._udp_thread = None
        self._udp_thread_stop = threading.Event()

        if isinstance(source, str) and source.upper().startswith("UDP://"):
            addr = source[6:]
            if ':' not in addr:
                raise ValueError("UDP源格式错误，应为 UDP://ip:port")
            ip, port = addr.split(':')
            port = int(port)
            self.udp_sock = self.camera_init_udp(host=ip, port=port)
            self.is_udp = True
            self._udp_thread = threading.Thread(target=self._udp_receiver_thread, daemon=True)
            self._udp_thread.start()
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
        processed_frame,processed_shape = self.camera_frame_process(frame=frame, target_reso=win_size)
        if processed_frame is None:
            raise ValueError("实时画面处理失败！")
        return processed_frame,processed_shape

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

    def _udp_receiver_thread(self):
        sock = self.udp_sock
        max_packet_size = 65536
        timeout = 2.0
        sock.settimeout(timeout)
        frame_chunks = {}
        chunk_count = {}
        frame_id_last = None
        while not self._udp_thread_stop.is_set():
            try:
                data, _ = sock.recvfrom(max_packet_size)
                if len(data) < 8:
                    continue
                header = data[:8]
                frame_id, chunk_idx, total_chunks = struct.unpack('!IHH', header)
                chunk = data[8:]
                if frame_id_last is not None and frame_id != frame_id_last:
                    frame_chunks.clear()
                    chunk_count.clear()
                frame_id_last = frame_id
                frame_chunks[chunk_idx] = chunk
                chunk_count[frame_id] = total_chunks
                if len(frame_chunks) == total_chunks:
                    full_data = b''.join(frame_chunks[i] for i in range(total_chunks))
                    np_data = np.frombuffer(full_data, dtype=np.uint8)
                    frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
                    if frame is not None:
                        self._udp_frame_buffer.append(frame)
                    frame_chunks.clear()
                    chunk_count.clear()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"UDP接收线程异常: {e}", file=sys.stderr)
                continue

    def camera_capture_udp(self, sock=None, timeout=2.0):
        # 直接从缓冲区取最新帧
        start_time = time.time()
        while True:
            if self._udp_frame_buffer:
                return self._udp_frame_buffer.pop()
            if time.time() - start_time > timeout:
                print("UDP流缓冲区取帧超时", file=sys.stderr)
                return None
            time.sleep(0.01)

    def camera_frame_process(self, target_reso=None, frame=None):
        if frame is None:
            raise ValueError("real frame can not be None")
        if target_reso is None:
            raise ValueError("target ")
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
        return bordered,(new_w, new_h)

    def __del__(self):
        # 停止线程
        if hasattr(self, '_udp_thread_stop'):
            self._udp_thread_stop.set()
        if hasattr(self, '_udp_thread') and self._udp_thread is not None:
            self._udp_thread.join(timeout=1)