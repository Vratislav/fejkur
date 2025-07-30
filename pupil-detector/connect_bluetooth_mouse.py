#!/usr/bin/env python3

import subprocess
import time
import sys

def run_command(cmd, description=""):
    """Run a command and show the output"""
    print(f"\n--- {description} ---" if description else f"\n--- Running: {cmd} ---")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        print(f"Command: {cmd}")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {cmd}")
        return False
    except Exception as e:
        print(f"Exception running command: {e}")
        return False

def connect_bluetooth_mouse():
    """Guide through connecting a Bluetooth mouse"""
    print("Bluetooth Mouse Connection Helper")
    print("=" * 40)
    
    # Check if Bluetooth is available
    print("1. Checking Bluetooth status...")
    if not run_command("systemctl is-active bluetooth", "Bluetooth Service Status"):
        print("Starting Bluetooth service...")
        run_command("sudo systemctl start bluetooth")
        run_command("sudo systemctl enable bluetooth")
    
    # Check Bluetooth adapter
    run_command("hciconfig", "Bluetooth Adapter Info")
    
    # Make sure Bluetooth is up
    print("\n2. Bringing up Bluetooth adapter...")
    run_command("sudo hciconfig hci0 up")
    
    # Start bluetoothctl in interactive mode
    print("\n3. Starting Bluetooth discovery...")
    print("Put your mouse in pairing mode now!")
    print("(Usually hold a button or turn it on)")
    
    input("Press Enter when your mouse is in pairing mode...")
    
    # Scan for devices
    print("Scanning for Bluetooth devices...")
    run_command("sudo bluetoothctl scan on &", "Start scanning")
    time.sleep(10)  # Scan for 10 seconds
    
    # Show available devices
    print("\n4. Available Bluetooth devices:")
    run_command("bluetoothctl devices", "List discovered devices")
    
    # Interactive pairing
    print("\n5. Manual pairing instructions:")
    print("Run these commands in a separate terminal:")
    print("sudo bluetoothctl")
    print("Then in bluetoothctl:")
    print("  scan on")
    print("  devices  (find your mouse MAC address)")
    print("  pair XX:XX:XX:XX:XX:XX  (replace with your mouse MAC)")
    print("  trust XX:XX:XX:XX:XX:XX")
    print("  connect XX:XX:XX:XX:XX:XX")
    print("  exit")
    
    # Alternative GUI method
    print("\n6. Alternative - GUI method:")
    print("If you have desktop access, try:")
    print("  sudo blueman-manager")
    print("  or")
    print("  sudo bluetooth-wizard")
    
    # Test mouse after connection
    print("\n7. After connecting, test with:")
    print("  cat /proc/bus/input/devices | grep -A 5 mouse")
    print("  or")
    print("  xinput list")

def quick_bluetooth_scan():
    """Quick scan and attempt to connect common mouse devices"""
    print("Quick Bluetooth Mouse Connection")
    print("=" * 35)
    
    # Enable and start scanning
    run_command("sudo hciconfig hci0 up")
    run_command("sudo bluetoothctl power on")
    run_command("sudo bluetoothctl agent on")
    run_command("sudo bluetoothctl default-agent")
    
    print("Starting 15-second scan...")
    print("Make sure your mouse is in pairing mode!")
    
    # Start scan
    scan_process = subprocess.Popen(["sudo", "bluetoothctl", "scan", "on"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
    
    time.sleep(15)  # Scan for 15 seconds
    
    # Stop scan and get devices
    run_command("sudo bluetoothctl scan off")
    
    # List devices
    result = subprocess.run(["bluetoothctl", "devices"], 
                          capture_output=True, text=True)
    
    if result.stdout:
        print("\nFound devices:")
        devices = result.stdout.strip().split('\n')
        mouse_devices = []
        
        for device in devices:
            if any(keyword in device.lower() for keyword in ['mouse', 'mice', 'pointer', 'mx', 'logitech']):
                mouse_devices.append(device)
                print(f"  Potential mouse: {device}")
        
        if mouse_devices:
            print(f"\nFound {len(mouse_devices)} potential mouse device(s)")
            for i, device in enumerate(mouse_devices):
                mac = device.split()[1]  # Extract MAC address
                print(f"\nTrying to pair with device {i+1}: {mac}")
                run_command(f"sudo bluetoothctl pair {mac}")
                run_command(f"sudo bluetoothctl trust {mac}")
                run_command(f"sudo bluetoothctl connect {mac}")
        else:
            print("No obvious mouse devices found. Try the manual method.")
    else:
        print("No devices found in scan.")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_bluetooth_scan()
    else:
        connect_bluetooth_mouse()

if __name__ == "__main__":
    main() 