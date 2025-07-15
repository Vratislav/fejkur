#!/usr/bin/env python3
"""
List available audio devices for input and output
"""

import pyaudio
import sys

def list_audio_devices():
    """List all available audio devices"""
    p = pyaudio.PyAudio()
    
    print("Available Audio Devices:")
    print("=" * 50)
    
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        
        # Determine device type
        device_type = []
        if device_info['maxInputChannels'] > 0:
            device_type.append("INPUT")
        if device_info['maxOutputChannels'] > 0:
            device_type.append("OUTPUT")
        
        device_type_str = "/".join(device_type)
        
        print(f"Device {i}: {device_info['name']}")
        print(f"  Type: {device_type_str}")
        print(f"  Sample Rate: {device_info['defaultSampleRate']} Hz")
        print(f"  Input Channels: {device_info['maxInputChannels']}")
        print(f"  Output Channels: {device_info['maxOutputChannels']}")
        print()
    
    # Show default devices
    try:
        default_input = p.get_default_input_device_info()
        print(f"Default Input: {default_input['name']} (Device {default_input['index']})")
    except Exception as e:
        print(f"Default Input: Error - {e}")
    
    try:
        default_output = p.get_default_output_device_info()
        print(f"Default Output: {default_output['name']} (Device {default_output['index']})")
    except Exception as e:
        print(f"Default Output: Error - {e}")
    
    p.terminate()

if __name__ == "__main__":
    list_audio_devices() 