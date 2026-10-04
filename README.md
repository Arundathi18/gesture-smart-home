# Gesture Smart Home

Hand gestures in front of a MacBook webcam switch three room lights (LEDs) on an ESP32, with status shown on a 16x2 I2C LCD. A model trained on your own hand recognises the gesture on the Mac and sends a one-line command to the ESP32 over USB serial.

| Gesture | Action |
| --- | --- |
| Index finger | Toggle LED 1 (Living room, GPIO4) |
| Index + middle | Toggle LED 2 (Bedroom, GPIO19) |
| Index + middle + ring | Toggle LED 3 (Kitchen, GPIO23) |
| Fist | All lights off |
| Open palm | All lights on |

## Hardware

ESP32 DOIT DevKit V1, 3 LEDs with 220-330 ohm resistors, 16x2 LCD with I2C backpack (SDA GPIO21, SCL GPIO22), 2-channel relay module (IN1 on GPIO18, reserved for a fan, currently held off).

## Setup

1. Upload `esp32/gesture_control/gesture_control.ino` (Arduino IDE, board "DOIT ESP32 DEVKIT V1", library `LiquidCrystal_I2C`).
2. On the Mac (Python 3.11):
   ```bash
   cd mac
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python3 gesture_control.py
   ```
   Press `q` in the camera window to quit.

## Training the gesture model

`gesture_model.pkl` is trained on one person's hand. To train on yours:

```bash
python3 collect_data.py   # 1/2/3, f (fist), p (palm), n (no gesture) to record; q to quit
python3 train_model.py
```

Without a model file, `gesture_control.py` falls back to simple finger-counting rules.
