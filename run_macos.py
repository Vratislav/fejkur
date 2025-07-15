#!/usr/bin/env python3
"""
Voice Recognition Door Opener - macOS Version
Runs on macOS for development and testing
Skips GPIO and Bluetooth components
"""

import sys
import os
import signal
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voice_recognizer_base import VoiceRecognizerBase


class MacOSVoiceRecognizer(VoiceRecognizerBase):
    """Voice recognition system for macOS development"""
    
    def __init__(self):
        """Initialize the macOS voice recognition system"""
        super().__init__(platform_name="MacOS")
    
    def platform_initialize(self):
        """Platform-specific initialization for macOS"""
        # macOS doesn't need GPIO or Bluetooth initialization
        self.logger.info("macOS platform initialization complete")
        return True
    
    def platform_run(self):
        """Platform-specific main loop for macOS"""
        # macOS runs in interactive mode
        self.run_interactive_mode()
    
    def platform_shutdown(self):
        """Platform-specific shutdown for macOS"""
        # macOS doesn't need special shutdown procedures
        pass


def main():
    """Main function"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    
    # Create and initialize the recognizer
    recognizer = MacOSVoiceRecognizer()
    recognizer.setup_logging()
    
    # Run the application
    recognizer.run()


if __name__ == "__main__":
    main() 