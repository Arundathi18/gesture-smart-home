import csv
import os

import cv2
import mediapipe as mp

from gesture_features import GESTURES, landmarks_to_features

DATA_FILE = os.path.join(os.path.dirname(__file__), "gesture_data.csv")

# key to press -> gesture label
KEYS = {ord("n"): "NONE", ord("f"): "FIST", ord("1"): "1", ord("2"): "2", ord("3"): "3", ord("p"): "PALM"}


def load_counts():
    counts = {g: 0 for g in GESTURES}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            for row in csv.reader(f):
                counts[row[0]] += 1
    return counts


def main():
    counts = load_counts()
    recording = None

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.6)
    mp_draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)

    print("Press a key to START recording a gesture, press it again to STOP:")
    print("  1 / 2 / 3 = fingers,  f = fist,  p = open palm,  n = anything else / no gesture")
    print("  q = quit")

    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                frame = cv2.flip(frame, 1)
                result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                if result.multi_hand_landmarks:
                    landmarks = result.multi_hand_landmarks[0]
                    mp_draw.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)
                    if recording:
                        writer.writerow([recording] + list(landmarks_to_features(landmarks)))
                        counts[recording] += 1

                status = f"REC {recording}" if recording else "not recording"
                cv2.putText(frame, status, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255) if recording else (200, 200, 200), 2)
                for i, g in enumerate(GESTURES):
                    cv2.putText(frame, f"{g}: {counts[g]}", (10, 80 + i * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (0, 255, 0), 2)
                cv2.imshow("Collect gesture data", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key in KEYS:
                    recording = None if recording == KEYS[key] else KEYS[key]
        finally:
            cap.release()
            cv2.destroyAllWindows()

    print("Saved samples:", counts)


if __name__ == "__main__":
    main()
