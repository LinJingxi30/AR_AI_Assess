import cv2
import socket
import sys
import json
import threading  # 添加并行支持

def split_and_send_camera_to_udp(camera_index=0, n=2, resolution=(1280, 720), jpeg_quality=10):
    """
    读取本地摄像头，将画面横向切成n份，分别发送到n个UDP端口。
    自动分配端口，并通过stdout输出端口信息。
    """
    # 先分配端口并立即释放socket
    udp_ports = []
    for _ in range(n):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        udp_ports.append(port)
        s.close()
    # 输出端口信息到stdout，通知Node.js
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    print(json.dumps(udp_ports), flush=True)
    print(f"分割摄像头画面：{n}份，目标UDP端口={udp_ports}")
    print(f"打开摄像头 index={camera_index}，分辨率={resolution}")
    print("开始推流")
    # 重新创建n个socket用于推流
    socks = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM) for _ in range(n)]
    udp_targets = [('127.0.0.1', port) for port in udp_ports]
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("摄像头读取失败", file=sys.stderr)
                break
            h, w = frame.shape[:2]
            seg_w = w // n
            # 并行发送函数
            def send_segment(seg, sock, target):
                try:
                    _, buf = cv2.imencode('.jpg', seg, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    data = buf.tobytes()
                    sock.sendto(data, target)
                except Exception as e:
                    print(f"发送失败: {e}", file=sys.stderr)

            threads = []
            for i in range(n):
                x1 = i * seg_w
                x2 = (i + 1) * seg_w if i < n - 1 else w
                seg = frame[:, x1:x2]
                
                # 为每个片段创建发送线程
                t = threading.Thread(
                    target=send_segment, 
                    args=(seg, socks[i], udp_targets[i])
                )
                t.daemon = True  # 设为守护线程
                t.start()
                threads.append(t)
            
            # 等待所有发送线程完成
            for t in threads:
                t.join()
    finally:
        cap.release()
        for s in socks:
            s.close()
        print("摄像头和UDP socket已关闭")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera_index', type=int, default=0)
    parser.add_argument('--n', type=int, default=2)
    parser.add_argument('--resolution', type=str, default='1280x720')
    parser.add_argument('--jpeg_quality', type=int, default=60)
    args = parser.parse_args()

    n = args.n
    camera_index = args.camera_index
    if 'x' in args.resolution:
        w, h = map(int, args.resolution.split('x'))
        resolution = (w, h)
    else:
        resolution = (1280, 720)
    split_and_send_camera_to_udp(
        camera_index=camera_index,
        n=n,
        resolution=resolution,
        jpeg_quality=args.jpeg_quality
    )