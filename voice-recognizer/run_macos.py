#!/usr/bin/env python3
"""
Voice Recognition Door Opener - macOS Entry Point
Runs on macOS for development and testing
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from pi_macos.run_macos import main

if __name__ == "__main__":
    main() 