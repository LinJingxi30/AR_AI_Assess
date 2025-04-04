import cv2
from cvzone.PoseModule import PoseDetector
from enum import Enum


# 动作方向枚举
class Direction(Enum):
    NONE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


# 手势动作检测器类
class HandMotionDetector:
    def __init__(self, window_size=7, threshold=200):
        """
        初始化手势动作检测器
        :param window_size: 记录历史坐标的窗口大小
        :param threshold: 移动距离阈值(像素)
        """
        self.window_size = window_size
        self.threshold = threshold
        self.left_hand_history = []  # 左手坐标历史
        self.right_hand_history = []  # 右手坐标历史
        self.left_last_direction = Direction.NONE  # 左手上次移动方向
        self.right_last_direction = Direction.NONE  # 右手上次移动方向

    def _get_direction(self, start, end):
        """
        计算两点之间的主要移动方向
        :param start: 起始点(x,y)
        :param end: 结束点(x,y)
        :return: Direction枚举
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # 优先判断垂直方向
        if abs(dy) > abs(dx):
            return Direction.UP if dy < 0 else Direction.DOWN
        else:
            return Direction.LEFT if dx < 0 else Direction.RIGHT

    def _check_direction_change(self, history):
        """
        检查方向变化模式
        :param history: 坐标历史记录
        :return: 检测到的动作描述字符串，若无则返回None
        """
        if len(history) < 2:
            return None

        # 获取最近的两个方向
        dir1 = self._get_direction(history[-2], history[-1])
        dir2 = None
        if len(history) >= 3:
            dir2 = self._get_direction(history[-3], history[-2])

        # 检查方向变化
        if dir2 is not None and dir1 != dir2:
            if dir2 == Direction.DOWN and dir1 == Direction.UP:
                return "先下后上"
            elif dir2 == Direction.UP and dir1 == Direction.DOWN:
                return "先上后下"
            elif dir2 == Direction.RIGHT and dir1 == Direction.LEFT:
                return "先右后左"
            elif dir2 == Direction.LEFT and dir1 == Direction.RIGHT:
                return "先左后右"
        return None

    def update(self, left_hand, right_hand):
        """
        更新手部坐标并检测动作
        :param left_hand: 左手坐标(x,y)或None
        :param right_hand: 右手坐标(x,y)或None
        :return: (左手动作, 右手动作) 若无动作为None
        """
        left_action = None
        right_action = None

        # 更新左手历史
        if left_hand is not None:
            if len(self.left_hand_history) == 0 or \
                    ((left_hand[0] - self.left_hand_history[-1][0]) ** 2 +
                     (left_hand[1] - self.left_hand_history[-1][1]) ** 2) > self.threshold ** 2:
                self.left_hand_history.append(left_hand)
                if len(self.left_hand_history) > self.window_size:
                    self.left_hand_history.pop(0)

                # 检测动作
                left_action = self._check_direction_change(self.left_hand_history)

        # 更新右手历史
        if right_hand is not None:
            if len(self.right_hand_history) == 0 or \
                    ((right_hand[0] - self.right_hand_history[-1][0]) ** 2 +
                     (right_hand[1] - self.right_hand_history[-1][1]) ** 2) > self.threshold ** 2:
                self.right_hand_history.append(right_hand)
                if len(self.right_hand_history) > self.window_size:
                    self.right_hand_history.pop(0)

                # 检测动作
                right_action = self._check_direction_change(self.right_hand_history)

        return left_action, right_action


def main():
    # 摄像头初始化
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：摄像头初始化失败！")
        return

    detector = PoseDetector()
    motion_detector = HandMotionDetector(window_size=7, threshold=80)
    cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)

    while cap.isOpened():
        # 读取实时帧
        success, image = cap.read()
        if not success:
            continue

        # 水平翻转画面
        image = cv2.flip(image, 1)

        # 实时骨架检测
        image = detector.findPose(image, draw=False)
        lmList, _ = detector.findPosition(image, draw=False)

        # 定义手的关节点索引
        left_wrist_idx = 18  # 左手腕
        right_wrist_idx = 17  # 右手腕

        left_hand = None
        right_hand = None

        # 获取手的坐标
        if lmList:
            # 左手坐标
            if len(lmList) > left_wrist_idx:
                left_hand = lmList[left_wrist_idx][0:2]  # 只取x,y坐标
                cv2.circle(image, (int(left_hand[0]), int(left_hand[1])), 10, (0, 255, 0), -1)

            # 右手坐标
            if len(lmList) > right_wrist_idx:
                right_hand = lmList[right_wrist_idx][0:2]  # 只取x,y坐标
                cv2.circle(image, (int(right_hand[0]), int(right_hand[1])), 10, (0, 0, 255), -1)

        # 检测手势动作
        left_action, right_action = motion_detector.update(left_hand, right_hand)

        # 显示检测结果
        if left_action:
            print(f"左手检测到动作: {left_action}")
            cv2.putText(image, f"Left: {left_action}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if right_action:
            print(f"右手检测到动作: {right_action}")
            cv2.putText(image, f"Right: {right_action}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 显示画面
        cv2.imshow("Hand Tracking", image)

        # 按键控制
        key = cv2.waitKey(1)
        if key == 27:  # ESC 键退出
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()