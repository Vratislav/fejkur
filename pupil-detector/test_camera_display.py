#!/usr/bin/env python3

import os
import time
from picamera2 import Picamera2

# Force local display on Pi (not SSH forwarded)
os.environ.pop('DISPLAY', None)  # Remove SSH forwarded display
os.environ.pop('SSH_CLIENT', None)  # Remove SSH indicators

def test_camera_display():
    """Simple test to verify camera display works on local Pi display"""
    print("Starting camera display test on local Pi HDMI display...")
    
    # Initialize camera
    camera = Picamera2()
    
    # Create simple preview configuration
    preview_config = camera.create_preview_configuration(main={"size": (640, 480)})
    camera.configure(preview_config)
    
    print("Starting preview on local Pi display...")
    try:
        # Start preview - this should show on Pi's HDMI display
        camera.start_preview()
        camera.start()
        
        print("Camera preview started on Pi's HDMI display.")
        print("Check the Pi's monitor - you should see the camera feed there.")
        print("Press Ctrl+C to stop the test...")
        
        # Keep running for 30 seconds or until interrupted
        for i in range(30):
            print(f"Running... {30-i} seconds remaining")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Stopping camera...")
        camera.stop_preview()
        camera.stop()
        print("Camera test completed.")

if __name__ == "__main__":
    test_camera_display() 