#!/usr/bin/env python3
"""
Test script for Voice Recognition Door Opener
Tests all system components
"""

import sys
import time
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config_manager import ConfigManager
from core.audio_manager import AudioManager
from core.voice_processor import VoiceProcessor
from core.mqtt_client import MQTTClient
from core.password_manager import PasswordManager
from pi_macos.bluetooth_manager import BluetoothManager
from pi_macos.button_handler import ButtonHandler


def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_config_manager():
    """Test configuration manager"""
    print("\n=== Testing Config Manager ===")
    
    try:
        config = ConfigManager()
        print("✓ Config manager created successfully")
        
        # Test configuration validation
        if config.validate_config():
            print("✓ Configuration validation passed")
        else:
            print("✗ Configuration validation failed")
            return False
        
        # Test getting configuration sections
        audio_config = config.get_audio_config()
        bluetooth_config = config.get_bluetooth_config()
        mqtt_config = config.get_mqtt_config()
        
        print(f"✓ Audio config: {len(audio_config)} settings")
        print(f"✓ Bluetooth config: {len(bluetooth_config)} settings")
        print(f"✓ MQTT config: {len(mqtt_config)} settings")
        
        return True
        
    except Exception as e:
        print(f"✗ Config manager test failed: {e}")
        return False


def test_password_manager():
    """Test password manager"""
    print("\n=== Testing Password Manager ===")
    
    try:
        config = ConfigManager()
        password_manager = PasswordManager(config)
        
        # Test password loading
        if password_manager.load_passwords():
            print("✓ Passwords loaded successfully")
        else:
            print("✗ Failed to load passwords")
            return False
        
        # Test password matching
        test_passwords = ["otevři", "otevři dveře", "invalid password"]
        for test_pwd in test_passwords:
            matches = password_manager.test_password_matching(test_pwd)
            if matches:
                print(f"✓ Password '{test_pwd}' matched: {matches}")
            else:
                print(f"✗ Password '{test_pwd}' no matches")
        
        print(f"✓ Total passwords loaded: {password_manager.get_password_count()}")
        return True
        
    except Exception as e:
        print(f"✗ Password manager test failed: {e}")
        return False


def test_audio_manager():
    """Test audio manager"""
    print("\n=== Testing Audio Manager ===")
    
    try:
        config = ConfigManager()
        audio_manager = AudioManager(config)
        
        # Test initialization
        if audio_manager.initialize():
            print("✓ Audio manager initialized successfully")
        else:
            print("✗ Audio manager initialization failed")
            return False
        
        # Test audio devices
        devices = audio_manager.get_audio_devices()
        print(f"✓ Found {len(devices)} audio devices")
        
        # Test audio playback (if files exist)
        test_sounds = ['prompt', 'success', 'failure', 'error']
        for sound in test_sounds:
            if audio_manager.play_sound(sound):
                print(f"✓ Audio playback test: {sound}")
            else:
                print(f"⚠ Audio playback test: {sound} (file may not exist)")
        
        audio_manager.shutdown()
        return True
        
    except Exception as e:
        print(f"✗ Audio manager test failed: {e}")
        return False


def test_bluetooth_manager():
    """Test Bluetooth manager"""
    print("\n=== Testing Bluetooth Manager ===")
    
    try:
        config = ConfigManager()
        bluetooth_manager = BluetoothManager(config)
        
        # Test initialization
        if bluetooth_manager.initialize():
            print("✓ Bluetooth manager initialized successfully")
        else:
            print("✗ Bluetooth manager initialization failed")
            return False
        
        # Test connection (this may fail if no device is paired)
        if bluetooth_manager.connect():
            print("✓ Bluetooth connection successful")
        else:
            print("⚠ Bluetooth connection failed (no paired devices?)")
        
        bluetooth_manager.shutdown()
        return True
        
    except Exception as e:
        print(f"✗ Bluetooth manager test failed: {e}")
        return False


def test_mqtt_client():
    """Test MQTT client"""
    print("\n=== Testing MQTT Client ===")
    
    try:
        config = ConfigManager()
        mqtt_client = MQTTClient(config)
        
        # Test initialization
        if mqtt_client.initialize():
            print("✓ MQTT client initialized successfully")
        else:
            print("✗ MQTT client initialization failed")
            return False
        
        # Wait for connection
        print("Waiting for MQTT connection...")
        time.sleep(5)
        
        if mqtt_client.is_connected():
            print("✓ MQTT client connected")
            
            # Test connection
            if mqtt_client.test_connection():
                print("✓ MQTT connection test successful")
            else:
                print("✗ MQTT connection test failed")
        else:
            print("⚠ MQTT client not connected (broker may not be available)")
        
        mqtt_client.shutdown()
        return True
        
    except Exception as e:
        print(f"✗ MQTT client test failed: {e}")
        return False


def test_button_handler():
    """Test button handler"""
    print("\n=== Testing Button Handler ===")
    
    try:
        config = ConfigManager()
        button_handler = ButtonHandler(config)
        
        # Test initialization
        if button_handler.initialize():
            print("✓ Button handler initialized successfully")
        else:
            print("✗ Button handler initialization failed")
            return False
        
        # Test button info
        button_info = button_handler.get_button_info()
        print(f"✓ Button pin: {button_info['button_pin']}")
        print(f"✓ LED pin: {button_info['led_pin']}")
        
        # Test LED (if available)
        if button_handler.test_button():
            print("✓ Button test successful")
        else:
            print("⚠ Button test failed (hardware may not be available)")
        
        button_handler.shutdown()
        return True
        
    except Exception as e:
        print(f"✗ Button handler test failed: {e}")
        return False


def test_voice_processor():
    """Test voice processor"""
    print("\n=== Testing Voice Processor ===")
    
    try:
        config = ConfigManager()
        voice_processor = VoiceProcessor(config)
        
        # Test initialization
        if voice_processor.initialize():
            print("✓ Voice processor initialized successfully")
        else:
            print("✗ Voice processor initialization failed")
            print("  Make sure VOSK model is downloaded and path is correct")
            return False
        
        # Test model info
        model_info = voice_processor.get_model_info()
        print(f"✓ Model path: {model_info.get('model_path', 'N/A')}")
        print(f"✓ Sample rate: {model_info.get('sample_rate', 'N/A')}")
        print(f"✓ Language: {model_info.get('language', 'N/A')}")
        
        voice_processor.shutdown()
        return True
        
    except Exception as e:
        print(f"✗ Voice processor test failed: {e}")
        return False


def run_all_tests():
    """Run all system tests"""
    print("Voice Recognition Door Opener - System Test")
    print("=" * 50)
    
    setup_logging()
    
    tests = [
        ("Configuration Manager", test_config_manager),
        ("Password Manager", test_password_manager),
        ("Audio Manager", test_audio_manager),
        ("Bluetooth Manager", test_bluetooth_manager),
        ("MQTT Client", test_mqtt_client),
        ("Button Handler", test_button_handler),
        ("Voice Processor", test_voice_processor),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} test PASSED")
            else:
                print(f"✗ {test_name} test FAILED")
        except Exception as e:
            print(f"✗ {test_name} test ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        return True
    else:
        print("⚠ Some tests failed. Please check the configuration and dependencies.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 