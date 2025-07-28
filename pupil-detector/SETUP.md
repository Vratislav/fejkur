# Setup Guide

## Prerequisites

### Hardware Requirements
- Raspberry Pi 4 (2GB+ RAM recommended)
- Raspberry Pi Camera Module v2
- IR Proximity Sensor (HC-SR04 or similar)
- White LED with 220Ω resistor
- RGB LED with 220Ω resistors
- Breadboard and jumper wires
- MicroSD card (16GB+)
- Power supply (5V, 3A+)

### Software Requirements
- Raspberry Pi OS (Bullseye or newer)
- Python 3.9+
- Git

## Installation Steps

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv
sudo apt install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev
sudo apt install -y libjasper-dev libqtcore4 libqtgui4 libqt4-test
sudo apt install -y libharfbuzz0b libpango-1.0-0 libpangocairo-1.0-0
sudo apt install -y libgdk-pixbuf2.0-0 libffi-dev libssl-dev
sudo apt install -y cmake build-essential pkg-config
sudo apt install -y libjpeg-dev libtiff-dev libjasper-dev libpng-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev libgtk-3-dev
sudo apt install -y libatlas-base-dev gfortran
sudo apt install -y libopenblas-dev liblapack-dev
sudo apt install -y libhdf5-dev libhdf5-serial-dev libhdf5-103
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt install -y libgtk-3-dev libcanberra-gtk3-dev
sudo apt install -y libboost-all-dev
```

### 2. Enable Hardware Interfaces

```bash
# Enable camera interface
sudo raspi-config nonint do_camera 0

# Enable I2C (if needed for additional sensors)
sudo raspi-config nonint do_i2c 0

# Enable SPI (if needed for additional sensors)
sudo raspi-config nonint do_spi 0

# Enable hardware PWM
sudo raspi-config nonint do_pwm 0

# Reboot to apply changes
sudo reboot
```

### 3. Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd pupil-detector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Hardware Assembly

#### Camera Module
1. Disconnect power from Raspberry Pi
2. Locate the CSI port on the Pi
3. Gently lift the plastic clip on the CSI port
4. Insert the camera ribbon cable with blue side facing the Ethernet port
5. Press down the plastic clip to secure the cable
6. Connect power and test camera

#### Proximity Sensor
1. Connect VCC to 5V (Pin 2)
2. Connect GND to GND (Pin 6)
3. Connect OUT to GPIO17 (Pin 11)

#### LEDs
1. **White LED**:
   - Anode → GPIO18 (Pin 12) via 220Ω resistor
   - Cathode → GND

2. **RGB LED**:
   - Red → GPIO22 (Pin 15) via 220Ω resistor
   - Green → GPIO23 (Pin 16) via 220Ω resistor
   - Common → GND (common cathode) or 3.3V (common anode)

### 5. Download Facial Landmark Model

```bash
# Download dlib facial landmark predictor
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat utils/
```

### 6. Configuration

Create configuration file:

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml`:

```yaml
# Hardware Configuration
hardware:
  proximity_pin: 17
  white_led_pin: 18
  rgb_led_red_pin: 22
  rgb_led_green_pin: 23
  
# Camera Configuration
camera:
  resolution: [640, 480]
  fps: 30
  exposure_mode: "auto"
  awb_mode: "auto"
  
# Measurement Configuration
measurement:
  duration: 30  # seconds
  sampling_rate: 10  # Hz
  min_pupil_change: 0.5  # pixels
  alert_threshold: 2.0  # seconds
  
# MQTT Configuration
mqtt:
  broker: "localhost"
  port: 1883
  topic: "pupil_detector/alerts"
  username: ""
  password: ""
```

### 7. Test Individual Components

#### Test Camera
```bash
python3 -c "
from picamera2 import Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()
print('Camera initialized successfully')
picam2.stop()
"
```

#### Test GPIO
```bash
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)
print('GPIO initialized successfully')
GPIO.cleanup()
"
```

#### Test Proximity Sensor
```bash
python3 tests/test_proximity.py
```

#### Test LEDs
```bash
python3 tests/test_leds.py
```

### 8. Run Initial Tests

```bash
# Test eye detection
python3 tests/test_eye_detection.py

# Test pupil measurement
python3 tests/test_pupil_measurement.py

# Test full system
python3 tests/test_system.py
```

## Troubleshooting

### Common Issues

#### 1. Camera Not Detected
```bash
# Check camera interface
vcgencmd get_camera

# Should return: supported=1 detected=1
```

#### 2. GPIO Permission Errors
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Log out and back in, or reboot
```

#### 3. OpenCV Installation Issues
```bash
# Install OpenCV from source if needed
pip uninstall opencv-python
pip install opencv-python-headless
```

#### 4. Dlib Compilation Issues
```bash
# Install dlib dependencies
sudo apt install -y cmake build-essential pkg-config
sudo apt install -y libopenblas-dev liblapack-dev
sudo apt install -y libx11-dev libgtk-3-dev
sudo apt install -y libboost-python-dev

# Reinstall dlib
pip uninstall dlib
pip install dlib
```

### Performance Optimization

#### 1. Overclock Raspberry Pi (Optional)
```bash
# Edit config.txt
sudo nano /boot/config.txt

# Add these lines:
over_voltage=2
arm_freq=1750
gpu_freq=600
```

#### 2. Enable GPU Memory Split
```bash
# Edit config.txt
sudo nano /boot/config.txt

# Set GPU memory:
gpu_mem=128
```

#### 3. Disable Unnecessary Services
```bash
# Disable Bluetooth if not needed
sudo systemctl disable bluetooth

# Disable WiFi if using Ethernet
sudo systemctl disable wpa_supplicant
```

## Development Setup

### Code Quality Tools
```bash
# Install development tools
pip install black flake8 pytest

# Format code
black .

# Check code style
flake8 .

# Run tests
pytest
```

### IDE Setup
- Install VS Code with Python extension
- Configure Python interpreter to use virtual environment
- Install recommended extensions for Python development

## Deployment

### Production Setup
```bash
# Create systemd service
sudo nano /etc/systemd/system/pupil-detector.service
```

Service file content:
```ini
[Unit]
Description=Pupil Detection System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pupil-detector
Environment=PATH=/home/pi/pupil-detector/venv/bin
ExecStart=/home/pi/pupil-detector/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl enable pupil-detector
sudo systemctl start pupil-detector
sudo systemctl status pupil-detector
```

### Monitoring
```bash
# View logs
sudo journalctl -u pupil-detector -f

# Check system resources
htop
```

## Next Steps

1. **Calibrate the system** with known test subjects
2. **Fine-tune parameters** based on your specific use case
3. **Set up MQTT broker** for external communication
4. **Implement data visualization** for monitoring
5. **Add web interface** for remote monitoring 