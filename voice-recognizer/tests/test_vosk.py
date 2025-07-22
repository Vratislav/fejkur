#!/usr/bin/env python3
"""
Test script for VOSK speech recognition
"""

import sys
import time
import logging
import numpy as np
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config_manager import ConfigManager
from core.voice_processor import VoiceProcessor
from core.audio_manager import AudioManager


def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def setup_bluetooth_audio():
    """Ensure Bluetooth headset is connected and audio profile is set"""
    from bluetooth_manager import BluetoothManager
    config = ConfigManager()
    bt = BluetoothManager(config)
    bt.initialize()
    bt.connect()
    bt.ensure_audio_profile()


def test_vosk_recognition():
    """Test VOSK speech recognition and show raw output, looping until user quits"""
    print("🎤 VOSK Speech Recognition Test")
    print("=" * 50)
    
    try:
        setup_bluetooth_audio()
        # Initialize components
        config = ConfigManager()
        audio_manager = AudioManager(config)
        voice_processor = VoiceProcessor(config)
        
        # Initialize audio
        if not audio_manager.initialize():
            print("❌ Failed to initialize audio manager")
            return False
        
        # Initialize voice processor
        if not voice_processor.initialize():
            print("❌ Failed to initialize voice processor")
            print("   Make sure VOSK model is downloaded and path is correct")
            return False
        
        print("✅ Components initialized successfully")
        
        # Show model info
        model_info = voice_processor.get_model_info()
        print(f"📁 Model path: {model_info.get('model_path', 'N/A')}")
        print(f"🎵 Sample rate: {model_info.get('sample_rate', 'N/A')}")
        print(f"🌍 Language: {model_info.get('language', 'N/A')}")
        
        while True:
            print("\n🎤 Ready to record! Press Enter to start recording, or 'q' then Enter to quit...")
            user_input = input()
            if user_input.strip().lower() == 'q':
                print("👋 Exiting test.")
                break
            
            # Record audio
            print("🔴 Recording... (speak now)")
            audio_data = audio_manager.record_audio()
            
            if audio_data is None:
                print("❌ Failed to record audio")
                continue
            
            print(f"✅ Recorded {len(audio_data)} samples ({len(audio_data) / 16000:.2f} seconds)")
            
            # Process with VOSK
            print("\n🔍 Processing with VOSK...")
            recognized_text = voice_processor.recognize_speech(audio_data)
            
            print("\n📝 RESULTS:")
            print("=" * 30)
            
            if recognized_text:
                print(f"✅ Recognized text: '{recognized_text}'")
            else:
                print("❌ No speech recognized")
            
            # Get detailed results with alternatives
            print("\n🔍 DETAILED VOSK RESULTS:")
            print("=" * 40)
            
            alternatives = voice_processor.recognize_speech_with_alternatives(audio_data)
            
            if alternatives:
                for i, alt in enumerate(alternatives, 1):
                    confidence = alt.get('confidence', 0.0)
                    text = alt.get('text', '')
                    print(f"{i}. '{text}' (confidence: {confidence:.3f})")
            else:
                print("❌ No alternatives found")
            
            # Test password matching
            if recognized_text:
                print("\n🔐 PASSWORD MATCHING TEST:")
                print("=" * 35)
                
                from password_manager import PasswordManager
                password_manager = PasswordManager(config)
                password_manager.load_passwords()
                
                matches = password_manager.test_password_matching(recognized_text)
                if matches:
                    print(f"✅ Password matches: {matches}")
                else:
                    print("❌ No password matches found")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            audio_manager.shutdown()
            voice_processor.shutdown()
        except:
            pass


def test_vosk_with_file(audio_file):
    """Test VOSK with an existing audio file"""
    print(f"🎤 VOSK Test with audio file: {audio_file}")
    print("=" * 50)
    
    try:
        import wave
        
        # Load audio file
        with wave.open(audio_file, 'rb') as wf:
            audio_data = wf.readframes(wf.getnframes())
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        print(f"✅ Loaded audio file: {len(audio_array)} samples")
        
        # Initialize voice processor
        config = ConfigManager()
        voice_processor = VoiceProcessor(config)
        
        if not voice_processor.initialize():
            print("❌ Failed to initialize voice processor")
            return False
        
        # Process with VOSK
        print("🔍 Processing with VOSK...")
        recognized_text = voice_processor.recognize_speech(audio_array)
        
        print("\n📝 RESULTS:")
        print("=" * 30)
        
        if recognized_text:
            print(f"✅ Recognized text: '{recognized_text}'")
        else:
            print("❌ No speech recognized")
        
        # Get alternatives
        alternatives = voice_processor.recognize_speech_with_alternatives(audio_array)
        
        if alternatives:
            print("\n🔍 ALTERNATIVES:")
            for i, alt in enumerate(alternatives, 1):
                confidence = alt.get('confidence', 0.0)
                text = alt.get('text', '')
                print(f"{i}. '{text}' (confidence: {confidence:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_vosk_continuous():
    """Test VOSK continuous recognition from microphone"""
    print("🎤 VOSK Continuous Recognition Test")
    print("=" * 50)
    try:
        setup_bluetooth_audio()
        config = ConfigManager()
        audio_manager = AudioManager(config)
        voice_processor = VoiceProcessor(config)
        if not audio_manager.initialize():
            print("❌ Failed to initialize audio manager")
            return False
        if not voice_processor.initialize():
            print("❌ Failed to initialize voice processor")
            return False
        print("✅ Components initialized successfully")
        print("\n🎤 Listening! Press Enter to stop...")
        stop = [False]
        import threading
        def wait_for_enter():
            input()
            stop[0] = True
        t = threading.Thread(target=wait_for_enter)
        t.daemon = True
        t.start()
        voice_processor.recognize_continuous(audio_manager, stop_callback=lambda: stop[0])
        print("👋 Continuous recognition stopped.")
        return True
    except Exception as e:
        print(f"❌ Error during continuous test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    setup_logging()
    print("Select test mode:")
    print("1. Single-shot recognition (default)")
    print("2. Continuous recognition (streaming)")
    mode = input("Enter 1 or 2: ").strip()
    if len(sys.argv) > 1:
        # Test with audio file
        audio_file = sys.argv[1]
        test_vosk_with_file(audio_file)
    elif mode == '2':
        test_vosk_continuous()
    else:
        test_vosk_recognition()


if __name__ == "__main__":
    main() 