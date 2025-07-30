import cv2
import socket
import sys
import json
import threading
import argparse
import struct
import time


def split_and_send_camera_to_udp(camera_index=0, n=2, resolution=(1280, 720),
                                 jpeg_quality=40, overlap_width=100, max_packet_size=60000):
    """
    读取本地摄像头，将画面横向切成n份（带重叠区域），分别发送到n个UDP端口。
    参数:
        camera_index: 摄像头索引
        n: 分割份数
        resolution: 分辨率 (width, height)
        jpeg_quality: JPEG压缩质量 (0-100)
        overlap_width: 重叠区域宽度（像素）
    """
    # 分配UDP端口
    udp_ports = []
    for _ in range(n):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        udp_ports.append(port)
        s.close()

    # 输出端口信息
    print(json.dumps({
        "ports": udp_ports,
        "overlap": overlap_width
    }), flush=True)

    print(f"分割摄像头画面：{n}份，重叠宽度={overlap_width}px，UDP端口={udp_ports}")
    print(f"摄像头 index={camera_index}，分辨率={resolution}")

    # 初始化摄像头
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    # 创建UDP socket
    socks = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM) for _ in range(n)]
    udp_targets = [('127.0.0.1', port) for port in udp_ports]

    frame_id = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("摄像头读取失败", file=sys.stderr)
                break

            h, w = frame.shape[:2]
            seg_width = (w + (n - 1) * overlap_width) // n
            seg_height = min(seg_width*720//512, h)

            # 并行发送函数
            def send_segment(seg, sock, target, frame_id):
                try:
                    _, buf = cv2.imencode('.jpg', seg, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    data = buf.tobytes()
                    total_len = len(data)
                    chunk_size = max_packet_size - 8  # 8字节头部
                    total_chunks = (total_len + chunk_size - 1) // chunk_size
                    for idx in range(total_chunks):
                        chunk = data[idx*chunk_size:(idx+1)*chunk_size]
                        # 头部: [frame_id(4字节)][chunk_idx(2字节)][total_chunks(2字节)]
                        header = struct.pack('!IHH', frame_id, idx, total_chunks)
                        sock.sendto(header + chunk, target)
                except Exception as e:
                    print(f"发送失败: {e}", file=sys.stderr)

            threads = []
            for i in range(n):
                x_start = max(0, i * (seg_width - overlap_width))
                x_end = min(w, x_start + seg_width)
                if i == n - 1:
                    x_end = w
                seg = frame[h//2-seg_height//2:h//2+seg_height//2, x_start:x_end]
                t = threading.Thread(
                    target=send_segment,
                    args=(seg, socks[i], udp_targets[i], frame_id)
                )
                t.daemon = True
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            frame_id = (frame_id + 1) % 2**32  # 防止溢出

    finally:
        cap.release()
        for s in socks:
            s.close()
        print("资源已释放")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='摄像头画面分割推流工具')
    parser.add_argument('--camera_index', type=int, default=0, help='摄像头设备索引')
    parser.add_argument('--n', type=int, default=2, help='分割份数')
    parser.add_argument('--resolution', type=str, default='4096x2160', help='分辨率格式: WxH')
    parser.add_argument('--jpeg_quality', type=int, default=80, help='JPEG压缩质量 (0-100)')
    parser.add_argument('--overlap', type=int, default=0, help='重叠区域宽度（像素）')

    args = parser.parse_args()
    resolution = tuple(map(int, args.resolution.split('x'))) if 'x' in args.resolution else (1280, 720)

    split_and_send_camera_to_udp(
        camera_index=args.camera_index,
        n=args.n,
        resolution=resolution,
        jpeg_quality=args.jpeg_quality,
        overlap_width=args.overlap
    )
