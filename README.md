# Gesture Smart Home

Hand gestures in front of a MacBook webcam switch three room lights (LEDs) on an ESP32, with status shown on a 16x2 I2C LCD. A model trained on your own hand recognises the gesture on the Mac and sends commands to the ESP32 over WiFi using MQTT (USB serial as a fallback). A phone dashboard shows the live state and can switch rooms, and ntfy sends a phone notification whenever a light changes.

| Gesture | Action |
| --- | --- |
| Index finger | Toggle LED 1 (Living room, GPIO4) |
| Index + middle | Toggle LED 2 (Bedroom, GPIO19) |
| Index + middle + ring | Toggle LED 3 (Kitchen, GPIO23) |
| Fist | All lights off |
| Open palm | All lights on |

## Hardware

ESP32 DOIT DevKit V1, 3 LEDs with 220-330 ohm resistors, 16x2 LCD with I2C backpack (SDA GPIO21, SCL GPIO22), 2-channel relay module (IN1 on GPIO18, reserved for a fan, currently held off).

## How it talks

```
Webcam -> gesture model (Mac) --MQTT--> Mosquitto broker (Mac) --WiFi--> ESP32 -> LEDs, LCD
                                              |  ^
               phone dashboard (WebSockets) --+  +-- ESP32 publishes room state
               ntfy notifications <-- home_server.py
```

| Topic | Payload | Direction |
| --- | --- | --- |
| `home/lights/<living\|bedroom\|kitchen>/set` | `ON`, `OFF`, `TOGGLE` | commands to the board |
| `home/lights/all/set` | `ON`, `OFF` | commands to the board |
| `home/lights/<room>/state` | `ON`, `OFF` (retained) | published by the board |
| `home/esp32/status` | `online`, `offline` (retained, last will) | published by the board |

## Setup

1. **Broker** (Mac): `brew install mosquitto`. Either run it as a service with a WebSockets listener on port 9001 added to its config, or let `start.sh` run it with `mac/mosquitto.conf`.
2. **Firmware**: copy `esp32/gesture_control/secrets.example.h` to `secrets.h` and fill in your WiFi name, password and the Mac's IP (`ipconfig getifaddr en0`). The ESP32 needs a 2.4 GHz network. Upload `gesture_control.ino` (Arduino IDE, board "DOIT ESP32 DEVKIT V1", libraries `LiquidCrystal_I2C` and `PubSubClient`). The LCD shows `Ready (WiFi)` once connected.
3. **Mac** (Python 3.11):
   ```bash
   cd mac
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ./start.sh            # or ./start.sh --serial to use USB instead of WiFi
   ```
   Press `q` in the camera window to quit.
4. **Dashboard**: on a phone on the same WiFi, open `http://<mac-ip>:8000`.
5. **Notifications**: install the ntfy app (iOS or Android) and subscribe to the topic `start.sh` prints (stored in `mac/ntfy_topic.txt`, server ntfy.sh).

## Training the gesture model

`gesture_model.pkl` is trained on one person's hand. To train on yours:

```bash
python3 collect_data.py   # 1/2/3, f (fist), p (palm), n (no gesture) to record; q to quit
python3 train_model.py
```

Without a model file, `gesture_control.py` falls back to simple finger-counting rules.
