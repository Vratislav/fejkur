#!/usr/bin/env python3
"""
Test script for new folder structure
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def test_imports():
    """Test that all imports work with the new structure"""
    print("Testing imports with new folder structure...")
    
    try:
        # Test core imports
        from core.voice_recognizer_base import VoiceRecognizerBase
        from core.config_manager import ConfigManager
        from core.audio_manager import AudioManager
        from core.voice_processor import VoiceProcessor
        from core.password_manager import PasswordManager
        from core.mqtt_client import MQTTClient
        print("✓ Core imports successful")
        
        # Test pi_macos imports
        from pi_macos.bluetooth_manager import BluetoothManager
        from pi_macos.button_handler import ButtonHandler
        print("✓ pi_macos imports successful")
        
        # Test utils imports
        import utils.list_audio_devices
        print("✓ Utils imports successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration loading...")
    
    try:
        from core.config_manager import ConfigManager
        config = ConfigManager()
        print("✓ Configuration loaded successfully")
        
        # Test some config values
        audio_config = config.get_audio_config()
        print(f"✓ Audio sample rate: {audio_config.get('sample_rate')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_structure():
    """Test folder structure"""
    print("\nTesting folder structure...")
    
    expected_dirs = [
        'src',
        'src/core',
        'src/pi_macos', 
        'src/utils',
        'scripts',
        'tests',
        'config',
        'models',
        'sounds',
        'docs',
        'deployment'
    ]
    
    for dir_path in expected_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ Missing: {dir_path}/")
            return False
    
    return True

if __name__ == "__main__":
    print("Testing new folder structure...\n")
    
    structure_ok = test_structure()
    imports_ok = test_imports()
    config_ok = test_config()
    
    if structure_ok and imports_ok and config_ok:
        print("\n🎉 All tests passed! New folder structure is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.") 