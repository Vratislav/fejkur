#!/usr/bin/env python3
"""
Voice Recognition Door Opener - Main Application
Raspberry Pi 4 voice recognition system for door access control
"""

import os
import sys
import time
import logging
import signal
import threading
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from bluetooth_manager import BluetoothManager
from audio_manager import AudioManager
from voice_processor import VoiceProcessor
from mqtt_client import MQTTClient
from button_handler import ButtonHandler
from password_manager import PasswordManager


class VoiceRecognizer:
    """Main voice recognition application class"""
    
    def __init__(self):
        """Initialize the voice recognition system"""
        self.config = ConfigManager()
        self.setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting Voice Recognition Door Opener")
        
        # Initialize components
        self.password_manager = PasswordManager(self.config)
        self.bluetooth_manager = BluetoothManager(self.config)
        self.audio_manager = AudioManager(self.config)
        self.voice_processor = VoiceProcessor(self.config)
        self.mqtt_client = MQTTClient(self.config)
        self.button_handler = ButtonHandler(self.config)
        
        # State management
        self.running = False
        self.processing = False
        self.attempts = 0
        self.lockout_until = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def setup_logging(self):
        """Configure logging system"""
        log_config = self.config.get('logging')
        
        # Create logs directory if it doesn't exist
        log_file = log_config['file']
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def startup(self):
        """Initialize and start all system components"""
        try:
            self.logger.info("Initializing system components...")
            
            # Initialize password manager
            self.password_manager.load_passwords()
            
            # Initialize Bluetooth
            if not self.bluetooth_manager.initialize():
                self.logger.error("Failed to initialize Bluetooth")
                return False
            
            # Initialize audio
            if not self.audio_manager.initialize():
                self.logger.error("Failed to initialize audio")
                return False
            
            # Initialize voice processor
            if not self.voice_processor.initialize():
                self.logger.error("Failed to initialize voice processor")
                return False
            
            # Initialize MQTT (optional)
            if not self.mqtt_client.initialize():
                self.logger.warning("Failed to initialize MQTT client - continuing without MQTT")
                self.mqtt_available = False
            else:
                self.mqtt_available = True
            
            # Initialize button handler
            if not self.button_handler.initialize():
                self.logger.error("Failed to initialize button handler")
                return False
            
            # Connect to Bluetooth device
            if not self.bluetooth_manager.connect():
                self.logger.error("Failed to connect to Bluetooth device")
                return False
            
            self.logger.info("System initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Startup failed: {e}")
            return False
    
    def shutdown(self):
        """Shutdown all system components gracefully"""
        self.logger.info("Shutting down system...")
        self.running = False
        
        try:
            self.button_handler.shutdown()
            self.audio_manager.shutdown()
            self.bluetooth_manager.shutdown()
            self.mqtt_client.shutdown()
            self.voice_processor.shutdown()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        self.logger.info("Shutdown complete")
    
    def check_lockout(self):
        """Check if system is in lockout mode"""
        if time.time() < self.lockout_until:
            remaining = int(self.lockout_until - time.time())
            self.logger.warning(f"System locked out for {remaining} more seconds")
            return True
        return False
    
    def reset_lockout(self):
        """Reset lockout state"""
        self.attempts = 0
        self.lockout_until = 0
        self.logger.info("Lockout reset")
    
    def evaluate_password_continuous(self):
        """Evaluate password using continuous recognition like learning mode"""
        try:
            self.logger.info("Starting continuous password evaluation...")
            
            # Reset recognizer state to clear any cached results
            self.voice_processor.recognizer.Reset()
            
            # Play password prompt
            self.audio_manager.play_sound('prompt')
            time.sleep(0.5)  # Small delay after prompt
            
            # Use continuous recognition
            stop = [False]
            import threading
            
            def wait_for_input():
                # Wait for user input or timeout
                import select
                import sys
                if select.select([sys.stdin], [], [], 10.0)[0]:  # 10 second timeout
                    input()  # Consume the input
                stop[0] = True
            
            t = threading.Thread(target=wait_for_input)
            t.daemon = True
            t.start()
            
            # Collect results from continuous recognition
            current_transcription = ""
            final_transcription = ""
            
            # Open input stream for continuous recognition
            p = self.audio_manager.pyaudio
            stream = p.open(
                format=self.audio_manager.format,
                channels=self.audio_manager.channels,
                rate=self.audio_manager.sample_rate,
                input=True,
                frames_per_buffer=self.audio_manager.chunk_size
            )
            
            try:
                while not stop[0]:
                    data = stream.read(self.audio_manager.chunk_size, exception_on_overflow=False)
                    
                    # Check for final result
                    if self.voice_processor.recognizer.AcceptWaveform(data):
                        result = self.voice_processor.recognizer.Result()
                        if result:
                            # Parse the result
                            import json
                            try:
                                result_data = json.loads(result)
                                if 'text' in result_data and result_data['text'].strip():
                                    text = result_data['text'].strip()
                                    if text != current_transcription:  # Only show if changed
                                        current_transcription = text
                                        final_transcription = text  # Keep the latest
                                        self.logger.info(f"Final transcription: '{text}'")
                                        
                                        # Check password on final result
                                        if self.password_manager.check_password(text):
                                            self.logger.info(f"Password match found in final: '{text}'")
                                            return text
                            except json.JSONDecodeError:
                                pass
                    else:
                        # Check partial result
                        partial = self.voice_processor.recognizer.PartialResult()
                        if partial:
                            # Parse partial result
                            import json
                            try:
                                partial_data = json.loads(partial)
                                if 'partial' in partial_data and partial_data['partial'].strip():
                                    partial_text = partial_data['partial'].strip()
                                    
                                    # Only log if it's different from last partial
                                    if partial_text != getattr(self, '_last_partial', ''):
                                        self._last_partial = partial_text
                                        self.logger.debug(f"Partial transcription: '{partial_text}'")
                                        
                                        # Check password on partial result
                                        if self.password_manager.check_password(partial_text):
                                            self.logger.info(f"Password match found in partial: '{partial_text}'")
                                            return partial_text
                            except json.JSONDecodeError:
                                pass
            finally:
                stream.stop_stream()
                stream.close()
            
            # Wait for thread to finish
            t.join(timeout=1)
            
            if final_transcription and final_transcription.strip():
                self.logger.info(f"Final transcription: '{final_transcription}'")
                return final_transcription
            else:
                self.logger.warning("No speech detected")
                return None
                
        except Exception as e:
            self.logger.error(f"Error during continuous password evaluation: {e}")
            return None

    def handle_button_press(self):
        """Handle button press event"""
        if self.processing:
            self.logger.info("Already processing, ignoring button press")
            return
        
        if self.check_lockout():
            self.audio_manager.play_sound('error')
            return
        
        self.logger.info("Button pressed, starting voice recognition")
        self.processing = True
        
        try:
            # Use continuous recognition for password evaluation
            recognized_text = self.evaluate_password_continuous()
            
            if not recognized_text:
                self.logger.warning("No speech detected")
                self.audio_manager.play_sound('failure')
                self.attempts += 1
                return
            
            # Password was already checked in evaluate_password_continuous
            # If we get here, a password was matched
            self.logger.info(f"Password accepted: '{recognized_text}'")
            self.audio_manager.play_sound('success')
            
            # Send MQTT unlock message (if available)
            if hasattr(self, 'mqtt_available') and self.mqtt_available:
                if self.mqtt_client.send_unlock_message():
                    self.logger.info("MQTT unlock message sent successfully")
                else:
                    self.logger.warning("Failed to send MQTT unlock message")
            else:
                self.logger.info("MQTT not available - skipping unlock message")
            
            self.reset_lockout()
        
        except Exception as e:
            self.logger.error(f"Error during voice recognition: {e}")
            self.audio_manager.play_sound('error')
        
        finally:
            self.processing = False
    
    def run(self):
        """Main application loop"""
        if not self.startup():
            self.logger.error("Failed to start system")
            return
        
        self.running = True
        self.logger.info("System ready - waiting for button press")
        
        # Set up button callback
        self.button_handler.set_callback(self.handle_button_press)
        
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
        finally:
            self.shutdown()


def main():
    """Main entry point"""
    app = VoiceRecognizer()
    app.run()


if __name__ == "__main__":
    main() 