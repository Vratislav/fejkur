#!/usr/bin/env python3

import time
from picamera2 import Picamera2

def test_working_preview():
    """Test camera preview using the same method as libcamera-hello"""
    print("Testing camera preview with working method...")
    
    camera = Picamera2()
    
    # Use the same configuration as our main script
    preview_config = camera.create_preview_configuration(
        main={"size": (640, 480)},
        lores={"size": (320, 240), "format": "YUV420"})
    camera.configure(preview_config)
    
    print("Starting camera with show_preview=True...")
    
    try:
        # This is the method that works (same as libcamera-hello)
        camera.start(show_preview=True)
        
        print("Camera preview started! You should see the camera feed on the Pi's display.")
        print("This uses the same method as libcamera-hello.")
        print("Press Ctrl+C to stop...")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping camera preview...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        camera.stop()
        print("Camera stopped.")

if __name__ == "__main__":
    test_working_preview() 