#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);  // if blank, try 0x3F

const int relayPin = 18;  // fan relay (active-LOW), fan on hold so it stays off

const int ledPins[3] = {4, 19, 23};
const char *roomNames[3] = {"Living room", "Bedroom", "Kitchen"};
bool ledOn[3] = {false, false, false};

void showStatus(const char *action) {
  lcd.setCursor(0, 0);
  lcd.printf("L:%-3s B:%-3s K:%-3s", ledOn[0] ? "ON" : "OFF", ledOn[1] ? "ON" : "OFF", ledOn[2] ? "ON" : "OFF");
  lcd.setCursor(0, 1);
  lcd.printf("%-16s", action);
}

void setLed(int i, bool on) {
  ledOn[i] = on;
  digitalWrite(ledPins[i], on ? HIGH : LOW);
}

void handleCommand(String cmd) {
  if (cmd == "1" || cmd == "2" || cmd == "3") {
    int i = cmd.toInt() - 1;
    setLed(i, !ledOn[i]);
    char action[17];
    snprintf(action, sizeof(action), "%s %s", roomNames[i], ledOn[i] ? "ON" : "OFF");
    showStatus(action);
  } else if (cmd == "FIST") {
    for (int i = 0; i < 3; i++) setLed(i, false);
    showStatus("All lights OFF");
  } else if (cmd == "PALM") {
    for (int i = 0; i < 3; i++) setLed(i, true);
    showStatus("All lights ON");
  }
  // anything else (e.g. NONE) leaves the lights as they are
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
  showStatus("Ready");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    handleCommand(cmd);
  }
}
