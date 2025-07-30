#!/usr/bin/env python3

import os
import subprocess
import glob

def check_pi_environment():
    """Check the Pi's environment and suggest solutions"""
    print("=== Raspberry Pi Display Environment Check ===")
    
    # Check if we're actually on a Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        if 'Raspberry Pi' in cpuinfo:
            print("✓ Running on Raspberry Pi")
        else:
            print("✗ Not running on Raspberry Pi")
            return
    except:
        print("? Could not determine if this is a Pi")
    
    # Check display manager
    print("\n--- Display Manager Check ---")
    try:
        result = subprocess.run(['systemctl', 'is-active', 'lightdm'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ LightDM is running")
        else:
            print("✗ LightDM is not running")
    except:
        print("? Could not check LightDM")
    
    # Check if desktop is running
    try:
        result = subprocess.run(['pgrep', '-f', 'lxsession'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Desktop session is running")
        else:
            print("✗ No desktop session found")
    except:
        print("? Could not check desktop session")
    
    # Check current user and groups
    print(f"\n--- User Info ---")
    print(f"Current user: {os.getenv('USER', 'unknown')}")
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        print(f"User groups: {result.stdout.strip()}")
        
        if 'video' in result.stdout:
            print("✓ User is in video group")
        else:
            print("✗ User NOT in video group")
            print("  Fix: sudo usermod -a -G video $USER")
    except:
        print("? Could not check user groups")
    
    # Check display devices
    print(f"\n--- Display Devices ---")
    fb_devices = glob.glob('/dev/fb*')
    print(f"Framebuffer devices: {fb_devices}")
    
    drm_devices = glob.glob('/dev/dri/*')
    print(f"DRM devices: {drm_devices}")
    
    # Check GPU memory split
    try:
        result = subprocess.run(['vcgencmd', 'get_mem', 'gpu'], 
                              capture_output=True, text=True)
        gpu_mem = result.stdout.strip()
        print(f"GPU memory: {gpu_mem}")
        
        if 'gpu=64' in gpu_mem or 'gpu=128' in gpu_mem or 'gpu=256' in gpu_mem:
            print("✓ GPU has sufficient memory")
        else:
            print("✗ GPU might need more memory")
            print("  Fix: Add 'gpu_mem=128' to /boot/config.txt")
    except:
        print("? Could not check GPU memory")
    
    # Check camera
    try:
        result = subprocess.run(['vcgencmd', 'get_camera'], 
                              capture_output=True, text=True)
        camera_status = result.stdout.strip()
        print(f"Camera status: {camera_status}")
        
        if 'detected=1' in camera_status and 'supported=1' in camera_status:
            print("✓ Camera is detected and supported")
        else:
            print("✗ Camera issue detected")
    except:
        print("? Could not check camera status")
    
    # Suggestions
    print(f"\n--- Suggestions ---")
    print("1. Try running without SSH X11 forwarding:")
    print("   ssh fejkur@fejkur.local  # (no -X flag)")
    print("2. Or try running directly on the Pi console (not via SSH)")
    print("3. Make sure you're in the video group")
    print("4. Check if raspi-config has camera and GPU settings correct")

if __name__ == "__main__":
    check_pi_environment() 