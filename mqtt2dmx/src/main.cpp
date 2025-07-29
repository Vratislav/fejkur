
#include <Arduino.h>
#include <WiFiS3.h>
#include <ArduinoJson.h>
#include <EEPROM.h>

// WiFi settings
const char* ssid = "ChillNaZahrade";     // TODO: Replace with your WiFi credentials
const char* password = "TaXfGh76";  // TODO: Replace with your WiFi password

// Web server on port 80
WiFiServer server(80);

// DMX configuration
#define DMX_TX_PIN 1      // Serial1 TX (D1)
#define DMX_DE_PIN 2      // Direction Enable for MAX485
#define DMX_CHANNELS 512  // Total DMX channels
#define DMX_BREAK_TIME 92 // 92μs break
#define DMX_MAB_TIME 12   // 12μs mark after break
#define DMX_FRAME_TIME 25000  // 25ms = 40Hz

// Demo mode state & preset storage
#define MAX_PRESETS 10
#define CHANNELS_PER_PRESET 11

// EEPROM configuration
#define EEPROM_ADDR 0
#define EEPROM_MAGIC 0x444D5844 // "DMXD"

struct DemoConfig {
  uint32_t magic;
  uint8_t numPresets;
  unsigned long moveDelay;
  unsigned long holdTime;
  uint8_t presets[MAX_PRESETS][CHANNELS_PER_PRESET];
};

// Demo mode state
bool demoMode = false;
unsigned long demoLastUpdate = 0;
unsigned long demoMoveDelay = 1000;  // Movement delay in ms
unsigned long demoHoldTime = 5000;   // Hold time in ms
int demoCurrentStep = 0;  // 0: fade out, 1: move, 2: wait move, 3: fade in, 4: hold
int demoCurrentPreset = 0;

// Current fade values
float currentFadeProgress = 0.0;
uint8_t fadeStartColors[6] = {0}; // Dimmer, Strobe, R, G, B, W
#define FADE_TIME 5000 // 5 seconds fade

// Store preset data statically
uint8_t storedPresets[MAX_PRESETS][CHANNELS_PER_PRESET];
int numStoredPresets = 0;

// DMX data buffer and timing
uint8_t dmxData[DMX_CHANNELS] = {0};
unsigned long lastFrameTime = 0;
unsigned long frameCount = 0;

#include "index.h"

// Function declarations
void setDMXChannel(uint16_t channel, uint8_t value);
void sendDMXBreak();
void sendDMXFrame();
void processDemo();
void handleWebRequest(WiFiClient client);
void saveDemoToEEPROM();
void clearDemoFromEEPROM();
void loadDemoFromEEPROM();

// Set DMX channel value
void setDMXChannel(uint16_t channel, uint8_t value) {
    if (channel >= 1 && channel <= DMX_CHANNELS) {
        dmxData[channel - 1] = value;
    }
}

// Send DMX break signal
void sendDMXBreak() {
    Serial1.end();
    pinMode(DMX_TX_PIN, OUTPUT);
    digitalWrite(DMX_TX_PIN, LOW);
    delayMicroseconds(DMX_BREAK_TIME);
    digitalWrite(DMX_TX_PIN, HIGH);
    delayMicroseconds(DMX_MAB_TIME);
    Serial1.begin(250000, SERIAL_8N2);
}

// Send complete DMX frame
void sendDMXFrame() {
    frameCount++;
    digitalWrite(DMX_DE_PIN, HIGH);
    sendDMXBreak();
    Serial1.write((uint8_t)0x00);
    for (int i = 0; i < DMX_CHANNELS; i++) {
        Serial1.write((uint8_t)dmxData[i]);
    }
    Serial1.flush();
    digitalWrite(DMX_DE_PIN, LOW);
}

