
#include <Arduino.h>

// DMX configuration for Arduino R4
#define DMX_TX_PIN 1      // Serial1 TX (D1)
#define DMX_DE_PIN 2      // Direction Enable for MAX485
#define DMX_CHANNELS 512  // Number of DMX channels

// DMX timing constants (microseconds)
#define DMX_BREAK_TIME 92     // 92μs break (DMX512-A standard)
#define DMX_MAB_TIME 12       // 12μs mark after break
#define DMX_FRAME_RATE 40     // 40Hz frame rate
#define DMX_FRAME_TIME 25000  // 25ms = 40Hz

// DMX data buffer (512 channels + start code)
uint8_t dmxData[DMX_CHANNELS] = {0};

// Timing variables
unsigned long lastFrameTime = 0;
unsigned long frameCount = 0;

// Fade state variables
bool isFading = false;
int fadeStep = 0;
int fadeTargetR = 0, fadeTargetG = 0, fadeTargetB = 0;
int fadeStartR = 0, fadeStartG = 0, fadeStartB = 0;

// Current RGB values
int currentR = 0;
int currentG = 0;
int currentB = 0;

#define HOLD_TIME 10000    // 10 seconds in milliseconds
#define FADE_TIME 3000     // 3 seconds in milliseconds
#define FADE_STEPS 100     // Number of steps for smooth fade

// Set DMX channel value
void setDMXChannel(uint16_t channel, uint8_t value) {
    if (channel >= 1 && channel <= DMX_CHANNELS) {
        dmxData[channel - 1] = value;
    }
}

// Send DMX break signal
void sendDMXBreak() {
    // Disable Serial1 temporarily
    Serial1.end();
    
    // Configure pin for manual control
    pinMode(DMX_TX_PIN, OUTPUT);
    
    // Generate break signal (92μs LOW)
    digitalWrite(DMX_TX_PIN, LOW);
    delayMicroseconds(DMX_BREAK_TIME);
    
    // Mark after break (12μs HIGH)
    digitalWrite(DMX_TX_PIN, HIGH);
    delayMicroseconds(DMX_MAB_TIME);
    
    // Re-enable Serial1 for data transmission
    Serial1.begin(250000, SERIAL_8N2);
}

// Send complete DMX frame
void sendDMXFrame() {
    frameCount++;
    
    // Enable MAX485 driver
    digitalWrite(DMX_DE_PIN, HIGH);
    
    // Send break and mark-after-break
    sendDMXBreak();
    
    // Send start code (0x00)
    Serial1.write((uint8_t)0x00);
    
    // Send all 512 channels
    for (int i = 0; i < DMX_CHANNELS; i++) {
        Serial1.write((uint8_t)dmxData[i]);
    }
    
    // Wait for transmission to complete
    Serial1.flush();
    
    // Disable MAX485 driver
    digitalWrite(DMX_DE_PIN, LOW);
    
    // Debug output every 100 frames
    if (frameCount % 100 == 0) {
        Serial.print("Sent frame #");
        Serial.print(frameCount);
        Serial.print(" RGB(");
        Serial.print(currentR);
        Serial.print(",");
        Serial.print(currentG);
        Serial.print(",");
        Serial.print(currentB);
        Serial.println(")");
    }
}

// Start fade to color (non-blocking)
void startFadeToColor(int targetR, int targetG, int targetB) {
    fadeStartR = currentR;
    fadeStartG = currentG;
    fadeStartB = currentB;
    fadeTargetR = targetR;
    fadeTargetG = targetG;
    fadeTargetB = targetB;
    fadeStep = 0;
    isFading = true;
    
    // Don't update DMX channels here - let updateFade() handle it
    // This prevents immediate color change before fade starts
    
    Serial.print("Starting fade to RGB(");
    Serial.print(targetR);
    Serial.print(",");
    Serial.print(targetG);
    Serial.print(",");
    Serial.print(targetB);
    Serial.println(")");
}

