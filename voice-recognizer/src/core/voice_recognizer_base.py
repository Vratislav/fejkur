#!/usr/bin/env python3
"""
Base Voice Recognizer Class
Shared functionality between macOS and Raspberry Pi versions
"""

import sys
import os
import time
import signal
import logging
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from core.config_manager import ConfigManager
from core.audio_manager import AudioManager
from core.voice_processor import VoiceProcessor
from core.password_manager import PasswordManager
from core.mqtt_client import MQTTClient

# Platform-specific imports will be handled in the platform classes

class VoiceRecognizerBase:
    """Base voice recognition system with shared functionality"""
    
    def __init__(self, platform_name="Base"):
        """Initialize the voice recognition system"""
        self.platform_name = platform_name
        self.running = False
        self.processing = False
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = ConfigManager()
        
        # Initialize components
        self.audio_manager = AudioManager(self.config)
        self.voice_processor = VoiceProcessor(self.config)
        self.password_manager = PasswordManager(self.config)
        self.mqtt_client = MQTTClient(self.config)
        
        # Security settings
        self.security_config = self.config.get_security_config()
        self.max_attempts = self.security_config.get('max_attempts', 10)
        self.lockout_duration = self.security_config.get('lockout_duration', 0)
        self.failed_attempts = 0
        self.last_failed_time = 0
        
        self.logger.info(f"{platform_name} Voice Recognizer initialized")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'voice-recognizer-{self.platform_name.lower()}.log')
            ]
        )
    
    def initialize(self):
        """Initialize all components - to be overridden by platform-specific classes"""
        try:
            self.logger.info(f"Initializing {self.platform_name} Voice Recognizer...")
            
            # Initialize audio manager
            if not self.audio_manager.initialize():
                self.logger.error("Failed to initialize audio manager")
                return False
            
            # Initialize voice processor
            if not self.voice_processor.initialize():
                self.logger.error("Failed to initialize voice processor")
                return False
            
            # Load passwords
            if not self.password_manager.load_passwords():
                self.logger.error("Failed to load passwords")
                return False
            
            # Initialize MQTT (optional)
            try:
                self.mqtt_client.initialize()
                self.logger.info("MQTT client initialized")
                self.mqtt_available = True
            except Exception as e:
                self.logger.warning(f"MQTT initialization failed (continuing without MQTT): {e}")
                self.mqtt_available = False
            
            # Platform-specific initialization
            if not self.platform_initialize():
                self.logger.error("Failed to initialize platform-specific components")
                return False
            
            self.logger.info(f"{self.platform_name} Voice Recognizer initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    def platform_initialize(self):
        """Platform-specific initialization - to be overridden"""
        return True
    
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
    
    def handle_trigger_event(self):
        """Handle trigger event (button press, Enter key, etc.)"""
        if self.processing:
            self.logger.info("Already processing, ignoring trigger event")
            return
        
        if self.check_lockout():
            self.audio_manager.play_sound('fail')
            return
        
        self.logger.info("Trigger event detected, starting voice recognition")
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
    
    def run_interactive_mode(self):
        """Run in interactive mode for testing"""
        self.logger.info("Starting interactive mode...")
        self.logger.info("Press Enter to start voice recognition, 'q' to quit")
        
        while self.running:
            try:
                user_input = input("> ").strip().lower()
                
                if user_input == 'q':
                    self.logger.info("Quitting...")
                    break
                elif user_input == '':
                    # Start voice recognition
                    self.handle_trigger_event()
                else:
                    print("Commands: Enter = start recognition, q = quit")
                    
            except KeyboardInterrupt:
                self.logger.info("Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in interactive mode: {e}")
    
    def run(self):
        """Main application loop - to be overridden by platform-specific classes"""
        if not self.initialize():
            self.logger.error("Failed to initialize system")
            return
        
        self.running = True
        self.logger.info("System ready")
        
        try:
            # Platform-specific main loop
            self.platform_run()
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.shutdown()
    
    def platform_run(self):
        """Platform-specific main loop - to be overridden"""
        self.run_interactive_mode()
    
    def shutdown(self):
        """Shutdown the system"""
        self.logger.info(f"Shutting down {self.platform_name} Voice Recognizer...")
        self.running = False
        
        try:
            self.audio_manager.shutdown()
            self.voice_processor.shutdown()
            self.mqtt_client.shutdown()
            self.platform_shutdown()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        self.logger.info("Shutdown complete")
    
    def platform_shutdown(self):
        """Platform-specific shutdown - to be overridden"""
        pass
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0) 