#!/bin/bash
# Starts the dashboard/notification server and the gesture camera.
# Uses the Mosquitto broker if one is already running (e.g. `brew services start mosquitto`),
# otherwise starts one with mosquitto.conf. Pass --serial to send gestures over USB instead of WiFi.
cd "$(dirname "$0")"
source venv/bin/activate

PIDS=""
if ! lsof -nP -iTCP:1883 -sTCP:LISTEN >/dev/null 2>&1; then
  mosquitto -c mosquitto.conf &
  PIDS="$!"
  sleep 1
fi
python3 -u home_server.py &
PIDS="$PIDS $!"
trap 'kill $PIDS 2>/dev/null' EXIT
sleep 1

python3 gesture_control.py "$@"
