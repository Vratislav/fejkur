# Technical Specification

## Hardware Design

### Component Specifications

#### 1. Raspberry Pi 4
- **Model**: Raspberry Pi 4 Model B (2GB/4GB/8GB RAM)
- **CPU**: Broadcom BCM2711, Quad-core Cortex-A72 (ARM v8) 64-bit SoC @ 1.5GHz
- **GPU**: Broadcom VideoCore VI
- **Memory**: 2GB/4GB/8GB LPDDR4-3200 SDRAM
- **Storage**: MicroSD card slot (16GB+ recommended)
- **GPIO**: 40-pin header with PWM, I2C, SPI, UART

#### 2. Camera Module v2
- **Sensor**: Sony IMX219 8-megapixel sensor
- **Resolution**: 3280 x 2464 pixels
- **Frame Rate**: Up to 90fps at 640x480
- **Interface**: MIPI CSI-2
- **IR Sensitivity**: Good for low-light conditions

#### 3. IR Proximity Sensor
- **Model**: HC-SR04 or similar
- **Operating Voltage**: 5V
- **Detection Range**: 2cm - 400cm
- **Output**: Digital (HIGH/LOW)
- **Interface**: 3-pin (VCC, GND, OUT)

#### 4. LEDs
- **White LED**: 5mm, 3.3V, PWM controlled
- **RGB LED**: 2-pin, common anode/cathode
- **Current**: 20mA max per LED
- **Voltage**: 3.3V (Pi GPIO compatible)

### Wiring Diagram

```
Raspberry Pi 4
├── Camera Module v2
│   ├── CSI-2 Interface
│   └── Power from Pi
├── IR Proximity Sensor
│   ├── VCC → 5V (Pin 2)
│   ├── GND → GND (Pin 6)
│   └── OUT → GPIO4 (Pin 7)
└── NeoPixel LED
    ├── VCC → 5V
    ├── GND → GND
    └── DIN → GPIO18/PWM0 (Pin 12)
```

**Important Notes:**
- NeoPixel MUST use GPIO18 (PWM0) for proper timing
- Audio PWM is disabled to prevent interference with LED control
- 5V power is recommended for NeoPixel (not 3.3V) for reliable operation
- Use a level shifter if available for DIN (3.3V → 5V)

## Software Architecture

### Core Algorithms

#### 1. Eye Detection Algorithm
```python
def detect_eyes(frame):
    """
    Detect eyes using facial landmark detection
    Returns: List of eye ROIs
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Load facial landmark predictor
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    detector = dlib.get_frontal_face_detector()
    
    # Detect faces
    faces = detector(gray)
    
    eyes = []
    for face in faces:
        landmarks = predictor(gray, face)
        
        # Extract eye regions (landmarks 36-47 for left eye, 42-53 for right eye)
        left_eye = extract_eye_region(landmarks, 36, 47)
        right_eye = extract_eye_region(landmarks, 42, 53)
        
        eyes.extend([left_eye, right_eye])
    
    return eyes
```

#### 2. Pupil Detection Algorithm
```python
def measure_pupil_size(eye_roi):
    """
    Measure pupil size using contour detection
    Returns: Pupil diameter in pixels
    """
    # Convert to grayscale
    gray = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive threshold
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by area and circularity
    pupil_contour = None
    max_area = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # Minimum area threshold
            # Calculate circularity
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.7:  # Circularity threshold
                    if area > max_area:
                        max_area = area
                        pupil_contour = contour
    
    if pupil_contour is not None:
        # Calculate diameter using minimum enclosing circle
        (x, y), radius = cv2.minEnclosingCircle(pupil_contour)
        diameter = radius * 2
        return diameter
    
    return None
```

#### 3. Change Detection Algorithm
```python
def analyze_pupil_changes(measurements, time_window=2.0):
    """
    Analyze pupil size changes over time
    Returns: Alert status and change magnitude
    """
    if len(measurements) < 10:  # Minimum measurements
        return False, 0
    
    # Calculate rolling standard deviation
    window_size = int(time_window * SAMPLING_RATE)
    if len(measurements) < window_size:
        return False, 0
    
    recent_measurements = measurements[-window_size:]
    std_dev = np.std(recent_measurements)
    
    # Check if change is minimal
    if std_dev < MIN_PUPIL_CHANGE:
        return True, std_dev  # Alert condition
    
    return False, std_dev
```

