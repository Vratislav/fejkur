#!/usr/bin/env python3

import subprocess
import os

def fix_display_permissions():
    """Fix display permissions for camera preview"""
    print("Fixing Display Permissions for Camera Preview")
    print("=" * 50)
    
    # Get current user info
    user = os.getenv('USER', 'unknown')
    print(f"Current user: {user}")
    
    # 1. Add user to video group (needed for camera access)
    print("\n1. Adding user to video group...")
    subprocess.run(f"sudo usermod -a -G video {user}", shell=True)
    
    # 2. Fix X11 permissions for sudo
    print("\n2. Setting up X11 authorization...")
    subprocess.run("xhost +local:root", shell=True)
    
    # 3. Set proper DISPLAY variable
    print("\n3. Setting DISPLAY variable...")
    os.environ['DISPLAY'] = ':0'
    
    # 4. Check current permissions
    print("\n4. Checking current setup...")
    subprocess.run("groups", shell=True)
    subprocess.run("echo $DISPLAY", shell=True)
    subprocess.run("xauth list", shell=True)
    
    print("\n5. Instructions:")
    print("Now try running:")
    print("  export DISPLAY=:0")
    print("  python3 test_working_preview.py  # (without sudo)")
    print("  OR")
    print("  sudo -E python3 test_working_preview.py  # (preserve environment)")
    print("  OR")
    print("  sudo DISPLAY=:0 python3 test_working_preview.py")

def test_different_methods():
    """Test different ways to run the camera"""
    print("\nTesting Different Methods")
    print("=" * 30)
    
    methods = [
        "libcamera-hello --timeout 5000",
        "DISPLAY=:0 python3 test_working_preview.py",
        "sudo -E DISPLAY=:0 python3 test_working_preview.py"
    ]
    
    for method in methods:
        print(f"\nTrying: {method}")
        print("Run this command manually and tell me if it works:")
        print(f"  {method}")
        input("Press Enter when you've tried it...")

if __name__ == "__main__":
    fix_display_permissions()
    test_different_methods() 