#!/usr/bin/env python3
"""
Audio Debugging Script
Helps diagnose microphone and Bluetooth audio issues
"""

import pyaudio
import numpy as np
import time
import subprocess
import sys

def list_audio_devices():
    """List all available audio devices"""
    print("🎵 AUDIO DEVICES")
    print("=" * 50)
    
    p = pyaudio.PyAudio()
    
    print(f"Default input device: {p.get_default_input_device_info()['name']}")
    print(f"Default output device: {p.get_default_output_device_info()['name']}")
    print()
    
    print("All input devices:")
    for i in range(p.get_device_count()):
        try:
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                print(f"  {i}: {device_info['name']}")
                print(f"      Channels: {device_info['maxInputChannels']}")
                print(f"      Sample Rate: {device_info['defaultSampleRate']}")
                print(f"      Host API: {device_info['hostApi']}")
                print()
        except Exception as e:
            print(f"  {i}: Error getting device info: {e}")
    
    p.terminate()

def test_microphone_levels(device_index=None, duration=5):
    """Test microphone levels and show real-time audio levels"""
    print("🎤 MICROPHONE LEVEL TEST")
    print("=" * 50)
    
    p = pyaudio.PyAudio()
    
    if device_index is None:
        device_index = p.get_default_input_device_info()['index']
    
    try:
        device_info = p.get_device_info_by_index(device_index)
        print(f"Testing device: {device_info['name']}")
        print(f"Sample rate: {device_info['defaultSampleRate']}")
        print(f"Channels: {device_info['maxInputChannels']}")
        print()
        
        # Open stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=int(device_info['defaultSampleRate']),
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024
        )
        
        print("🎤 Recording for 5 seconds... Speak into the microphone!")
        print("Audio levels (should increase when you speak):")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                data = stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                level = np.max(np.abs(audio_data))
                normalized_level = level / 32767.0
                
                # Create a visual level indicator
                bars = int(normalized_level * 50)
                bar_str = "█" * bars + "░" * (50 - bars)
                
                print(f"\rLevel: {normalized_level:.3f} [{bar_str}] {level:6d}", end="", flush=True)
                
            except Exception as e:
                print(f"\nError reading audio: {e}")
                break
        
        print("\n\n✅ Microphone test complete!")
        
    except Exception as e:
        print(f"❌ Error testing microphone: {e}")
    finally:
        try:
            stream.stop_stream()
            stream.close()
        except:
            pass
        p.terminate()

def check_bluetooth_status():
    """Check Bluetooth status and connected devices"""
    print("📱 BLUETOOTH STATUS")
    print("=" * 50)
    
    try:
        # Check if Bluetooth is enabled
        result = subprocess.run(['bluetoothctl', 'show'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Bluetooth is enabled")
            print(result.stdout)
        else:
            print("❌ Bluetooth is not enabled or not available")
            return False
    except FileNotFoundError:
        print("❌ bluetoothctl not found. Install bluetooth package.")
        return False
    
    print("\n📱 Connected devices:")
    try:
        result = subprocess.run(['bluetoothctl', 'devices', 'Connected'], capture_output=True, text=True)
        if result.returncode == 0:
            if result.stdout.strip():
                print(result.stdout)
            else:
                print("❌ No devices connected")
        else:
            print("❌ Error getting connected devices")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n📱 Available devices:")
    try:
        result = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ Error getting available devices")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_audio_device_selection():
    """Test different audio devices to find the right one"""
    print("🔍 AUDIO DEVICE SELECTION TEST")
    print("=" * 50)
    
    p = pyaudio.PyAudio()
    
    input_devices = []
    for i in range(p.get_device_count()):
        try:
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append((i, device_info))
        except:
            continue
    
    print(f"Found {len(input_devices)} input devices:")
    for i, (device_id, device_info) in enumerate(input_devices):
        print(f"{i+1}. {device_info['name']} (ID: {device_id})")
    
    print("\nTesting each device for 3 seconds...")
    
    for i, (device_id, device_info) in enumerate(input_devices):
        print(f"\n🎤 Testing device {i+1}: {device_info['name']}")
        print("Speak into the microphone for 3 seconds...")
        
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=int(device_info['defaultSampleRate']),
                input=True,
                input_device_index=device_id,
                frames_per_buffer=1024
            )
            
            start_time = time.time()
            max_level = 0
            
            while time.time() - start_time < 3:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    level = np.max(np.abs(audio_data))
                    max_level = max(max_level, level)
                    
                    bars = int((level / 32767.0) * 30)
                    bar_str = "█" * bars + "░" * (30 - bars)
                    print(f"\rLevel: {level:6d} [{bar_str}]", end="", flush=True)
                    
                except Exception as e:
                    print(f"\nError: {e}")
                    break
            
            print(f"\nMax level: {max_level}")
            if max_level > 1000:
                print("✅ Device appears to be working")
            else:
                print("❌ Device may not be receiving audio")
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"❌ Error testing device: {e}")
    
    p.terminate()

def main():
    """Main debugging function"""
    print("🔧 AUDIO DEBUGGING TOOL")
    print("=" * 50)
    
    while True:
        print("\nSelect a test:")
        print("1. List audio devices")
        print("2. Test microphone levels")
        print("3. Check Bluetooth status")
        print("4. Test all audio devices")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            list_audio_devices()
        elif choice == '2':
            device_index = input("Enter device index (or press Enter for default): ").strip()
            if device_index:
                test_microphone_levels(int(device_index))
            else:
                test_microphone_levels()
        elif choice == '3':
            check_bluetooth_status()
        elif choice == '4':
            test_audio_device_selection()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main() 