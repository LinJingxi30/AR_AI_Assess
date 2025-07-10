import json
import sys

class DataSender:
    """数据发送工具类，用于处理 Python 到 Node.js 的数据传输"""
    
    @staticmethod
    def send_frame(buffer):
        """发送图像帧数据
        Args:
            buffer: 图像的二进制数据
        """
        header = {
            "type": "image",
            "length": len(buffer)
        }
        sys.stdout.buffer.write(b"---FRAME---\n")
        sys.stdout.buffer.write((json.dumps(header) + "\n").encode('utf-8'))
        sys.stdout.buffer.flush()
        sys.stdout.buffer.write(buffer)
        sys.stdout.flush()

    @staticmethod 
    def send_control(command, **kwargs):
        """发送控制消息
        Args:
            command: 控制命令名称
            **kwargs: 其他控制参数
        """
        header = {
            "type": "control",
            "command": command,
            **kwargs
        }
        sys.stdout.buffer.write(b"---FRAME---\n")
        sys.stdout.buffer.write((json.dumps(header) + "\n").encode('utf-8'))
        sys.stdout.flush()