#!/usr/bin/env python3
"""
Voice Recognition Door Opener - Raspberry Pi Version
Raspberry Pi 4 voice recognition system for door access control
"""

import sys
import os
import time
import signal
import logging
import threading
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_recognizer_base import VoiceRecognizerBase
from bluetooth_manager import BluetoothManager
from button_handler import ButtonHandler


class RaspberryPiVoiceRecognizer(VoiceRecognizerBase):
    """Voice recognition system for Raspberry Pi"""
    
    def __init__(self):
        """Initialize the Raspberry Pi voice recognition system"""
        super().__init__(platform_name="RaspberryPi")
        
        # Initialize Raspberry Pi specific components
        self.bluetooth_manager = BluetoothManager(self.config)
        self.button_handler = ButtonHandler(self.config)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def platform_initialize(self):
        """Platform-specific initialization for Raspberry Pi"""
        try:
            self.logger.info("Initializing Raspberry Pi specific components...")
            
            # Initialize Bluetooth
            if not self.bluetooth_manager.initialize():
                self.logger.error("Failed to initialize Bluetooth")
                return False
            
            # Initialize button handler
            if not self.button_handler.initialize():
                self.logger.error("Failed to initialize button handler")
                return False
            
            # Connect to Bluetooth device
            if not self.bluetooth_manager.connect():
                self.logger.error("Failed to connect to Bluetooth device")
                return False
            
            self.logger.info("Raspberry Pi platform initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Raspberry Pi components: {e}")
            return False
    
    def platform_run(self):
        """Platform-specific main loop for Raspberry Pi"""
        self.logger.info("System ready - waiting for button press")
        
        # Set up button callback
        self.button_handler.set_callback(self.handle_trigger_event)
        
        try:
            while self.running:
                time.sleep(0.1)  # Small sleep to prevent CPU spinning
                
                # Check for Bluetooth connection issues (only if not shutting down)
                if self.running and not self.bluetooth_manager.is_connected:
                    self.logger.warning("Bluetooth disconnected, attempting reconnect...")
                    if not self.bluetooth_manager.connect():
                        self.logger.error("Failed to reconnect Bluetooth")
                        time.sleep(5)  # Wait before retry
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
    
    def platform_shutdown(self):
        """Platform-specific shutdown for Raspberry Pi"""
        try:
            self.button_handler.shutdown()
            self.bluetooth_manager.shutdown()
        except Exception as e:
            self.logger.error(f"Error during Raspberry Pi shutdown: {e}")


def main():
    """Main entry point"""
    app = RaspberryPiVoiceRecognizer()
    app.run()


if __name__ == "__main__":
    main() 