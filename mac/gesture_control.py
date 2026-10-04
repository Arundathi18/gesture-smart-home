import argparse
import os
import time

import cv2
import joblib
import mediapipe as mp
import paho.mqtt.client as mqtt
import serial
import serial.tools.list_ports

from gesture_features import landmarks_to_features

STABLE_FRAMES = 8  # frames a gesture must be held before it's sent (~0.3s)
MIN_CONFIDENCE = 0.7  # below this the model's guess is treated as NONE
MODEL_FILE = os.path.join(os.path.dirname(__file__), "gesture_model.pkl")
MQTT_HOST = "localhost"  # the broker runs on this Mac

# gesture -> (topic, payload); the ESP32 owns the light state and does the toggling
MQTT_COMMANDS = {
    "1": ("home/lights/living/set", "TOGGLE"),
    "2": ("home/lights/bedroom/set", "TOGGLE"),
    "3": ("home/lights/kitchen/set", "TOGGLE"),
    "FIST": ("home/lights/all/set", "OFF"),
    "PALM": ("home/lights/all/set", "ON"),
}


def find_esp32_port():
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        if "usb" in p.device.lower() or "wch" in desc or "cp210" in desc or "silicon labs" in desc:
            return p.device
    return None


def open_serial():
    port = find_esp32_port()
    if port is None:
        print("Could not auto-detect the ESP32's serial port. Available ports:")
        for p in serial.tools.list_ports.comports():
            print(" -", p.device, p.description)
        port = input("Enter the port manually (e.g. /dev/cu.usbserial-0001): ").strip()
    ser = serial.Serial(port, 115200, timeout=1)
    time.sleep(2)  # let the ESP32 finish resetting after the serial connection opens
    print(f"Connected to {port}")
    return ser


class MqttSender:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="gesture-camera")
        self.client.connect(MQTT_HOST, 1883)
        self.client.loop_start()
        print(f"Connected to MQTT broker on {MQTT_HOST}")

    def send(self, gesture):
        if gesture in MQTT_COMMANDS:
            self.client.publish(*MQTT_COMMANDS[gesture])

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()


class SerialSender:
    def __init__(self):
        self.ser = open_serial()

    def send(self, gesture):
        self.ser.write((gesture + "\n").encode())

    def close(self):
        self.ser.close()


def fingers_up(landmarks):
    # index, middle, ring, pinky (thumb is ignored, it's unreliable for counting)
    tips = [8, 12, 16, 20]
    joints = [6, 10, 14, 18]
    return [landmarks.landmark[tip].y < landmarks.landmark[joint].y for tip, joint in zip(tips, joints)]


def classify_with_rules(landmarks):
    up = fingers_up(landmarks)
    if not any(up):
        return "FIST"
    if all(up):
        return "PALM"
    if up == [True, False, False, False]:
        return "1"
    if up == [True, True, False, False]:
        return "2"
    if up == [True, True, True, False]:
        return "3"
    return "NONE"


def classify_with_model(model, landmarks):
    probs = model.predict_proba([landmarks_to_features(landmarks)])[0]
    best = probs.argmax()
    return model.classes_[best] if probs[best] >= MIN_CONFIDENCE else "NONE"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", action="store_true", help="send over USB serial instead of MQTT/WiFi")
    args = parser.parse_args()
    sender = SerialSender() if args.serial else MqttSender()

    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
        classify = lambda landmarks: classify_with_model(model, landmarks)
        print("Using trained gesture model")
    else:
        classify = classify_with_rules
        print("No trained model found, using finger-counting rules")

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.6)
    mp_draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    last_sent = None
    candidate = None
    stable_count = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            gesture = "NONE"
            if result.multi_hand_landmarks:
                landmarks = result.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)
                gesture = classify(landmarks)

            cv2.putText(frame, gesture, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Gesture Control", frame)

            # only act once a gesture has been held steady, so passing through
            # 3 -> 2 -> 1 fingers while closing the hand doesn't toggle lights
            if gesture == candidate:
                stable_count += 1
            else:
                candidate = gesture
                stable_count = 1
            if stable_count == STABLE_FRAMES and gesture != last_sent:
                sender.send(gesture)
                last_sent = gesture

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        sender.close()


if __name__ == "__main__":
    main()
