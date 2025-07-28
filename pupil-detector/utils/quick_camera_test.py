#!/usr/bin/env python3
"""
Quick Camera Test Script
Tests camera functionality and captures a test image
"""

import cv2
import numpy as np
import time
import os
from picamera2 import Picamera2

def test_camera():
    """Test basic camera functionality"""
    print("Testing Raspberry Pi Camera...")
    
    try:
        # Initialize camera
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(
            main={"size": (640, 480)}
        ))
        
        print("Starting camera...")
        picam2.start()
        
        # Wait for camera to initialize
        time.sleep(2)
        
        # Capture a test frame
        print("Capturing test frame...")
        frame = picam2.capture_array()
        
        print(f"Frame captured successfully!")
        print(f"Frame shape: {frame.shape}")
        print(f"Frame dtype: {frame.dtype}")
        print(f"Frame min/max values: {frame.min()}/{frame.max()}")
        
        # Convert to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Save test image
        test_image_path = "/tmp/camera_test.jpg"
        cv2.imwrite(test_image_path, frame_bgr)
        print(f"Test image saved to: {test_image_path}")
        
        # Display frame info
        height, width = frame.shape[:2]
        print(f"Resolution: {width}x{height}")
        
        # Check if image looks reasonable
        mean_brightness = np.mean(frame)
        print(f"Average brightness: {mean_brightness:.1f}")
        
        if mean_brightness < 10:
            print("WARNING: Image appears very dark - check lighting")
        elif mean_brightness > 250:
            print("WARNING: Image appears very bright - check exposure")
        else:
            print("Image brightness looks normal")
        
        picam2.stop()
        print("Camera test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Camera test failed: {e}")
        return False

def capture_image(output_path="/tmp/camera_capture.jpg"):
    """Capture and save a single image"""
    try:
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(
            main={"size": (640, 480)}
        ))
        
        picam2.start()
        time.sleep(1)  # Wait for camera to settle
        
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        cv2.imwrite(output_path, frame_bgr)
        print(f"Image captured and saved to: {output_path}")
        
        picam2.stop()
        return True
        
    except Exception as e:
        print(f"Failed to capture image: {e}")
        return False

def test_camera_stream(duration=5):
    """Test camera streaming for a few seconds"""
    print(f"Testing camera stream for {duration} seconds...")
    
    try:
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(
            main={"size": (640, 480)}
        ))
        
        picam2.start()
        
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < duration:
            frame = picam2.capture_array()
            frame_count += 1
            
            # Calculate FPS
            elapsed = time.time() - start_time
            fps = frame_count / elapsed
            
            print(f"\rFrames: {frame_count}, FPS: {fps:.1f}", end="")
            
        print(f"\nStream test completed: {frame_count} frames in {duration}s")
        print(f"Average FPS: {frame_count/duration:.1f}")
        
        picam2.stop()
        return True
        
    except Exception as e:
        print(f"Stream test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=== Raspberry Pi Camera Test ===")
    print()
    
    # Test 1: Basic camera functionality
    print("1. Testing basic camera functionality...")
    if test_camera():
        print("✓ Basic camera test passed")
    else:
        print("✗ Basic camera test failed")
        return
    
    print()
    
    # Test 2: Capture test image
    print("2. Capturing test image...")
    if capture_image():
        print("✓ Image capture test passed")
    else:
        print("✗ Image capture test failed")
    
    print()
    
    # Test 3: Stream test (optional)
    print("3. Testing camera stream (5 seconds)...")
    if test_camera_stream(5):
        print("✓ Stream test passed")
    else:
        print("✗ Stream test failed")
    
    print()
    print("=== Test Summary ===")
    print("If all tests passed, your camera is working correctly!")
    print("You can now use the camera viewer to see the feed over SSH.")
    print()
    print("To view camera feed over SSH:")
    print("  ssh -X pi@raspberrypi")
    print("  python3 utils/camera_viewer.py --method ssh_x11")

if __name__ == "__main__":
    main() 