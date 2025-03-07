# skeleton_capture.py
import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose


class RealtimeSkeleton:
    def __init__(self):
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.cap = cv2.VideoCapture(1)

    def get_skeleton(self):
        success, image = self.cap.read()
        if not success: return None, None

        # 镜像处理增强AR沉浸感
        image = cv2.flip(image, 1)
        results = self.pose.process(image)

        if results.pose_landmarks:
            landmarks = self._normalize_landmarks(results.pose_landmarks)
            return image, landmarks
        return image, None

    def _normalize_landmarks(self, landmarks):
        # 转换为归一化坐标（适配不同分辨率）
        return np.array([
            [lm.x, lm.y, lm.z]  # Z值使用MediaPipe的预估相对深度
            for lm in landmarks.landmark
        ], dtype=np.float32)

    def display(self):
        while True:
            image, landmarks = self.get_skeleton()
            if image is None:
                break

            if landmarks is not None:
                for lm in landmarks:
                    x, y = int(lm[0] * image.shape[1]), int(lm[1] * image.shape[0])
                    cv2.circle(image, (x, y), 5, (0, 255, 0), -1)

            cv2.imshow('Skeleton Capture', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    skeleton = RealtimeSkeleton()
    skeleton.display()