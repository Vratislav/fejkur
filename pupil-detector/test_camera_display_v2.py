#!/usr/bin/env python3

import os
import time
from picamera2 import Picamera2

def check_display_environment():
    """Check display environment and available outputs"""
    print("=== Display Environment Check ===")
    print(f"DISPLAY env var: {os.environ.get('DISPLAY', 'Not set')}")
    print(f"WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'Not set')}")
    
    # Check if we're in a desktop session
    print(f"XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', 'Not set')}")
    print(f"XDG_CURRENT_DESKTOP: {os.environ.get('XDG_CURRENT_DESKTOP', 'Not set')}")
    
    # Check framebuffer devices
    try:
        fb_devices = os.listdir('/dev/')
        fb_devices = [d for d in fb_devices if d.startswith('fb')]
        print(f"Framebuffer devices: {fb_devices}")
    except:
        print("Could not check framebuffer devices")
    
    print("=" * 40)

def test_opencv_display():
    """Test if OpenCV display works"""
    print("\n=== Testing OpenCV Display ===")
    try:
        import cv2
        import numpy as np
        
        # Create a simple test image
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(test_image, "OpenCV Test", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        
        cv2.namedWindow("Test", cv2.WINDOW_NORMAL)
        cv2.imshow("Test", test_image)
        
        print("OpenCV window created. Check if you can see it...")
        for i in range(5):
            print(f"Waiting... {5-i}")
            if cv2.waitKey(1000) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
        print("OpenCV test completed")
        return True
    except Exception as e:
        print(f"OpenCV test failed: {e}")
        return False

def test_camera_no_preview():
    """Test camera without preview - just capture frames"""
    print("\n=== Testing Camera Capture (No Preview) ===")
    try:
        camera = Picamera2()
        config = camera.create_still_configuration(main={"size": (640, 480)})
        camera.configure(config)
        camera.start()
        
        print("Camera started, capturing test frame...")
        frame = camera.capture_array()
        print(f"Captured frame shape: {frame.shape}")
        
        camera.stop()
        print("Camera capture test successful")
        return True
    except Exception as e:
        print(f"Camera capture test failed: {e}")
        return False

def test_camera_with_drm():
    """Test camera with DRM preview"""
    print("\n=== Testing Camera with DRM Preview ===")
    try:
        from picamera2.previews import DrmPreview
        
        camera = Picamera2()
        preview = DrmPreview(camera)
        
        config = camera.create_preview_configuration(main={"size": (640, 480)})
        camera.configure(config)
        camera.start()
        
        print("DRM preview started. Check your display...")
        for i in range(10):
            print(f"Running... {10-i}")
            time.sleep(1)
        
        camera.stop()
        print("DRM preview test completed")
        return True
    except Exception as e:
        print(f"DRM preview test failed: {e}")
        return False

def main():
    print("Camera Display Diagnostic Tool")
    print("=" * 40)
    
    check_display_environment()
    
    # Test basic camera functionality
    camera_works = test_camera_no_preview()
    
    if camera_works:
        print("\n✓ Camera hardware is working")
        
        # Test OpenCV display
        opencv_works = test_opencv_display()
        
        if opencv_works:
            print("✓ OpenCV display is working")
        else:
            print("✗ OpenCV display is not working")
        
        # Test DRM preview
        drm_works = test_camera_with_drm()
        
        if drm_works:
            print("✓ DRM preview is working")
        else:
            print("✗ DRM preview is not working")
    else:
        print("✗ Camera hardware is not working")
    
    print("\nDiagnostic completed.")

if __name__ == "__main__":
    main() 