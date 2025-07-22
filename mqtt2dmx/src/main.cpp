
#include <Conceptinetics.h>

#define DMX_CHANNELS 3
#define RXEN_PIN 2
#define HOLD_TIME 10000    // 10 seconds in milliseconds
#define FADE_TIME 3000     // 3 seconds in milliseconds
#define FADE_STEPS 100     // Number of steps for smooth fade

DMX_Master dmx_master(DMX_CHANNELS, RXEN_PIN);

// Track current RGB values
int currentR = 0;
int currentG = 0;
int currentB = 0;

void setup() {
  dmx_master.enable();
}

void fadeToColor(int targetR, int targetG, int targetB) {
  for (int step = 0; step <= FADE_STEPS; step++) {
    int r = map(step, 0, FADE_STEPS, currentR, targetR);
    int g = map(step, 0, FADE_STEPS, currentG, targetG);
    int b = map(step, 0, FADE_STEPS, currentB, targetB);
    
    dmx_master.setChannelValue(1, r);
    dmx_master.setChannelValue(2, g);
    dmx_master.setChannelValue(3, b);
    
    delay(FADE_TIME / FADE_STEPS);
  }
  
  // Update current values
  currentR = targetR;
  currentG = targetG;
  currentB = targetB;
}

void loop() {
  // Red
  fadeToColor(255, 0, 0);
  delay(HOLD_TIME);
  
  // Fade to black
  fadeToColor(0, 0, 0);
  
  // Green
  fadeToColor(0, 255, 0);
  delay(HOLD_TIME);
  
  // Fade to black
  fadeToColor(0, 0, 0);
  
  // Blue
  fadeToColor(0, 0, 255);
  delay(HOLD_TIME);
  
  // Fade to black
  fadeToColor(0, 0, 0);
}
