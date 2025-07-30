#!/usr/bin/env python3

import os
import time
from picamera2 import Picamera2

# Clear any SSH forwarding
os.environ.pop('DISPLAY', None)
os.environ.pop('SSH_CLIENT', None)

def test_method_1_basic_preview():
    """Test Method 1: Basic start_preview()"""
    print("\n=== Method 1: Basic Preview ===")
    try:
        camera = Picamera2()
        config = camera.create_preview_configuration(main={"size": (640, 480)})
        camera.configure(config)
        
        camera.start_preview()
        camera.start()
        
        print("Basic preview started. Check Pi's HDMI display...")
        time.sleep(5)
        
        camera.stop_preview()
        camera.stop()
        print("Method 1 completed")
        return True
    except Exception as e:
        print(f"Method 1 failed: {e}")
        return False

def test_method_2_drm_preview():
    """Test Method 2: DRM Preview"""
    print("\n=== Method 2: DRM Preview ===")
    try:
        from picamera2.previews import DrmPreview
        
        camera = Picamera2()
        preview = DrmPreview(camera)
        
        config = camera.create_preview_configuration(main={"size": (640, 480)})
        camera.configure(config)
        camera.start()
        
        print("DRM preview started. Check Pi's HDMI display...")
        time.sleep(5)
        
        camera.stop()
        print("Method 2 completed")
        return True
    except Exception as e:
        print(f"Method 2 failed: {e}")
        return False

def test_method_3_qt_preview():
    """Test Method 3: Qt Preview with local display"""
    print("\n=== Method 3: Qt Preview ===")
    try:
        from picamera2.previews import QtPreview
        
        # Set Qt to use local framebuffer
        os.environ['QT_QPA_PLATFORM'] = 'linuxfb'
        
        camera = Picamera2()
        preview = QtPreview(camera)
        
        config = camera.create_preview_configuration(main={"size": (640, 480)})
        camera.configure(config)
        camera.start()
        
        print("Qt preview started. Check Pi's HDMI display...")
        time.sleep(5)
        
        camera.stop()
        print("Method 3 completed")
        return True
    except Exception as e:
        print(f"Method 3 failed: {e}")
        return False

def test_method_4_null_preview():
    """Test Method 4: Null preview (should work for capture)"""
    print("\n=== Method 4: No Preview (Capture Only) ===")
    try:
        from picamera2.previews import NullPreview
        
        camera = Picamera2()
        preview = NullPreview(camera)
        
        config = camera.create_preview_configuration(main={"size": (640, 480)})
        camera.configure(config)
        camera.start()
        
        # Capture a frame to verify camera works
        frame = camera.capture_array()
        print(f"Captured frame shape: {frame.shape}")
        print("Camera capture working (no preview)")
        
        camera.stop()
        print("Method 4 completed")
        return True
    except Exception as e:
        print(f"Method 4 failed: {e}")
        return False

def check_display_devices():
    """Check available display devices"""
    print("\n=== Display Device Check ===")
    
    # Check framebuffer devices
    try:
        import glob
        fb_devices = glob.glob('/dev/fb*')
        print(f"Framebuffer devices: {fb_devices}")
    except:
        print("Could not check framebuffer devices")
    
    # Check DRM devices
    try:
        drm_devices = glob.glob('/dev/dri/*')
        print(f"DRM devices: {drm_devices}")
    except:
        print("Could not check DRM devices")
    
    # Check if running in console or desktop
    try:
        with open('/proc/self/stat', 'r') as f:
            stat = f.read()
        print(f"Process info available")
    except:
        print("Could not read process info")

def main():
    print("Pi Display Method Testing")
    print("=" * 40)
    
    check_display_devices()
    
    # Try each method
    methods = [
        test_method_1_basic_preview,
        test_method_2_drm_preview, 
        test_method_3_qt_preview,
        test_method_4_null_preview
    ]
    
    working_methods = []
    
    for method in methods:
        try:
            if method():
                working_methods.append(method.__name__)
        except Exception as e:
            print(f"Exception in {method.__name__}: {e}")
    
    print(f"\n=== Results ===")
    if working_methods:
        print(f"Working methods: {working_methods}")
    else:
        print("No display methods worked!")
    
    print("Testing completed.")

if __name__ == "__main__":
    main() 