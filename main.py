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
        
        # Security settings
        self.security_config = self.config.get_security_config()
        self.max_attempts = self.security_config.get('max_attempts', 10)
        self.lockout_duration = self.security_config.get('lockout_duration', 0)
        self.failed_attempts = 0
        self.last_failed_time = 0
        
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
            try:
                self.mqtt_client.initialize()
                self.logger.info("MQTT client initialized")
                self.mqtt_available = True
            except Exception as e:
                self.logger.warning(f"MQTT initialization failed (continuing without MQTT): {e}")
                self.mqtt_available = False
            
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
        if self.lockout_duration > 0 and self.failed_attempts >= self.max_attempts:
            time_since_last_failed = time.time() - self.last_failed_time
            if time_since_last_failed < self.lockout_duration:
                remaining_time = self.lockout_duration - time_since_last_failed
                self.logger.warning(f"System locked out. Try again in {remaining_time:.0f} seconds")
                return True
            else:
                # Reset lockout
                self.failed_attempts = 0
                self.logger.info("Lockout period expired")
        
        return False
    
    def handle_successful_password(self):
        """Handle successful password recognition"""
        self.logger.info("Password accepted!")
        
        # Reset failed attempts
        self.failed_attempts = 0
        
        # Play success sound
        self.audio_manager.play_sound('success')
        
        # Send MQTT message
        try:
            if self.mqtt_available:
                self.mqtt_client.send_unlock_message()
                self.logger.info("MQTT unlock message sent")
            else:
                self.logger.info("MQTT not available - skipping unlock message")
        except Exception as e:
            self.logger.warning(f"Failed to send MQTT message: {e}")
    
    def handle_failed_password(self):
        """Handle failed password recognition"""
        self.logger.warning("Password rejected")
        
        # Increment failed attempts
        self.failed_attempts += 1
        self.last_failed_time = time.time()
        
        # Play failure sound
        self.audio_manager.play_sound('fail')
        
        # Check for lockout
        if self.failed_attempts >= self.max_attempts:
            self.logger.warning(f"Maximum failed attempts reached ({self.max_attempts})")
            if self.lockout_duration > 0:
                self.logger.warning(f"System locked for {self.lockout_duration} seconds")
    
    def continuous_password_evaluation(self):
        """Continuously evaluate password from voice input with smart timeout"""
        try:
            self.logger.info("Starting continuous password evaluation...")
            
            # Reset VOSK recognizer state
            self.voice_processor.reset_recognizer()
            
            # Play prompt sound and wait for it to finish
            self.audio_manager.play_sound('prompt')
            
            # Wait a moment for prompt to finish playing
            time.sleep(0.5)  # Brief pause to ensure prompt is done
            
            # Open audio input stream with specific device if configured
            p = self.audio_manager.pyaudio
            if self.audio_manager.input_device_index is not None:
                stream = p.open(
                    format=self.audio_manager.format,
                    channels=self.audio_manager.channels,
                    rate=self.audio_manager.sample_rate,
                    input=True,
                    input_device_index=self.audio_manager.input_device_index,
                    frames_per_buffer=self.audio_manager.chunk_size
                )
            else:
                stream = p.open(
                    format=self.audio_manager.format,
                    channels=self.audio_manager.channels,
                    rate=self.audio_manager.sample_rate,
                    input=True,
                    frames_per_buffer=self.audio_manager.chunk_size
                )
            
            try:
                # Start timeout AFTER prompt finishes
                start_time = time.time()
                timeout = 15  # 15 seconds timeout for complete sentence
                last_speech_time = None  # Will be set when first speech is detected
                silence_threshold = 2.0  # 2 seconds of silence indicates sentence end
                speech_detected = False  # Track if any speech has been detected
                sentence_complete = False  # Track if we have a complete sentence
                
                while time.time() - start_time < timeout:
                    # Read audio data
                    data = stream.read(self.audio_manager.chunk_size, exception_on_overflow=False)
                    
                    # Process audio chunk
                    if self.voice_processor.process_audio_chunk(data):
                        # Speech detected, update last speech time
                        speech_detected = True
                        last_speech_time = time.time()
                        sentence_complete = False  # Reset sentence completion flag
                        
                        # Get final result
                        final_result = self.voice_processor.get_final_result()
                        if final_result:
                            self.logger.info(f"Final: '{final_result}'")
                            sentence_complete = True  # We have a complete sentence
                            if self.password_manager.check_password(final_result):
                                self.logger.info(f"Password match found in final: '{final_result}'")
                                return "success"
                            else:
                                # Speech detected but wrong password
                                self.logger.info("Speech detected but password incorrect")
                                return "failed"
                    else:
                        # Get partial result
                        partial_result = self.voice_processor.get_partial_result()
                        if partial_result:
                            # Speech detected in partial result
                            speech_detected = True
                            last_speech_time = time.time()
                            self.logger.debug(f"Partial: '{partial_result}'")
                            # Don't check password on partial results - wait for complete sentence
                    
                    # Check for sentence completion (silence after speech)
                    if speech_detected and last_speech_time and (time.time() - last_speech_time > silence_threshold):
                        if sentence_complete:
                            # We have a complete sentence but no password match
                            self.logger.info("Sentence completed but no password match")
                            return "failed"
                        else:
                            # Still waiting for sentence completion
                            self.logger.debug("Waiting for sentence completion...")
                            # Continue listening for a bit longer
                            if time.time() - last_speech_time > silence_threshold + 1.0:  # Extra 1 second
                                self.logger.info("No complete sentence detected")
                                stream.stop_stream()
                                stream.close()
                                self.audio_manager.play_sound('timeout')
                                return "timeout"
                
                # Full timeout reached
                self.logger.info("Full timeout reached")
                # Close stream before playing timeout sound
                stream.stop_stream()
                stream.close()
                self.audio_manager.play_sound('timeout')
                return "timeout"
                
            except Exception as e:
                self.logger.error(f"Error during audio processing: {e}")
                stream.stop_stream()
                stream.close()
                return False
            
        except Exception as e:
            self.logger.error(f"Error during password evaluation: {e}")
            return False
    
    def handle_button_press(self):
        """Handle button press event"""
        if self.processing:
            self.logger.info("Already processing, ignoring button press")
            return
        
        if self.check_lockout():
            self.audio_manager.play_sound('fail')
            return
        
        self.logger.info("Button pressed, starting voice recognition")
        self.processing = True
        
        try:
            # Use improved continuous recognition for password evaluation
            result = self.continuous_password_evaluation()
            
            if result == "success":
                self.handle_successful_password()
            elif result == "failed":
                self.handle_failed_password()
            elif result == "timeout":
                # Timeout - do nothing, already handled by continuous_password_evaluation
                pass
            else:
                self.logger.warning("Unexpected result from password evaluation")
        
        except Exception as e:
            self.logger.error(f"Error during voice recognition: {e}")
            self.audio_manager.play_sound('fail')
        
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