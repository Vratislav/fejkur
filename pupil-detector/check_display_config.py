#!/usr/bin/env python3

import subprocess
import os
import glob

def run_cmd(cmd, description=""):
    """Run command and return output"""
    print(f"\n--- {description or cmd} ---")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        print(f"Failed to run: {e}")
        return "", str(e), -1

def check_display_configuration():
    """Comprehensive display configuration check"""
    print("Pi Display Configuration Check")
    print("=" * 40)
    
    # 1. Basic system info
    run_cmd("uname -a", "System Information")
    run_cmd("cat /proc/device-tree/model", "Pi Model")
    
    # 2. Display hardware detection
    print("\n" + "="*40)
    print("DISPLAY HARDWARE")
    print("="*40)
    
    run_cmd("tvservice -s", "HDMI Status")
    run_cmd("tvservice -m CEA", "Supported CEA Modes")
    run_cmd("tvservice -m DMT", "Supported DMT Modes")
    run_cmd("vcgencmd display_power", "Display Power Status")
    
    # 3. Framebuffer info
    print("\n" + "="*40)
    print("FRAMEBUFFER")
    print("="*40)
    
    run_cmd("cat /sys/class/graphics/fb0/virtual_size", "Virtual Size")
    run_cmd("cat /sys/class/graphics/fb0/bits_per_pixel", "Bits Per Pixel")
    run_cmd("fbset", "Framebuffer Settings")
    
    # 4. Boot config
    print("\n" + "="*40)
    print("BOOT CONFIGURATION")
    print("="*40)
    
    if os.path.exists("/boot/config.txt"):
        run_cmd("grep -E '^(hdmi_|display_|gpu_mem)' /boot/config.txt", "HDMI/Display Config")
    elif os.path.exists("/boot/firmware/config.txt"):
        run_cmd("grep -E '^(hdmi_|display_|gpu_mem)' /boot/firmware/config.txt", "HDMI/Display Config")
    
    # 5. X11 and Wayland status
    print("\n" + "="*40)
    print("DISPLAY SERVERS")
    print("="*40)
    
    run_cmd("ps aux | grep -E '(Xorg|wayland|weston)' | grep -v grep", "Running Display Servers")
    run_cmd("systemctl is-active lightdm", "LightDM Status")
    run_cmd("systemctl is-active gdm", "GDM Status")
    run_cmd("echo $XDG_SESSION_TYPE", "Session Type")
    
    # 6. Environment variables
    print("\n" + "="*40)
    print("ENVIRONMENT")
    print("="*40)
    
    env_vars = ['DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'XDG_SESSION_TYPE']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"{var}: {value}")
    
    # 7. DRM/KMS info
    print("\n" + "="*40)
    print("DRM/KMS")
    print("="*40)
    
    run_cmd("ls -la /dev/dri/", "DRM Devices")
    run_cmd("cat /sys/module/vc4/parameters/hdmi_debug", "VC4 HDMI Debug")
    
    # 8. Current display processes
    print("\n" + "="*40)
    print("DISPLAY PROCESSES")
    print("="*40)
    
    run_cmd("ps aux | grep -E '(camera|preview|display)' | grep -v grep", "Camera/Display Processes")
    
    # 9. Input devices (mouse check)
    print("\n" + "="*40)
    print("INPUT DEVICES")
    print("="*40)
    
    run_cmd("cat /proc/bus/input/devices | grep -A 5 -B 5 mouse", "Mouse Devices")
    run_cmd("xinput list 2>/dev/null || echo 'xinput not available'", "X Input Devices")
    
    # 10. Test simple display
    print("\n" + "="*40)
    print("DISPLAY TEST")
    print("="*40)
    
    print("Testing if we can open a display...")
    
    # Try to get display info
    run_cmd("xrandr 2>/dev/null || echo 'xrandr not available'", "Display Resolution Info")
    run_cmd("xdpyinfo 2>/dev/null || echo 'xdpyinfo not available'", "X Display Info")
    
    # Check if desktop is visible
    print("\nCan you see a desktop with mouse cursor? (y/n)")
    desktop_visible = input().lower().startswith('y')
    
    if desktop_visible:
        print("✓ Desktop is visible - display hardware is working")
        print("Issue is likely with camera preview configuration")
    else:
        print("✗ Desktop not visible - display configuration issue")
        print("Need to fix basic display first")
    
    # 11. Recommendations
    print("\n" + "="*40)
    print("RECOMMENDATIONS")
    print("="*40)
    
    if desktop_visible:
        print("Since desktop is visible, try these camera preview fixes:")
        print("1. Set DISPLAY environment variable:")
        print("   export DISPLAY=:0")
        print("2. Run camera preview as the desktop user (not root)")
        print("3. Try: libcamera-hello --display 0")
        print("4. Check: sudo usermod -a -G video $USER")
    else:
        print("Fix display first:")
        print("1. Check HDMI cable connection")
        print("2. Try: sudo raspi-config -> Advanced -> Resolution")
        print("3. Check /boot/config.txt for hdmi_force_hotplug=1")
        print("4. Reboot and check again")

if __name__ == "__main__":
    check_display_configuration() 