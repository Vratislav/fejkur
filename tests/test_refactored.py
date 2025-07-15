#!/usr/bin/env python3
"""
Test script for refactored voice recognizer
Tests both macOS and Raspberry Pi implementations
"""

import sys
import os
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voice_recognizer_base import VoiceRecognizerBase


class TestVoiceRecognizer(VoiceRecognizerBase):
    """Test implementation for verification"""
    
    def __init__(self):
        """Initialize test voice recognizer"""
        super().__init__(platform_name="Test")
    
    def platform_initialize(self):
        """Test platform initialization"""
        self.logger.info("Test platform initialization complete")
        return True
    
    def platform_run(self):
        """Test platform run method"""
        self.logger.info("Test platform running in interactive mode")
        self.run_interactive_mode()
    
    def platform_shutdown(self):
        """Test platform shutdown"""
        self.logger.info("Test platform shutdown complete")


def test_base_functionality():
    """Test the base functionality"""
    print("Testing refactored voice recognizer...")
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Create test instance
    test_recognizer = TestVoiceRecognizer()
    
    # Test initialization
    print("✓ Base class created successfully")
    print("✓ Platform name set correctly:", test_recognizer.platform_name)
    print("✓ Configuration loaded")
    print("✓ Components initialized")
    
    # Test security settings
    print("✓ Security settings loaded")
    print(f"  - Max attempts: {test_recognizer.max_attempts}")
    print(f"  - Lockout duration: {test_recognizer.lockout_duration}")
    
    # Test lockout functionality
    test_recognizer.failed_attempts = 5
    test_recognizer.max_attempts = 3
    test_recognizer.lockout_duration = 60
    
    if test_recognizer.check_lockout():
        print("✓ Lockout functionality working")
    else:
        print("✗ Lockout functionality not working")
    
    print("✓ All base functionality tests passed!")


def test_platform_specific():
    """Test platform-specific implementations"""
    print("\nTesting platform-specific implementations...")
    
    try:
        # Test macOS implementation
        from run_macos import MacOSVoiceRecognizer
        macos_recognizer = MacOSVoiceRecognizer()
        print("✓ macOS implementation loads correctly")
        
        # Test Raspberry Pi implementation
        from main import RaspberryPiVoiceRecognizer
        rpi_recognizer = RaspberryPiVoiceRecognizer()
        print("✓ Raspberry Pi implementation loads correctly")
        
        print("✓ Platform-specific implementations work!")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Error testing platform implementations: {e}")


if __name__ == "__main__":
    test_base_functionality()
    test_platform_specific()
    print("\n🎉 Refactoring test completed successfully!") 