#include <Arduino.h>
#include <ESPDMX.h>

DMXESPSerial dmx;
uint8_t channel_values[4] = {0, 0, 0, 0};

void setup() {
  Serial.begin(9600);
  while (!Serial) { delay(10); }
  Serial.println("DMX Debug Start");
  dmx.init();
  delay(200);
}

void loop() {
  for (int ch = 1; ch <= 4; ch++) {
    // Set all channels to 0
    for (int i = 1; i <= 4; i++) {
      dmx.write(i, 0);
      channel_values[i-1] = 0;
    }
    // Set current channel to 255
    dmx.write(ch, 255);
    channel_values[ch-1] = 255;
    dmx.update();
    // Debug print
    Serial.print("Cycle: channel ");
    Serial.print(ch);
    Serial.print(" = 255, others = 0 | Values: ");
    for (int i = 0; i < 4; i++) {
      Serial.print("CH");
      Serial.print(i+1);
      Serial.print(":");
      Serial.print(channel_values[i]);
      Serial.print(" ");
    }
    Serial.println();
    delay(500);
  }
}