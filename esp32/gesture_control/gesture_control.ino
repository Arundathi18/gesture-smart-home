#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <LiquidCrystal_I2C.h>
#include "secrets.h"  // WIFI_SSID, WIFI_PASSWORD, MQTT_HOST (copy secrets.example.h)

LiquidCrystal_I2C lcd(0x27, 16, 2);  // if blank, try 0x3F

const int relayPin = 18;  // fan relay (active-LOW), fan on hold so it stays off

const int ledPins[3] = {4, 19, 23};
const char *roomNames[3] = {"Living room", "Bedroom", "Kitchen"};
const char *roomKeys[3] = {"living", "bedroom", "kitchen"};  // MQTT topic names
bool ledOn[3] = {false, false, false};

// Topics:
//   home/lights/<room>/set    ON | OFF | TOGGLE   (commands in)
//   home/lights/all/set       ON | OFF
//   home/lights/<room>/state  ON | OFF            (retained, published by this board)
//   home/esp32/status         online | offline    (retained, offline set as last will)
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
unsigned long lastReconnectAttempt = 0;

void showStatus(const char *action) {
  lcd.setCursor(0, 0);
  lcd.printf("L:%-3s B:%-3s K:%-3s", ledOn[0] ? "ON" : "OFF", ledOn[1] ? "ON" : "OFF", ledOn[2] ? "ON" : "OFF");
  lcd.setCursor(0, 1);
  lcd.printf("%-16s", action);
}

void publishState(int i) {
  if (!mqtt.connected()) return;
  char topic[40];
  snprintf(topic, sizeof(topic), "home/lights/%s/state", roomKeys[i]);
  mqtt.publish(topic, ledOn[i] ? "ON" : "OFF", true);
}

void setLed(int i, bool on) {
  ledOn[i] = on;
  digitalWrite(ledPins[i], on ? HIGH : LOW);
  publishState(i);
}

void setRoom(int i, bool on) {
  setLed(i, on);
  char action[17];
  snprintf(action, sizeof(action), "%s %s", roomNames[i], on ? "ON" : "OFF");
  showStatus(action);
}

void setAll(bool on) {
  for (int i = 0; i < 3; i++) setLed(i, on);
  showStatus(on ? "All lights ON" : "All lights OFF");
}

// USB serial fallback: same commands as before (1, 2, 3, FIST, PALM)
void handleSerialCommand(String cmd) {
  if (cmd == "1" || cmd == "2" || cmd == "3") {
    int i = cmd.toInt() - 1;
    setRoom(i, !ledOn[i]);
  } else if (cmd == "FIST") {
    setAll(false);
  } else if (cmd == "PALM") {
    setAll(true);
  }
}

void onMqttMessage(char *topic, byte *payload, unsigned int length) {
  String t = topic;
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  msg.trim();

  if (t == "home/lights/all/set") {
    if (msg == "ON") setAll(true);
    else if (msg == "OFF") setAll(false);
    return;
  }
  for (int i = 0; i < 3; i++) {
    if (t == String("home/lights/") + roomKeys[i] + "/set") {
      if (msg == "ON") setRoom(i, true);
      else if (msg == "OFF") setRoom(i, false);
      else if (msg == "TOGGLE") setRoom(i, !ledOn[i]);
    }
  }
}

bool connectMqtt() {
  if (!mqtt.connect("gesture-home-esp32", "home/esp32/status", 0, true, "offline")) return false;
  mqtt.publish("home/esp32/status", "online", true);
  mqtt.subscribe("home/lights/+/set");
  for (int i = 0; i < 3; i++) publishState(i);
  return true;
}

void setup() {
  Serial.begin(115200);

  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, HIGH);  // fan off

  for (int i = 0; i < 3; i++) {
    pinMode(ledPins[i], OUTPUT);
    setLed(i, false);
  }

  lcd.init();
  lcd.backlight();
  showStatus("WiFi connecting");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  for (int tries = 0; tries < 20 && WiFi.status() != WL_CONNECTED; tries++) delay(500);

  mqtt.setServer(MQTT_HOST, 1883);
  mqtt.setCallback(onMqttMessage);

  if (WiFi.status() == WL_CONNECTED && connectMqtt()) {
    showStatus("Ready (WiFi)");
  } else {
    showStatus("Ready (USB only)");  // keeps retrying in loop()
  }
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    handleSerialCommand(cmd);
  }

  // WiFi reconnects on its own; retry the broker every 5 s without blocking serial
  if (mqtt.connected()) {
    mqtt.loop();
  } else if (WiFi.status() == WL_CONNECTED && millis() - lastReconnectAttempt > 5000) {
    lastReconnectAttempt = millis();
    connectMqtt();
  }
}
