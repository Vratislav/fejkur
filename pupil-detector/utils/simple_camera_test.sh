#!/bin/bash
# Simple Camera Test Script
# Quick commands to test Raspberry Pi camera over SSH

echo "=== Quick Camera Test Commands ==="
echo ""

# Test 1: Basic camera test
echo "1. Basic camera test:"
echo "python3 utils/quick_camera_test.py"
echo ""

# Test 2: Capture single image
echo "2. Capture single image:"
echo "python3 -c \"from picamera2 import Picamera2; import cv2; p=Picamera2(); p.configure(p.create_preview_configuration()); p.start(); frame=p.capture_array(); cv2.imwrite('/tmp/test.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)); p.stop(); print('Image saved to /tmp/test.jpg')\""
echo ""

# Test 3: X11 camera viewer
echo "3. View camera with X11 (Linux/Mac):"
echo "ssh -X pi@raspberrypi"
echo "python3 utils/camera_viewer.py --method ssh_x11"
echo ""

# Test 4: Save frames for analysis
echo "4. Save frames for analysis:"
echo "python3 utils/camera_viewer.py --method save_frames"
echo ""

# Test 5: Copy image to local machine
echo "5. Copy image to your computer:"
echo "scp pi@raspberrypi:/tmp/camera_test.jpg ./"
echo ""

echo "=== Quick Commands ==="
echo ""

# Function to run quick test
quick_test() {
    echo "Running quick camera test..."
    python3 utils/quick_camera_test.py
}

# Function to capture image
capture_image() {
    echo "Capturing image..."
    python3 -c "
from picamera2 import Picamera2
import cv2
import time

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()
time.sleep(1)

frame = picam2.capture_array()
frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
cv2.imwrite('/tmp/camera_snapshot.jpg', frame_bgr)
picam2.stop()
print('Image saved to /tmp/camera_snapshot.jpg')
"
}

# Function to show camera info
show_info() {
    echo "Camera information:"
    vcgencmd get_camera
    echo ""
    echo "Camera device:"
    ls -la /dev/video*
    echo ""
    echo "Camera permissions:"
    ls -la /dev/video0 2>/dev/null || echo "No camera device found"
}

# Check command line arguments
case "${1:-}" in
    "test")
        quick_test
        ;;
    "capture")
        capture_image
        ;;
    "info")
        show_info
        ;;
    "x11")
        echo "Starting X11 camera viewer..."
        python3 utils/camera_viewer.py --method ssh_x11
        ;;
    "vnc")
        echo "Starting VNC camera viewer..."
        python3 utils/camera_viewer.py --method vnc
        ;;
    "stream")
        echo "Starting network stream..."
        python3 utils/camera_viewer.py --method stream
        ;;
    "save")
        echo "Saving frames..."
        python3 utils/camera_viewer.py --method save_frames
        ;;
    *)
        echo "Usage: $0 [test|capture|info|x11|vnc|stream|save]"
        echo ""
        echo "Commands:"
        echo "  test    - Run full camera test"
        echo "  capture - Capture single image"
        echo "  info    - Show camera information"
        echo "  x11     - Start X11 camera viewer"
        echo "  vnc     - Start VNC camera viewer"
        echo "  stream  - Start network stream"
        echo "  save    - Save frames to disk"
        echo ""
        echo "Examples:"
        echo "  $0 test"
        echo "  $0 capture"
        echo "  $0 x11"
        ;;
esac 