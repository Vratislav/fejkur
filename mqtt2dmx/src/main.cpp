#include <esp_dmx.h>

// Pin definitions for CTC-DRA-10-R2 shield with Wemos D1 (ESP8266)
#define DMX_DIRECTION_PIN 4 // D2 on Wemos D1 mini, connected to DE/RE (tied together)
// DI (Data In)  -> TX (GPIO1)
// RO (Receiver) -> RX (GPIO3)
// DE/RE         -> D2 (GPIO4)
// A/B           -> DMX bus
// VCC           -> 5V
// GND           -> GND

void setup() {
  dmx_master_enable(DMX_DIRECTION_PIN);
}

void loop() {
  // Test sequence: turn on each channel to full, one at a time
  for (int ch = 0; ch < 4; ch++) {
    // Set all channels to 0
    for (int i = 0; i < 4; i++) {
      dmx_master_write(i, 0);
    }
    // Set current channel to max (255)
    dmx_master_write(ch, 255);
    delay(500);
  }
}