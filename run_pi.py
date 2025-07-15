#!/usr/bin/env python3
"""
Voice Recognition Door Opener - Raspberry Pi Entry Point
Raspberry Pi 4 voice recognition system for door access control
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from pi_macos.main import main

if __name__ == "__main__":
    main() 