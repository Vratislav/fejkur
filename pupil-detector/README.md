# Pupil Detection System

## System Overview

This project implements an automated pupil size monitoring system using a Raspberry Pi. The system detects when a user's eye is in front of the camera, measures pupil size changes over time, and provides feedback through LED indicators and MQTT communication.

## Key Features

- **Proximity Detection**: IR proximity sensor triggers camera activation
- **Eye Detection**: Computer vision algorithms detect and track the eye
- **Pupil Measurement**: Real-time pupil size measurement using OpenCV
- **LED Feedback**: White LED for measurement status, RGB LED for results
- **MQTT Communication**: Sends alerts when pupil size changes are minimal
- **Data Logging**: Continuous logging of pupil measurements

## Hardware Requirements

### Core Components
- **Raspberry Pi 4** (recommended) or Pi 3B+
- **Raspberry Pi Camera Module v2** (8MP, IR-sensitive)
- **IR Proximity Sensor** (3-pin: GND, VCC, OUT)
- **White LED** (with PWM control for brightness)
- **RGB LED** (2-pin, polarity-dependent color)
- **Breadboard and jumper wires**

### Performance Considerations
- **Raspberry Pi 4**: Excellent performance for real-time CV processing
- **Pi Camera v2**: Optimized for Pi, good IR sensitivity, 8MP resolution
- **Memory**: 2GB+ RAM recommended for smooth operation
- **Storage**: 16GB+ SD card for logging and system

## Software Architecture

### Core Modules

```
pupil-detector/
├── hardware/           # Hardware interface modules
│   ├── proximity.py    # IR proximity sensor control
│   ├── leds.py         # LED control (white + RGB)
│   └── camera.py       # Camera interface
├── vision/             # Computer vision modules
│   ├── eye_detector.py # Eye detection algorithms
│   ├── pupil_measure.py # Pupil size measurement
│   └── tracking.py     # Eye tracking
├── communication/      # Communication modules
│   ├── mqtt_client.py  # MQTT messaging
│   └── data_logger.py  # Measurement logging
├── utils/              # Utility functions
│   ├── config.py       # Configuration management
│   └── helpers.py      # Helper functions
└── main.py            # Main application entry point
```

### Dependencies

```python
# Core dependencies
opencv-python>=4.5.0
numpy>=1.21.0
paho-mqtt>=1.6.0
RPi.GPIO>=0.7.0
picamera2>=0.3.0  # For Pi Camera v2
dlib>=19.24.0      # For facial landmark detection
```

## System Workflow

### 1. Initialization Phase
- Initialize hardware components (camera, sensors, LEDs)
- Load configuration parameters
- Establish MQTT connection
- Calibrate proximity sensor

### 2. Detection Phase
- Monitor proximity sensor for user presence
- When triggered, activate camera and start image processing
- Detect eye position using facial landmark detection
- Track eye movement and position

### 3. Measurement Phase
- Extract eye region of interest (ROI)
- Apply pupil detection algorithms:
  - Convert to grayscale
  - Apply Gaussian blur
  - Use Hough Circle detection or contour analysis
  - Calculate pupil diameter in pixels
- Log measurements with timestamps

### 4. Analysis Phase
- Calculate pupil size changes over time
- Apply statistical analysis for trend detection
- Determine if size changes are minimal/absent
- Trigger alerts based on thresholds

### 5. Feedback Phase
- Control white LED brightness during measurement
- Set RGB LED color based on results:
  - Green: Normal pupil response
  - Red: Minimal/no pupil response
- Send MQTT messages for external monitoring

## Configuration Parameters

```python
# Measurement settings
MEASUREMENT_DURATION = 30  # seconds
SAMPLING_RATE = 10        # Hz
MIN_PUPIL_CHANGE = 0.5    # pixels
ALERT_THRESHOLD = 2.0     # seconds of minimal change

# Hardware settings
PROXIMITY_PIN = 17
WHITE_LED_PIN = 18
RGB_LED_RED_PIN = 22
RGB_LED_GREEN_PIN = 23
CAMERA_RESOLUTION = (640, 480)
CAMERA_FPS = 30

# MQTT settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "pupil_detector/alerts"
```

## Performance Analysis

### Raspberry Pi Feasibility

**Yes, this is very feasible on Raspberry Pi 4:**

- **CPU**: Quad-core ARM Cortex-A72 handles real-time CV well
- **Memory**: 2-8GB RAM sufficient for OpenCV operations
- **Camera**: Pi Camera v2 provides excellent performance
- **GPIO**: Built-in PWM and GPIO pins for all sensors/LEDs

### Performance Optimizations

1. **Image Processing**:
   - Use lower resolution (640x480) for faster processing
   - Implement ROI cropping to reduce processing area
   - Use optimized OpenCV algorithms

2. **Memory Management**:
   - Stream processing (no frame buffering)
   - Efficient data structures for measurements
   - Regular garbage collection

3. **Hardware Acceleration**:
   - Utilize Pi's GPU for image processing
   - Use hardware PWM for LED control
   - Optimize camera settings for speed

## Implementation Plan

### Phase 1: Hardware Setup
- [ ] Assemble hardware components
- [ ] Test individual components (camera, sensors, LEDs)
- [ ] Create basic GPIO control modules

### Phase 2: Core Vision
- [ ] Implement eye detection algorithms
- [ ] Develop pupil measurement system
- [ ] Create measurement logging

### Phase 3: Integration
- [ ] Integrate proximity sensor triggering
- [ ] Implement LED feedback system
- [ ] Add MQTT communication

### Phase 4: Testing & Optimization
- [ ] Performance testing and optimization
- [ ] Calibration and fine-tuning
- [ ] Documentation and deployment

## Safety Considerations

- **Eye Safety**: Ensure IR LED intensity is safe for eyes
- **Privacy**: Implement secure data handling for medical data
- **Reliability**: Add error handling and system recovery
- **Calibration**: Provide calibration procedures for accurate measurements

## Future Enhancements

- **Machine Learning**: Implement ML-based pupil detection
- **Web Interface**: Real-time monitoring dashboard
- **Mobile App**: Remote monitoring capabilities
- **Data Analytics**: Advanced trend analysis and reporting 