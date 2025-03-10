import mediapipe as mp
import cv2

mp_hands = mp.solutions.hands.Hands()
cap = cv2.VideoCapture(1)
while cap.isOpened():
    success, img = cap.read()
    results = mp_hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(img, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
    cv2.imshow("Hands", img)
    cv2.waitKey(1)