"""
Audio Manager for Voice Recognition Door Opener
Handles audio playback and recording
"""

import os
import time
import logging
import wave
import numpy as np
import pyaudio
from typing import Optional, Tuple, List
from datetime import datetime
import glob
import random


class AudioManager:
    """Manages audio playback and recording"""
    
    def __init__(self, config):
        """Initialize audio manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.audio_config = config.get_audio_config()
        
        self.pyaudio = None
        self.audio_stream = None
        self.playback_stream = None
        self.recording_stream = None
        
        # Audio settings
        self.sample_rate = self.audio_config.get('sample_rate', 16000)
        self.channels = self.audio_config.get('channels', 1)
        self.chunk_size = self.audio_config.get('chunk_size', 1024)
        self.format = self._get_pyaudio_format()
        self.recording_duration = self.audio_config.get('recording_duration', 5)
        self.silence_threshold = self.audio_config.get('silence_threshold', 0.01)
        
        # Device settings
        self.input_device_index = self.audio_config.get('input_device_index', None)
        self.output_device_index = self.audio_config.get('output_device_index', None)
        self.input_device_name = self.audio_config.get('input_device', None)
        self.output_device_name = self.audio_config.get('output_device', None)
        
        # Sound cycling
        self.sound_counters = {}
        
        # Audio file cache
        self.audio_cache = {}
    
    def initialize(self):
        """Initialize audio system"""
        try:
            self.logger.info("Initializing audio manager...")
            
            # Initialize PyAudio
            self.pyaudio = pyaudio.PyAudio()
            
            # Test audio device
            if not self._test_audio_device():
                self.logger.error("Audio device test failed")
                return False
            
            # Create audio directory if it doesn't exist
            audio_dir = os.path.dirname(self.config.get_audio_file_path('prompt'))
            if audio_dir and not os.path.exists(audio_dir):
                os.makedirs(audio_dir, exist_ok=True)
            
            self.logger.info("Audio manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio manager: {e}")
            return False
    
    def _get_pyaudio_format(self):
        """Get PyAudio format from config"""
        format_str = self.audio_config.get('format', 'int16')
        format_map = {
            'int16': pyaudio.paInt16,
            'int32': pyaudio.paInt32,
            'float32': pyaudio.paFloat32
        }
        return format_map.get(format_str, pyaudio.paInt16)
    
    def _test_audio_device(self):
        """Test if audio device is working"""
        try:
            # Test input device
            if self.input_device_index is not None:
                input_info = self.pyaudio.get_device_info_by_index(self.input_device_index)
                self.logger.info(f"Input device: {input_info['name']} (Device {self.input_device_index})")
            else:
                input_info = self.pyaudio.get_default_input_device_info()
                self.logger.info(f"Default input device: {input_info['name']}")
            
            # Test output device
            if self.output_device_index is not None:
                output_info = self.pyaudio.get_device_info_by_index(self.output_device_index)
                self.logger.info(f"Output device: {output_info['name']} (Device {self.output_device_index})")
            else:
                output_info = self.pyaudio.get_default_output_device_info()
                self.logger.info(f"Default output device: {output_info['name']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Audio device test failed: {e}")
            return False
    
    def _is_after_10pm(self) -> bool:
        """Check if current time is after 10 PM or if debug mode is enabled"""
        # Check debug setting first
        debug_config = self.config.get('debug', {})
        if debug_config.get('force_10pm_mode', False):
            self.logger.info("Debug mode: Forcing 10pm sound selection")
            return True
        
        # Normal time-based logic
        current_hour = datetime.now().hour
        return current_hour >= 22 or current_hour < 6  # 10 PM to 6 AM
    
    # Hardcoded sound file lists
    PROMPT_FILES = [
        'prompt-0.mp3',
        'prompt-1.mp3',
        'prompt-2.mp3',
    ]
    PROMPT_10PM_FILES = [
        'prompt-10pm-0.mp3',
        'prompt-10pm-1.mp3',
        'prompt-10pm-2.mp3',
    ]
    SUCCESS_FILES = [
        'success-0.mp3',
    ]
    SUCCESS_10PM_FILES = [
        'success-10pm-0.mp3',
    ]
    FAIL_FILES = [
        'fail-0.mp3',
    ]
    FAIL_10PM_FILES = [
        'fail-10pm-0.mp3',
    ]
    TIMEOUT_FILES = [
        'timeout-0.mp3',
    ]
    TIMEOUT_10PM_FILES = [
        'timeout-10pm-0.mp3',
    ]

    def _get_sound_files(self, sound_type: str) -> list:
        """Return hardcoded list of sound files for the given type and time period."""
        after_10pm = self._is_after_10pm()
        files = []
        if sound_type == 'prompt':
            files = self.PROMPT_10PM_FILES if after_10pm else self.PROMPT_FILES
        elif sound_type == 'success':
            files = self.SUCCESS_10PM_FILES if after_10pm else self.SUCCESS_FILES
        elif sound_type == 'fail':
            files = self.FAIL_10PM_FILES if after_10pm else self.FAIL_FILES
        elif sound_type == 'timeout':
            files = self.TIMEOUT_10PM_FILES if after_10pm else self.TIMEOUT_FILES
        else:
            self.logger.warning(f"Unknown sound type: {sound_type}")
            return []
        # Prepend sounds directory and check existence
        script_dir = self.config.get_script_directory()
        sounds_dir = os.path.join(script_dir, "sounds")
        full_paths = [os.path.join(sounds_dir, f) for f in files if os.path.exists(os.path.join(sounds_dir, f))]
        if not full_paths:
            self.logger.warning(f"No sound files found for type: {sound_type} (after 10pm: {after_10pm})")
        return full_paths
    
    def _get_next_sound_file(self, sound_type: str) -> Optional[str]:
        """Get next sound file for cycling"""
        try:
            sound_files = self._get_sound_files(sound_type)
            
            if not sound_files:
                self.logger.warning(f"No sound files found for type: {sound_type}")
                return None
            
            # Initialize counter if not exists
            if sound_type not in self.sound_counters:
                self.sound_counters[sound_type] = 0
            
            # Get next file (cycle through available files)
            file_index = self.sound_counters[sound_type] % len(sound_files)
            selected_file = sound_files[file_index]
            
            # Increment counter for next time
            self.sound_counters[sound_type] += 1
            
            self.logger.debug(f"Selected sound file: {selected_file} (index: {file_index})")
            return selected_file
            
        except Exception as e:
            self.logger.error(f"Error getting next sound file for {sound_type}: {e}")
            return None
    
    def play_sound(self, sound_type: str):
        """Play audio file by type with cycling and time-based selection"""
        try:
            # Try to get sound file from sounds directory first
            sound_file = self._get_next_sound_file(sound_type)
            
            if not sound_file:
                # Fallback to config-based audio files
                audio_file = self.config.get_audio_file_path(sound_type)
                if not audio_file or not os.path.exists(audio_file):
                    self.logger.warning(f"Audio file not found: {sound_type}")
                    return False
                sound_file = audio_file
            
            self.logger.info(f"Playing sound: {sound_type} -> {os.path.basename(sound_file)}")
            
            # Load and play audio data
            audio_data = self._load_audio_file(sound_file)
            if audio_data is None:
                return False
            
            return self._play_audio_data(audio_data)
            
        except Exception as e:
            self.logger.error(f"Error playing sound {sound_type}: {e}")
            return False
    
    def _load_audio_file(self, file_path: str):
        """Load audio file into memory (supports WAV and MP3)"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.wav':
                return self._load_wav_file(file_path)
            elif file_ext == '.mp3':
                return self._load_mp3_file(file_path)
            else:
                self.logger.error(f"Unsupported audio format: {file_ext}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error loading audio file {file_path}: {e}")
            return None
    
    def _load_wav_file(self, file_path: str):
        """Load WAV file into memory"""
        try:
            with wave.open(file_path, 'rb') as wf:
                # Get audio parameters
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                
                # Read audio data
                audio_data = wf.readframes(n_frames)
                
                # Convert to numpy array for processing
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                self.logger.debug(f"Loaded WAV: {channels} channels, {sample_rate} Hz, {len(audio_array)} samples")
                return {
                    'data': audio_array,
                    'channels': channels,
                    'sample_rate': sample_rate,
                    'sample_width': sample_width
                }
                
        except Exception as e:
            self.logger.error(f"Error loading WAV file {file_path}: {e}")
            return None
    
    def _load_mp3_file(self, file_path: str):
        """Load MP3 file into memory"""
        try:
            # Try to use pydub for MP3 support
            try:
                from pydub import AudioSegment
                from pydub.utils import make_chunks
                
                # Load MP3 file
                audio_segment = AudioSegment.from_mp3(file_path)
                
                # Convert to mono if needed
                if audio_segment.channels > 1:
                    audio_segment = audio_segment.set_channels(1)
                
                # Convert to 16-bit PCM
                audio_segment = audio_segment.set_sample_width(2)
                
                # Convert to numpy array
                audio_array = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)
                
                self.logger.debug(f"Loaded MP3: {audio_segment.channels} channels, {audio_segment.frame_rate} Hz, {len(audio_array)} samples")
                return {
                    'data': audio_array,
                    'channels': audio_segment.channels,
                    'sample_rate': audio_segment.frame_rate,
                    'sample_width': audio_segment.sample_width
                }
                
            except ImportError:
                self.logger.error("pydub not available for MP3 support. Install with: pip install pydub")
                return None
                
        except Exception as e:
            self.logger.error(f"Error loading MP3 file {file_path}: {e}")
            return None
    
    def _play_audio_data(self, audio_info):
        """Play audio data through output device"""
        try:
            # Open output stream with specific device if configured
            if self.output_device_index is not None:
                stream = self.pyaudio.open(
                    format=self.pyaudio.get_format_from_width(audio_info['sample_width']),
                    channels=audio_info['channels'],
                    rate=audio_info['sample_rate'],
                    output=True,
                    output_device_index=self.output_device_index
                )
            else:
                stream = self.pyaudio.open(
                    format=self.pyaudio.get_format_from_width(audio_info['sample_width']),
                    channels=audio_info['channels'],
                    rate=audio_info['sample_rate'],
                    output=True
                )
            
            # Convert back to bytes for playback
            audio_bytes = audio_info['data'].tobytes()
            
            # Play audio in chunks
            chunk_size = 1024
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                stream.write(chunk)
            
            # Clean up
            stream.stop_stream()
            stream.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing audio data: {e}")
            return False
    
    def record_audio(self) -> Optional[np.ndarray]:
        """Record audio from microphone"""
        try:
            self.logger.info("Starting audio recording...")
            
            # Open input stream
            stream = self.pyaudio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            silence_frames = 0
            max_silence_frames = int(self.sample_rate * 0.5 / self.chunk_size)  # 0.5 seconds of silence
            
            # Record for specified duration
            total_frames = int(self.sample_rate * self.recording_duration / self.chunk_size)
            
            for _ in range(total_frames):
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Check for silence (optional - for voice activity detection)
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    if np.max(np.abs(audio_chunk)) < (self.silence_threshold * 32767):
                        silence_frames += 1
                    else:
                        silence_frames = 0
                    
                    # Stop early if too much silence (optional)
                    if silence_frames > max_silence_frames:
                        self.logger.info("Detected silence, stopping recording early")
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error reading audio chunk: {e}")
                    break
            
            # Clean up
            stream.stop_stream()
            stream.close()
            
            if not frames:
                self.logger.warning("No audio frames recorded")
                return None
            
            # Combine all frames
            audio_data = b''.join(frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            self.logger.info(f"Recorded {len(audio_array)} samples ({len(audio_array) / self.sample_rate:.2f} seconds)")
            return audio_array
            
        except Exception as e:
            self.logger.error(f"Error recording audio: {e}")
            return None
    
    def record_audio_with_vad(self) -> Optional[np.ndarray]:
        """Record audio with voice activity detection"""
        try:
            self.logger.info("Starting audio recording with VAD...")
            
            # Open input stream
            stream = self.pyaudio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            silence_frames = 0
            speech_frames = 0
            max_silence_frames = int(self.sample_rate * 1.0 / self.chunk_size)  # 1 second of silence
            min_speech_frames = int(self.sample_rate * 0.5 / self.chunk_size)   # 0.5 seconds of speech
            
            # Record until silence is detected after speech
            while True:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Check for voice activity
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    volume = np.max(np.abs(audio_chunk)) / 32767
                    
                    if volume > self.silence_threshold:
                        speech_frames += 1
                        silence_frames = 0
                    else:
                        silence_frames += 1
                    
                    # Stop if we have speech followed by silence
                    if speech_frames >= min_speech_frames and silence_frames >= max_silence_frames:
                        self.logger.info("Voice activity detected and ended")
                        break
                    
                    # Stop if recording too long
                    if len(frames) > int(self.sample_rate * 10 / self.chunk_size):  # Max 10 seconds
                        self.logger.info("Maximum recording time reached")
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error reading audio chunk: {e}")
                    break
            
            # Clean up
            stream.stop_stream()
            stream.close()
            
            if not frames:
                self.logger.warning("No audio frames recorded")
                return None
            
            # Combine all frames
            audio_data = b''.join(frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            self.logger.info(f"Recorded {len(audio_array)} samples ({len(audio_array) / self.sample_rate:.2f} seconds)")
            return audio_array
            
        except Exception as e:
            self.logger.error(f"Error recording audio with VAD: {e}")
            return None
    
    def get_audio_devices(self):
        """Get list of available audio devices"""
        devices = []
        
        try:
            for i in range(self.pyaudio.get_device_count()):
                device_info = self.pyaudio.get_device_info_by_index(i)
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'max_inputs': device_info['maxInputChannels'],
                    'max_outputs': device_info['maxOutputChannels'],
                    'default_sample_rate': device_info['defaultSampleRate']
                })
        except Exception as e:
            self.logger.error(f"Error getting audio devices: {e}")
        
        return devices
    
    def shutdown(self):
        """Shutdown audio manager"""
        self.logger.info("Shutting down audio manager...")
        
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            
            if self.playback_stream:
                self.playback_stream.stop_stream()
                self.playback_stream.close()
            
            if self.recording_stream:
                self.recording_stream.stop_stream()
                self.recording_stream.close()
            
            if self.pyaudio:
                self.pyaudio.terminate()
                
        except Exception as e:
            self.logger.error(f"Error during audio shutdown: {e}")
        
        self.logger.info("Audio manager shutdown complete") 