// Demo mode functions
void processDemo() {
    if (!demoMode) return;

    unsigned long currentTime = millis();
    unsigned long stepTime = currentTime - demoLastUpdate;

    // Debug current state
    static int lastStep = -1;
    if (demoCurrentStep != lastStep) {
        Serial.print("Demo step changed to: ");
        Serial.print(demoCurrentStep);
        Serial.print(" (Preset: ");
        Serial.print(demoCurrentPreset);
        Serial.println(")");
        lastStep = demoCurrentStep;

        // Store start values at the beginning of fades
        if (demoCurrentStep == 0) { // Start of fade out
            fadeStartColors[0] = dmxData[5];  // Dimmer
            fadeStartColors[1] = dmxData[6];  // Strobe
            fadeStartColors[2] = dmxData[7];  // Red
            fadeStartColors[3] = dmxData[8];  // Green
            fadeStartColors[4] = dmxData[9];  // Blue
            fadeStartColors[5] = dmxData[10]; // White
            currentFadeProgress = 0.0;
            Serial.println("Starting fade out from:");
            Serial.print("Dimmer: "); Serial.print(fadeStartColors[0]);
            Serial.print(" RGB: "); Serial.print(fadeStartColors[2]);
            Serial.print(","); Serial.print(fadeStartColors[3]);
            Serial.print(","); Serial.println(fadeStartColors[4]);
        }
        else if (demoCurrentStep == 3) { // Start of fade in
            memset(fadeStartColors, 0, sizeof(fadeStartColors));
            currentFadeProgress = 0.0;
            Serial.println("Starting fade in");
        }
    }

    switch (demoCurrentStep) {
        case 0: // Fade out colors
            // Calculate fade progress (0.0 to 1.0)
            currentFadeProgress = min(1.0, (float)stepTime / FADE_TIME);
            
            // Linear interpolation from current colors to black
            for (int i = 0; i < 6; i++) {
                uint8_t targetValue = 0;
                uint8_t currentValue = fadeStartColors[i] + (targetValue - fadeStartColors[i]) * currentFadeProgress;
                setDMXChannel(6 + i, currentValue);  // Channels 6-11 (Dimmer through White)
            }

            if (stepTime % 1000 == 0) { // Debug print every second
                Serial.print("Fade out progress: ");
                Serial.print(currentFadeProgress * 100);
                Serial.println("%");
            }

            if (currentFadeProgress >= 1.0) {
                Serial.println("Fade out complete");
                demoCurrentStep = 1;
                demoLastUpdate = currentTime;
            }
            break;

        case 1: // Change position
            Serial.println("Changing position...");
            Serial.print("Setting channels from preset ");
            Serial.println(demoCurrentPreset);
            
            // Set position channels from stored preset
            setDMXChannel(1, storedPresets[demoCurrentPreset][0]); // Pan
            setDMXChannel(2, storedPresets[demoCurrentPreset][1]); // Pan Fine
            setDMXChannel(3, storedPresets[demoCurrentPreset][2]); // Tilt
            setDMXChannel(4, storedPresets[demoCurrentPreset][3]); // Tilt Fine
            setDMXChannel(5, storedPresets[demoCurrentPreset][4]); // Speed
            
            demoCurrentStep = 2;
            demoLastUpdate = currentTime;
            break;

        case 2: // Wait for movement
            if (stepTime >= demoMoveDelay) {
                Serial.print("Movement wait complete (");
                Serial.print(demoMoveDelay);
                Serial.println("ms)");
                demoCurrentStep = 3;
                demoLastUpdate = currentTime;
            }
            break;

        case 3: // Fade in colors
            // Calculate fade progress (0.0 to 1.0)
            currentFadeProgress = min(1.0, (float)stepTime / FADE_TIME);
            
            // Linear interpolation from black to target colors
            setDMXChannel(6, fadeStartColors[0] + (storedPresets[demoCurrentPreset][5] - fadeStartColors[0]) * currentFadeProgress);   // Dimmer
            setDMXChannel(7, fadeStartColors[1] + (storedPresets[demoCurrentPreset][6] - fadeStartColors[1]) * currentFadeProgress);   // Strobe
            setDMXChannel(8, fadeStartColors[2] + (storedPresets[demoCurrentPreset][7] - fadeStartColors[2]) * currentFadeProgress);   // Red
            setDMXChannel(9, fadeStartColors[3] + (storedPresets[demoCurrentPreset][8] - fadeStartColors[3]) * currentFadeProgress);   // Green
            setDMXChannel(10, fadeStartColors[4] + (storedPresets[demoCurrentPreset][9] - fadeStartColors[4]) * currentFadeProgress);  // Blue
            setDMXChannel(11, fadeStartColors[5] + (storedPresets[demoCurrentPreset][10] - fadeStartColors[5]) * currentFadeProgress); // White

            if (stepTime % 1000 == 0) { // Debug print every second
                Serial.print("Fade in progress: ");
                Serial.print(currentFadeProgress * 100);
                Serial.println("%");
            }

            if (currentFadeProgress >= 1.0) {
                Serial.println("Fade in complete");
                demoCurrentStep = 4;
                demoLastUpdate = currentTime;
            }
            break;

        case 4: // Hold
            if (stepTime >= demoHoldTime) {
                Serial.print("Hold complete, moving to next preset (");
                Serial.print(demoHoldTime);
                Serial.println("ms)");
                demoCurrentStep = 0;
                demoLastUpdate = currentTime;
                demoCurrentPreset = (demoCurrentPreset + 1) % numStoredPresets;
            }
            break;
    }
}