// Update fade (non-blocking)
void updateFade() {
    if (!isFading) return;
    
    unsigned long currentTime = millis();
    static unsigned long fadeStartTime = 0;
    
    if (fadeStartTime == 0) {
        fadeStartTime = currentTime;
    }
    
    unsigned long fadeElapsed = currentTime - fadeStartTime;
    
    if (fadeElapsed >= FADE_TIME) {
        // Fade complete
        currentR = fadeTargetR;
        currentG = fadeTargetG;
        currentB = fadeTargetB;
        isFading = false;
        fadeStartTime = 0;
        
        // Update DMX channels to final values
        setDMXChannel(1, currentR);
        setDMXChannel(2, currentG);
        setDMXChannel(3, currentB);
        
        Serial.println("Fade complete");
    } else {
        // Continue fade - use linear interpolation for consistent speed
        float progress = (float)fadeElapsed / (float)FADE_TIME;
        int r = fadeStartR + (int)((fadeTargetR - fadeStartR) * progress);
        int g = fadeStartG + (int)((fadeTargetG - fadeStartG) * progress);
        int b = fadeStartB + (int)((fadeTargetB - fadeStartB) * progress);
        
        // Only update if values changed
        if (r != currentR || g != currentG || b != currentB) {
            currentR = r;
            currentG = g;
            currentB = b;
            
            setDMXChannel(1, r);
            setDMXChannel(2, g);
            setDMXChannel(3, b);
        }
    }
}

void setup() {
    // Initialize USB Serial for debug output
    Serial.begin(115200);
    while (!Serial) { delay(10); }
    Serial.println("Arduino R4 DMX Start");
    
    // Initialize DMX pins
    pinMode(DMX_DE_PIN, OUTPUT);
    digitalWrite(DMX_DE_PIN, LOW);  // Disable driver initially
    
    // Initialize Serial1 for DMX (250k baud, 8N2)
    Serial1.begin(250000, SERIAL_8N2);
    
    Serial.println("DMX hardware initialized");
    Serial.println("Serial1: 250k baud, 8N2");
    Serial.println("Break: 92μs, MAB: 12μs");
    
    // Start with black and fade to red
    currentR = 0;
    currentG = 0;
    currentB = 0;
    setDMXChannel(1, 0);
    setDMXChannel(2, 0);
    setDMXChannel(3, 0);
    
    // Don't start fade immediately - let it start in the loop
    // startFadeToColor(255, 0, 0);
}

void loop() {
    // Send DMX frame at 40Hz
    unsigned long currentTime = millis();
    if (currentTime - lastFrameTime >= 25) { // 40Hz = 25ms
        sendDMXFrame();
        lastFrameTime = currentTime;
    }
    
    // Update fade (non-blocking)
    updateFade();
    
    // State machine for color sequence
    static int state = -1; // Start at -1 to handle initial state
    static unsigned long stateStartTime = 0;
    
    if (!isFading) {
        unsigned long currentMillis = millis();
        
        if (stateStartTime == 0) {
            stateStartTime = currentMillis;
        }
        
        unsigned long stateElapsed = currentMillis - stateStartTime;
        
        switch (state) {
            case -1: // Initial state - start fade to red
                startFadeToColor(255, 0, 0);
                state = 0;
                stateStartTime = currentMillis;
                break;
                
            case 0: // Red
                if (stateElapsed >= HOLD_TIME) {
                    startFadeToColor(0, 0, 0);
                    state = 1;
                    stateStartTime = currentMillis;
                }
                break;
                
            case 1: // Black (no hold - immediate transition)
                if (!isFading) {
                    startFadeToColor(0, 255, 0);
                    state = 2;
                    stateStartTime = currentMillis;
                }
                break;
                
            case 2: // Green
                if (stateElapsed >= HOLD_TIME) {
                    startFadeToColor(0, 0, 0);
                    state = 3;
                    stateStartTime = currentMillis;
                }
                break;
                
            case 3: // Black (no hold - immediate transition)
                if (!isFading) {
                    startFadeToColor(0, 0, 255);
                    state = 4;
                    stateStartTime = currentMillis;
                }
                break;
                
            case 4: // Blue
                if (stateElapsed >= HOLD_TIME) {
                    startFadeToColor(0, 0, 0);
                    state = 0;
                    stateStartTime = currentMillis;
                }
                break;
        }
    }
}
