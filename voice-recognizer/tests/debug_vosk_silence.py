#!/usr/bin/env python3
"""
Debug script for VOSK silence detection and parameters
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


def test_vosk_with_background_noise():
    """Test VOSK with background noise to understand silence detection"""
    print("🔍 VOSK Background Noise Detection Test")
    print("=" * 50)
    
    try:
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
            return False
        
        print("✅ Components initialized successfully")
        print("\n🎤 Starting continuous recognition...")
        print("📝 This will show you exactly what VOSK is detecting")
        print("🔊 Try having a phone call or background noise")
        print("⏹️  Press Ctrl+C to stop")
        
        # Test continuous recognition with detailed output
        import queue
        import threading
        
        # Open input stream
        p = audio_manager.pyaudio
        stream = p.open(
            format=audio_manager.format,
            channels=audio_manager.channels,
            rate=audio_manager.sample_rate,
            input=True,
            frames_per_buffer=audio_manager.chunk_size
        )
        
        chunk_count = 0
        last_partial_time = time.time()
        
        try:
            while True:
                data = stream.read(audio_manager.chunk_size, exception_on_overflow=False)
                chunk_count += 1
                
                # Check if we have a final result
                if voice_processor.recognizer.AcceptWaveform(data):
                    result = voice_processor.recognizer.Result()
                    if result:
                        print(f"\n🎯 FINAL RESULT: {result}")
                    else:
                        print(f"\n🔇 FINAL (empty): {result}")
                else:
                    # Check partial result
                    partial = voice_processor.recognizer.PartialResult()
                    current_time = time.time()
                    
                    # Only show partial if it's not empty or if it's been a while
                    if partial.strip() or (current_time - last_partial_time) > 2.0:
                        print(f"\n📝 PARTIAL: {partial}")
                        last_partial_time = current_time
                
                # Show chunk count every 100 chunks (about 6 seconds at 16kHz)
                if chunk_count % 100 == 0:
                    print(f"\n📊 Processed {chunk_count} chunks ({chunk_count * 1024 / 16000:.1f}s of audio)")
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping recognition...")
        finally:
            stream.stop_stream()
            stream.close()
        
        print(f"\n📊 Total chunks processed: {chunk_count}")
        print(f"⏱️  Total time: {chunk_count * 1024 / 16000:.1f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vosk_parameters():
    """Test different VOSK parameters"""
    print("🔧 VOSK Parameters Test")
    print("=" * 30)
    
    try:
        config = ConfigManager()
        voice_processor = VoiceProcessor(config)
        
        if not voice_processor.initialize():
            print("❌ Failed to initialize voice processor")
            return False
        
        print("📋 Current VOSK Configuration:")
        print(f"   Sample Rate: {voice_processor.sample_rate}")
        print(f"   Confidence Threshold: {voice_processor.confidence_threshold}")
        print(f"   Max Alternatives: {voice_processor.max_alternatives}")
        print(f"   Language: {voice_processor.language}")
        
        # Test with different confidence thresholds
        print("\n🧪 Testing different confidence thresholds...")
        
        original_threshold = voice_processor.confidence_threshold
        
        for threshold in [0.1, 0.3, 0.5, 0.7, 0.9]:
            voice_processor.confidence_threshold = threshold
            print(f"   Confidence threshold: {threshold}")
        
        # Restore original threshold
        voice_processor.confidence_threshold = original_threshold
        
        return True
        
    except Exception as e:
        print(f"❌ Error during parameter test: {e}")
        return False


def main():
    """Main test function"""
    setup_logging()
    
    print("Select test mode:")
    print("1. Background noise detection test")
    print("2. VOSK parameters test")
    
    mode = input("Enter 1 or 2: ").strip()
    
    if mode == "1":
        test_vosk_with_background_noise()
    elif mode == "2":
        test_vosk_parameters()
    else:
        print("Invalid mode selected")


if __name__ == "__main__":
    main() 