void saveDemoToEEPROM() {
  DemoConfig config;
  config.magic = EEPROM_MAGIC;
  config.numPresets = numStoredPresets;
  config.moveDelay = demoMoveDelay;
  config.holdTime = demoHoldTime;
  memcpy(config.presets, storedPresets, sizeof(storedPresets));

  Serial.println("Saving demo to EEPROM...");
  EEPROM.put(EEPROM_ADDR, config);
  Serial.println("Save complete.");
}

void clearDemoFromEEPROM() {
  Serial.println("Clearing demo from EEPROM...");
  uint32_t magic = 0; // Invalidate the magic number
  EEPROM.put(EEPROM_ADDR, magic);
  Serial.println("EEPROM cleared.");
}

void loadDemoFromEEPROM() {
  DemoConfig config;
  EEPROM.get(EEPROM_ADDR, config);

  if (config.magic == EEPROM_MAGIC) {
    Serial.println("Found valid demo in EEPROM. Starting automatically.");
    numStoredPresets = config.numPresets;
    demoMoveDelay = config.moveDelay;
    demoHoldTime = config.holdTime;
    memcpy(storedPresets, config.presets, sizeof(storedPresets));

    demoCurrentPreset = 0;
    demoCurrentStep = 0;
    demoLastUpdate = millis();
    demoMode = true;
  } else {
    Serial.println("No valid demo found in EEPROM.");
  }
}

