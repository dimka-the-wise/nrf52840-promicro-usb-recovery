/*
 * PROMICRO-USB-RECOVERY-01
 * Board: Pro Micro nRF52840
 * Core: Adafruit nRF52 1.7.0
 * SoftDevice: S140 6.1.1
 *
 * USB Serial diagnostic firmware.
 * No LoRa, BLE, SPI or I2C operations.
 */

#include <Arduino.h>
#include <Adafruit_TinyUSB.h>

void setup() {
  Serial.begin(115200);
}

void loop() {
  static uint32_t lastPrint = 0;

  if (millis() - lastPrint >= 1000) {
    lastPrint = millis();

    if (Serial) {
      Serial.print("PROMICRO-USB-RECOVERY-01 | Uptime: ");
      Serial.print(millis() / 1000);
      Serial.println(" s");
    }
  }
}
