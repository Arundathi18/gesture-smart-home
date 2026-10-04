import functools
import os
import secrets
import socket
import threading
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import paho.mqtt.client as mqtt

HERE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(HERE, "dashboard")
TOPIC_FILE = os.path.join(HERE, "ntfy_topic.txt")
HTTP_PORT = 8000
ROOM_NAMES = {"living": "Living room", "bedroom": "Bedroom", "kitchen": "Kitchen"}


def local_ip():
    # the address phones on the same WiFi use to reach this Mac
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("192.168.1.1", 80))
        return s.getsockname()[0]


def ntfy_topic():
    # ntfy.sh topics are public, so use a random name that only you know
    if not os.path.exists(TOPIC_FILE):
        with open(TOPIC_FILE, "w") as f:
            f.write(f"gesture-home-{secrets.token_hex(5)}\n")
    with open(TOPIC_FILE) as f:
        return f.read().strip()


def notify(topic, message):
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=message.encode(),
                                 headers={"Title": "Gesture Smart Home", "Tags": "bulb"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except OSError as e:
        print("Notification failed:", e)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the terminal quiet


def serve_dashboard():
    handler = functools.partial(QuietHandler, directory=DASHBOARD_DIR)
    ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), handler).serve_forever()


def main():
    topic = ntfy_topic()
    threading.Thread(target=serve_dashboard, daemon=True).start()

    def on_connect(client, userdata, flags, reason_code, properties):
        client.subscribe("home/lights/+/state")
        client.subscribe("home/esp32/status")

    last = {}

    def on_message(client, userdata, msg):
        payload = msg.payload.decode()
        changed = last.get(msg.topic) != payload
        last[msg.topic] = payload
        # retained = current state replayed on connect; unchanged = the board re-announcing after a reconnect
        if msg.retain or not changed:
            return
        if msg.topic == "home/esp32/status":
            text = "Board is back online" if payload == "online" else "Board went offline"
        else:
            room = ROOM_NAMES.get(msg.topic.split("/")[2], msg.topic)
            text = f"{room} light turned {payload}"
        print(text)
        threading.Thread(target=notify, args=(topic, text), daemon=True).start()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="gesture-home-server")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883)

    print(f"Dashboard:     http://{local_ip()}:{HTTP_PORT}  (open on a phone on the same WiFi)")
    print(f"Notifications: subscribe to \"{topic}\" in the ntfy app (server ntfy.sh)")
    client.loop_forever()


if __name__ == "__main__":
    main()
