# Camera Viewing Guide for SSH

This guide provides multiple methods to view the Raspberry Pi camera feed when connected via SSH.

## Method 1: X11 Forwarding (Recommended for Linux/Mac)

### Setup on Raspberry Pi
```bash
# Install X11 server if not already installed
sudo apt install -y x11-apps

# Make sure X11 forwarding is enabled in SSH config
sudo nano /etc/ssh/sshd_config
# Ensure these lines are uncommented:
# X11Forwarding yes
# X11DisplayOffset 10
# X11UseLocalhost yes

# Restart SSH service
sudo systemctl restart ssh
```

### Connect from Your Computer
```bash
# Connect with X11 forwarding enabled
ssh -X pi@raspberrypi

# Or for trusted X11 forwarding (if you get permission errors)
ssh -Y pi@raspberrypi
```

### View Camera Feed
```bash
# Run the camera viewer
python3 utils/camera_viewer.py --method ssh_x11

# Or use a simple test script
python3 -c "
from picamera2 import Picamera2
import cv2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()
while True:
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow('Camera', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
picam2.stop()
"
```

## Method 2: VNC (Recommended for Windows)

### Setup VNC Server on Raspberry Pi
```bash
# Enable VNC in raspi-config
sudo raspi-config
# Navigate to: Interface Options → VNC → Enable

# Or enable via command line
sudo raspi-config nonint do_vnc 0

# Install VNC server if needed
sudo apt install -y realvnc-vnc-server

# Start VNC server
vncserver :1 -geometry 1920x1080 -depth 24
```

### Connect via VNC
1. Install VNC Viewer on your computer
2. Connect to `raspberrypi:1` (or the IP address)
3. Run the camera viewer in the VNC session:
```bash
python3 utils/camera_viewer.py --method vnc
```

## Method 3: Web Stream (Browser-based)

### Setup Web Stream
```bash
# Install required packages
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good

# Create a simple web stream
python3 utils/camera_viewer.py --method stream
```

### Access via Browser
Open your browser and navigate to:
- `http://raspberrypi:8080` (if using hostname)
- `http://192.168.1.xxx:8080` (replace with Pi's IP)

## Method 4: Frame Capture (For Analysis)

### Save Frames for Later Viewing
```bash
# Save frames to disk
python3 utils/camera_viewer.py --method save_frames

# View saved frames
ls -la /tmp/camera_frames/

# Copy frames to your computer
scp -r pi@raspberrypi:/tmp/camera_frames/ ./local_frames/
```

## Method 5: Simple Test Scripts

### Quick Camera Test
```bash
# Test camera capture
python3 -c "
from picamera2 import Picamera2
import cv2
import numpy as np

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

print('Camera started. Press Ctrl+C to stop.')

try:
    while True:
        frame = picam2.capture_array()
        print(f'Frame shape: {frame.shape}')
        time.sleep(1)
except KeyboardInterrupt:
    print('Stopping camera...')
    picam2.stop()
"
```

### Capture Single Image
```bash
# Capture and save a single image
python3 -c "
from picamera2 import Picamera2
import cv2

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

frame = picam2.capture_array()
frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
cv2.imwrite('/tmp/test_image.jpg', frame)
print('Image saved to /tmp/test_image.jpg')
picam2.stop()
"
```

## Method 6: Network Stream with FFmpeg

### Stream to Network
```bash
# Install FFmpeg
sudo apt install -y ffmpeg

# Stream camera to network
ffmpeg -f lavfi -i testsrc -f v4l2 -i /dev/video0 -c:v libx264 -preset ultrafast -tune zerolatency -f mpegts udp://0.0.0.0:1234
```

### View Stream
```bash
# On your computer, install VLC or use FFplay
ffplay udp://raspberrypi:1234
```

## Troubleshooting

### X11 Issues
```bash
# Check if X11 forwarding is working
echo $DISPLAY

# If DISPLAY is not set, try:
export DISPLAY=:10.0

# Check X11 connection
xeyes  # Should show moving eyes if X11 is working
```

### Permission Issues
```bash
# Add user to video group
sudo usermod -a -G video pi

# Check camera permissions
ls -la /dev/video*

# Fix camera permissions if needed
sudo chmod 666 /dev/video0
```

### Camera Not Detected
```bash
# Check if camera is enabled
vcgencmd get_camera

# Should return: supported=1 detected=1

# If not detected, enable camera:
sudo raspi-config nonint do_camera 0
sudo reboot
```

### Performance Issues
```bash
# Reduce resolution for better performance
python3 utils/camera_viewer.py --resolution 320 240 --fps 15

# Use lower quality for streaming
python3 utils/camera_viewer.py --method stream --fps 10
```

## Quick Commands Reference

### Connect with X11
```bash
ssh -X pi@raspberrypi
```

### Test Camera
```bash
python3 utils/camera_viewer.py --method ssh_x11
```

### Save Test Image
```bash
python3 -c "
from picamera2 import Picamera2
import cv2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()
frame = picam2.capture_array()
frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
cv2.imwrite('/tmp/camera_test.jpg', frame)
picam2.stop()
print('Test image saved to /tmp/camera_test.jpg')
"
```

### Copy Image to Local Machine
```bash
scp pi@raspberrypi:/tmp/camera_test.jpg ./
```

## Advanced: Custom Camera Viewer

Create a custom viewer for your specific needs:

```python
#!/usr/bin/env python3
import cv2
from picamera2 import Picamera2
import numpy as np

class CustomCameraViewer:
    def __init__(self, resolution=(640, 480)):
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(
            main={"size": resolution}
        ))
        
    def start(self):
        self.picam2.start()
        
        while True:
            frame = self.picam2.capture_array()
            
            # Add your custom processing here
            # frame = self.process_frame(frame)
            
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imshow('Custom Camera Viewer', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cv2.destroyAllWindows()
        self.picam2.stop()
        
    def process_frame(self, frame):
        # Add your custom processing here
        # Example: add text overlay
        cv2.putText(frame, 'Raspberry Pi Camera', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame

if __name__ == "__main__":
    viewer = CustomCameraViewer()
    viewer.start()
```

## Tips for Best Performance

1. **Use X11 forwarding** for Linux/Mac - it's the most reliable
2. **Use VNC** for Windows - easier setup
3. **Reduce resolution** if you experience lag
4. **Use wired connection** instead of WiFi for better performance
5. **Close unnecessary applications** on the Pi to free up resources
6. **Monitor system resources** with `htop` while streaming 