### Data Structures

#### 1. Measurement Data
```python
@dataclass
class PupilMeasurement:
    timestamp: float
    diameter: float
    eye_id: int
    confidence: float
    frame_number: int
```

#### 2. System State
```python
@dataclass
class SystemState:
    is_measuring: bool
    proximity_detected: bool
    eye_detected: bool
    current_measurements: List[PupilMeasurement]
    alert_status: bool
    led_brightness: float
    rgb_led_color: str
```

### Performance Benchmarks

#### Expected Performance (Raspberry Pi 4)
- **Frame Processing**: 30 FPS at 640x480
- **Eye Detection**: < 50ms per frame
- **Pupil Measurement**: < 20ms per eye
- **Total Latency**: < 100ms end-to-end
- **Memory Usage**: < 500MB RAM
- **CPU Usage**: < 60% during measurement

#### Optimization Strategies
1. **ROI Processing**: Only process detected eye regions
2. **Frame Skipping**: Process every 2nd frame during tracking
3. **Resolution Scaling**: Use 320x240 for initial detection
4. **Multi-threading**: Separate threads for I/O and processing

## Communication Protocol

### MQTT Message Format
```json
{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "alert_type": "pupil_stagnation",
    "duration": 2.5,
    "measurements": [
        {"time": 0.0, "diameter": 4.2},
        {"time": 0.1, "diameter": 4.1},
        {"time": 0.2, "diameter": 4.2}
    ],
    "statistics": {
        "mean_diameter": 4.17,
        "std_deviation": 0.05,
        "change_magnitude": 0.05
    }
}
```

### LED Control Protocol
```python
# White LED (PWM control)
def set_white_led_brightness(brightness: float):
    """
    brightness: 0.0 to 1.0
    """
    pwm.ChangeDutyCycle(brightness * 100)

# RGB LED (digital control)
def set_rgb_led_color(color: str):
    """
    color: 'green', 'red', 'off'
    """
    if color == 'green':
        GPIO.output(RGB_LED_RED_PIN, GPIO.LOW)
        GPIO.output(RGB_LED_GREEN_PIN, GPIO.HIGH)
    elif color == 'red':
        GPIO.output(RGB_LED_RED_PIN, GPIO.HIGH)
        GPIO.output(RGB_LED_GREEN_PIN, GPIO.LOW)
    else:  # off
        GPIO.output(RGB_LED_RED_PIN, GPIO.LOW)
        GPIO.output(RGB_LED_GREEN_PIN, GPIO.LOW)
```

## Calibration Procedures

### 1. Camera Calibration
- Capture calibration images with known distances
- Calculate intrinsic camera parameters
- Store calibration matrix for accurate measurements

### 2. Proximity Sensor Calibration
- Measure detection range at different distances
- Adjust sensitivity settings
- Test with various lighting conditions

### 3. Pupil Measurement Calibration
- Use known-size objects for reference
- Calibrate pixel-to-millimeter conversion
- Account for individual eye variations

## Error Handling

### Common Error Scenarios
1. **Camera Connection Lost**: Retry connection, fallback to USB camera
2. **No Eye Detected**: Continue monitoring, log detection attempts
3. **Poor Lighting**: Adjust camera settings, increase IR illumination
4. **Hardware Failure**: Graceful degradation, alert user

### Recovery Procedures
- Automatic restart of failed components
- Data backup and recovery
- System health monitoring
- User notification for critical failures

## Testing Strategy

### Unit Tests
- Individual algorithm testing
- Hardware component testing
- Communication protocol testing

### Integration Tests
- End-to-end system testing
- Performance benchmarking
- Stress testing with continuous operation

### Field Testing
- Real-world environment testing
- User acceptance testing
- Long-term reliability testing 