#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Temporary sketch: reads the buck converter's output through a voltage
// divider so it can be set to 12V without a multimeter.

LiquidCrystal_I2C lcd(0x27, 16, 2);  // if blank, try 0x3F

const int sensePin = 34;        // ADC1, input-only
const int relayPin = 18;
const float R_TOP = 10000.0;    // resistor from buck OUT+ to GPIO34
const float R_BOTTOM = 2200.0;  // resistor from GPIO34 to GND

void setup() {
  Serial.begin(115200);
  analogSetPinAttenuation(sensePin, ADC_11db);

  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, HIGH);  // keep relay (fan) off

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Buck voltmeter");
}

void loop() {
  uint32_t sum = 0;
  for (int i = 0; i < 64; i++) sum += analogReadMilliVolts(sensePin);
  float pinVolts = sum / 64.0 / 1000.0;
  float volts = pinVolts * (R_TOP + R_BOTTOM) / R_BOTTOM;

  Serial.printf("%.2f V\n", volts);
  lcd.setCursor(0, 1);
  lcd.printf("Out: %5.2f V   ", volts);
  delay(300);
}