// Handle incoming web requests
void handleWebRequest(WiFiClient client) {
    String currentLine = "";
    String httpMethod = "";
    String path = "";
    bool headersDone = false;
    String body = "";
    
    unsigned long timeout = millis();
    
    while (client.connected() && millis() - timeout < 1000) {
        if (client.available()) {
            char c = client.read();
            timeout = millis();
            
            if (!headersDone) {
                if (c == '\n') {
                    if (currentLine.length() == 0) {
                        headersDone = true;
                        
                        if (httpMethod == "POST") {
                            while (client.available()) {
                                body += (char)client.read();
                            }
                        }
                        
                        if (path == "/") {
                            client.println("HTTP/1.1 200 OK");
                            client.println("Content-Type: text/html");
                            client.println();
                            client.print(INDEX_HTML);
                        }
                        else if (path == "/api/channels" && httpMethod == "POST") {
                            StaticJsonDocument<200> doc;
                            DeserializationError error = deserializeJson(doc, body);
                            
                            if (!error) {
                                int channel = doc["channel"];
                                int value = doc["value"];
                                
                                if (channel >= 1 && channel <= DMX_CHANNELS) {
                                    setDMXChannel(channel, value);
                                    client.println("HTTP/1.1 200 OK");
                                    client.println("Content-Type: application/json");
                                    client.println();
                                    client.println("{\"status\":\"ok\"}");
                                } else {
                                    client.println("HTTP/1.1 400 Bad Request");
                                    client.println();
                                }
                            }
                        }
                        else if (path == "/api/channels/batch" && httpMethod == "POST") {
                            StaticJsonDocument<1024> doc;
                            DeserializationError error = deserializeJson(doc, body);
                            
                            if (!error) {
                                JsonArray updates = doc["updates"];
                                bool valid = true;
                                
                                for (JsonObject update : updates) {
                                    int channel = update["channel"];
                                    int value = update["value"];
                                    if (channel < 1 || channel > DMX_CHANNELS || value < 0 || value > 255) {
                                        valid = false;
                                        break;
                                    }
                                }
                                
                                if (valid) {
                                    for (JsonObject update : updates) {
                                        setDMXChannel(update["channel"], update["value"]);
                                    }
                                    
                                    client.println("HTTP/1.1 200 OK");
                                    client.println("Content-Type: application/json");
                                    client.println();
                                    client.println("{\"status\":\"ok\"}");
                                } else {
                                    client.println("HTTP/1.1 400 Bad Request");
                                    client.println();
                                }
                            }
                        }
                        else if (path == "/api/demo/start" && httpMethod == "POST") {
                            StaticJsonDocument<4096> doc;
                            DeserializationError error = deserializeJson(doc, body);
                            
                            if (!error) {
                                Serial.println("Starting demo mode...");
                                Serial.print("Request body: ");
                                Serial.println(body);
                                
                                JsonArray presets = doc["presets"];
                                if (presets.isNull()) {
                                    Serial.println("ERROR: No presets array in request!");
                                    client.println("HTTP/1.1 400 Bad Request");
                                    client.println();
                                    return;
                                }

                                Serial.print("Number of presets: ");
                                Serial.println(presets.size());

                                if (presets.size() < 2 || presets.size() > MAX_PRESETS) {
                                    Serial.println("ERROR: Invalid number of presets!");
                                    client.println("HTTP/1.1 400 Bad Request");
                                    client.println();
                                    return;
                                }

                                // Store presets in our static array
                                numStoredPresets = 0;
                                for (JsonObject preset : presets) {
                                    if (!preset.containsKey("values")) {
                                        Serial.println("ERROR: Preset missing values array!");
                                        continue;
                                    }

                                    JsonArray values = preset["values"];
                                    if (values.size() < CHANNELS_PER_PRESET) {
                                        Serial.println("ERROR: Preset values array too small!");
                                        continue;
                                    }

                                    // Copy values to our static array
                                    for (int i = 0; i < CHANNELS_PER_PRESET; i++) {
                                        storedPresets[numStoredPresets][i] = values[i];
                                    }
                                    numStoredPresets++;

                                    Serial.print("Stored preset ");
                                    Serial.print(numStoredPresets - 1);
                                    Serial.print(": Pan=");
                                    Serial.print(storedPresets[numStoredPresets-1][0]);
                                    Serial.print(", Tilt=");
                                    Serial.println(storedPresets[numStoredPresets-1][2]);
                                }

                                if (numStoredPresets < 2) {
                                    Serial.println("ERROR: Not enough valid presets!");
                                    client.println("HTTP/1.1 400 Bad Request");
                                    client.println();
                                    return;
                                }

                                // Set demo parameters
                                demoMoveDelay = doc["moveDelay"] | 1000;
                                demoHoldTime = doc["holdTime"] | 5000;
                                demoCurrentPreset = 0;
                                demoCurrentStep = 0;
                                demoLastUpdate = millis();
                                demoMode = true;

                                Serial.print("Demo started with ");
                                Serial.print(numStoredPresets);
                                Serial.println(" presets");
                                Serial.print("Move delay: ");
                                Serial.print(demoMoveDelay);
                                Serial.print("ms, Hold time: ");
                                Serial.print(demoHoldTime);
                                Serial.println("ms");
                                
                                saveDemoToEEPROM(); // Save the new demo
                                
                                client.println("HTTP/1.1 200 OK");
                                client.println("Content-Type: application/json");
                                client.println();
                                client.println("{\"status\":\"ok\"}");
                            } else {
                                Serial.print("ERROR: JSON parse error - ");
                                Serial.println(error.c_str());
                                client.println("HTTP/1.1 400 Bad Request");
                                client.println();
                            }
                        }
                        else if (path == "/api/demo/stop" && httpMethod == "POST") {
                            demoMode = false;
                            clearDemoFromEEPROM(); // Clear auto-start
                            client.println("HTTP/1.1 200 OK");
                            client.println("Content-Type: application/json");
                            client.println();
                            client.println("{\"status\":\"ok\"}");
                        }
                        break;
                    } else {
                        if (httpMethod == "") {
                            int spaceIndex = currentLine.indexOf(' ');
                            if (spaceIndex != -1) {
                                httpMethod = currentLine.substring(0, spaceIndex);
                                path = currentLine.substring(spaceIndex + 1, currentLine.indexOf(' ', spaceIndex + 1));
                            }
                        }
                        currentLine = "";
                    }
                } else if (c != '\r') {
                    currentLine += c;
                }
            }
        }
    }
    client.stop();
}

void setup() {
    // Initialize Serial for debugging
    Serial.begin(115200);
    while (!Serial) delay(10);
    Serial.println("Arduino R4 DMX Web Controller");
    
    // Initialize DMX
    pinMode(DMX_DE_PIN, OUTPUT);
    digitalWrite(DMX_DE_PIN, LOW);
    Serial1.begin(250000, SERIAL_8N2);
    
    // Set initial DMX values
    setDMXChannel(2, 128);  // Pan Fine = 128
    setDMXChannel(4, 128);  // Tilt Fine = 128
    
    // Initialize WiFi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    
    // Start web server
    server.begin();
    
    Serial.println("System ready!");

    loadDemoFromEEPROM(); // Load and auto-start if present
}

void loop() {
    // Continue sending DMX frames at 40Hz
    unsigned long currentTime = micros();
    if (currentTime - lastFrameTime >= DMX_FRAME_TIME) {
        sendDMXFrame();
        lastFrameTime = currentTime;
    }
    
    if (demoMode) {
        processDemo();
    }
    
    // Handle web clients
    WiFiClient client = server.available();
    if (client) {
        handleWebRequest(client);
    }
}
