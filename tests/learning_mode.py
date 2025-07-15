#!/usr/bin/env python3
"""
Learning Mode for Voice Recognition
Records password repetitions and shows all VOSK recognition variations
"""

import sys
import time
import logging
import json
import numpy as np
from pathlib import Path
from collections import Counter

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config_manager import ConfigManager
from bluetooth_manager import BluetoothManager
from audio_manager import AudioManager
from voice_processor import VoiceProcessor


def setup_logging():
    """Setup logging for learning mode"""
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


def learn_password(password_text, repetitions=10):
    """Learn how VOSK recognizes a specific password"""
    print(f"🎓 LEARNING MODE: '{password_text}'")
    print("=" * 60)
    print("Instructions:")
    print("- Speak the password clearly")
    print("- When you see a good recognition, press Enter to save it")
    print("- Press 'q' then Enter to quit early")
    print("- Empty transcriptions are ignored")
    print(f"- Target: {repetitions} successful recognitions")
    print()
    
    try:
        # Setup Bluetooth audio
        setup_bluetooth_audio()
        
        # Initialize components
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
        print("Press Enter to start learning...")
        input()
        
        # Collect recognition results
        all_recognitions = []
        round_num = 0
        
        while round_num < repetitions:
            round_num += 1
            print(f"\n🎤 ROUND {round_num}/{repetitions}")
            print("🎤 Listening... (speak the password, press Enter to save, 'q' to quit)")
            
            # Use continuous recognition for each round
            stop = [False]
            quit_early = [False]
            import threading
            
            def wait_for_input():
                user_input = input()
                if user_input.strip().lower() == 'q':
                    quit_early[0] = True
                stop[0] = True
            
            t = threading.Thread(target=wait_for_input)
            t.daemon = True
            t.start()
            
            # Collect results from continuous recognition
            current_transcription = ""
            
            # Open input stream for continuous recognition
            p = audio_manager.pyaudio
            stream = p.open(
                format=audio_manager.format,
                channels=audio_manager.channels,
                rate=audio_manager.sample_rate,
                input=True,
                frames_per_buffer=audio_manager.chunk_size
            )
            
            try:
                while not stop[0]:
                    data = stream.read(audio_manager.chunk_size, exception_on_overflow=False)
                    if voice_processor.recognizer.AcceptWaveform(data):
                        result = voice_processor.recognizer.Result()
                        if result:
                            # Parse the result
                            import json
                            try:
                                result_data = json.loads(result)
                                if 'text' in result_data and result_data['text'].strip():
                                    text = result_data['text'].strip()
                                    if text != current_transcription:  # Only show if changed
                                        current_transcription = text
                                        print(f"\r📝 Current: '{text}'", end="", flush=True)
                            except json.JSONDecodeError:
                                pass
            finally:
                stream.stop_stream()
                stream.close()
            
            # Wait for thread to finish
            t.join(timeout=1)
            
            if quit_early[0]:
                print(f"\n👋 Quitting early after {round_num-1} rounds")
                break
            
            if current_transcription and current_transcription.strip():
                all_recognitions.append(current_transcription)
                print(f"\n✅ Saved: '{current_transcription}'")
            else:
                print(f"\n❌ No transcription to save")
                round_num -= 1  # Don't count this round
        
        # Analyze results
        print("\n" + "=" * 60)
        print("📊 LEARNING RESULTS")
        print("=" * 60)
        
        if all_recognitions:
            # Count unique recognitions
            recognition_counts = Counter(all_recognitions)
            
            print(f"🎯 Target password: '{password_text}'")
            print(f"📊 Successful recognitions: {len(all_recognitions)}")
            
            print(f"\n📝 RECOGNIZED VARIATIONS:")
            for recognition, count in recognition_counts.most_common():
                percentage = count / len(all_recognitions) * 100
                print(f"   • '{recognition}' ({count}x, {percentage:.1f}%)")
            
            # Suggest additions to passwords.txt
            print(f"\n💡 SUGGESTED ADDITIONS TO passwords.txt:")
            suggested = set()
            
            # Add all recognitions with >10% frequency
            for recognition, count in recognition_counts.items():
                if count / len(all_recognitions) > 0.1:
                    suggested.add(recognition)
            
            for suggestion in sorted(suggested):
                print(f"   {suggestion}")
            
            # Save results to file
            results_file = f"learning_results_{password_text.replace(' ', '_')}.json"
            results = {
                'target_password': password_text,
                'rounds_attempted': round_num,
                'successful_recognitions': len(all_recognitions),
                'recognition_rate': len(all_recognitions) / round_num if round_num > 0 else 0,
                'recognitions': all_recognitions,
                'recognition_counts': dict(recognition_counts),
                'suggested_additions': list(suggested)
            }
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {results_file}")
            
        else:
            print("❌ No successful recognitions. Try speaking more clearly or adjusting microphone.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during learning: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            audio_manager.shutdown()
            voice_processor.shutdown()
        except:
            pass


def main():
    """Main learning mode function"""
    setup_logging()
    
    print("🎓 VOSK PASSWORD LEARNING MODE")
    print("=" * 50)
    print("This mode helps you learn how VOSK recognizes your passwords")
    print("so you can add all variations to your passwords.txt file.")
    print()
    
    # Get password to learn
    password = input("Enter the password to learn: ").strip()
    if not password:
        print("❌ No password entered")
        return
    
    # Run learning mode with 10 rounds
    learn_password(password, repetitions=10)


if __name__ == "__main__":
    main() 