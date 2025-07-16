#!/usr/bin/env python3
"""
Test script for audio playback system
"""

import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config_manager import ConfigManager
from core.audio_manager import AudioManager


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_sound_system():
    """Test the enhanced sound system"""
    print("Testing Enhanced Sound System")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    
    try:
        # Initialize config and audio manager
        config = ConfigManager()
        audio_manager = AudioManager(config)
        
        if not audio_manager.initialize():
            print("Failed to initialize audio manager")
            return False
        
        print(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"After 10pm: {audio_manager._is_after_10pm()}")
        print()
        
        # Test sound file discovery
        sound_types = ['prompt', 'success', 'fail']
        
        for sound_type in sound_types:
            print(f"Testing {sound_type} sounds:")
            sound_files = audio_manager._get_sound_files(sound_type)
            
            if sound_files:
                print(f"  Found {len(sound_files)} files:")
                for i, file in enumerate(sound_files):
                    print(f"    {i+1}. {os.path.basename(file)}")
                
                # Test cycling
                print("  Testing cycling:")
                for i in range(min(3, len(sound_files))):
                    next_file = audio_manager._get_next_sound_file(sound_type)
                    if next_file:
                        print(f"    Cycle {i+1}: {os.path.basename(next_file)}")
            else:
                print(f"  No sound files found for {sound_type}")
            
            print()
        
        # Test actual playback
        print("Testing sound playback (will play each sound type once):")
        for sound_type in sound_types:
            print(f"Playing {sound_type} sound...")
            success = audio_manager.play_sound(sound_type)
            if success:
                print(f"  ✓ {sound_type} sound played successfully")
            else:
                print(f"  ✗ Failed to play {sound_type} sound")
            time.sleep(1)  # Brief pause between sounds
        
        print("\nSound system test completed!")
        return True
        
    except Exception as e:
        print(f"Error during sound system test: {e}")
        return False


if __name__ == "__main__":
    success = test_sound_system()
    sys.exit(0 if success else 1) 