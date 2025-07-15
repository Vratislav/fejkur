"""
Voice Processor for Voice Recognition Door Opener
Handles speech recognition using VOSK engine
"""

import os
import logging
import numpy as np
from vosk import Model, KaldiRecognizer
from typing import Optional, List, Dict


class VoiceProcessor:
    """Handles voice recognition using VOSK engine"""
    
    def __init__(self, config):
        """Initialize voice processor"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.voice_config = config.get_voice_config()
        
        self.model = None
        self.recognizer = None
        self.sample_rate = config.get_audio_config().get('sample_rate', 16000)
        
        # Recognition settings
        self.confidence_threshold = self.voice_config.get('confidence_threshold', 0.7)
        self.max_alternatives = self.voice_config.get('max_alternatives', 3)
        self.language = self.voice_config.get('language', 'cs')
    
    def initialize(self):
        """Initialize VOSK model and recognizer"""
        try:
            self.logger.info("Initializing voice processor...")
            
            # Get model path
            model_path = self.voice_config.get('model_path')
            if not model_path:
                self.logger.error("No VOSK model path specified")
                return False
            
            # Check if model exists
            if not os.path.exists(model_path):
                self.logger.error(f"VOSK model not found at: {model_path}")
                self.logger.info("Please download the Czech VOSK model from: https://alphacephei.com/vosk/models")
                return False
            
            # Load VOSK model
            self.logger.info(f"Loading VOSK model from: {model_path}")
            self.model = Model(model_path)
            
            # Create recognizer
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)  # Enable word timing
            
            self.logger.info("Voice processor initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize voice processor: {e}")
            return False
    
    def recognize_speech(self, audio_data: np.ndarray) -> Optional[str]:
        """Recognize speech from audio data"""
        try:
            if self.recognizer is None:
                self.logger.error("Recognizer not initialized")
                return None
            
            # Convert numpy array to bytes
            audio_bytes = audio_data.tobytes()
            
            # Process audio in chunks
            chunk_size = 4000  # VOSK recommended chunk size
            results = []
            
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                
                if self.recognizer.AcceptWaveform(chunk):
                    result = self.recognizer.Result()
                    if result:
                        results.append(result)
            
            # Get final result
            final_result = self.recognizer.FinalResult()
            if final_result:
                results.append(final_result)
            
            # Parse results
            recognized_text = self._parse_recognition_results(results)
            
            if recognized_text:
                self.logger.info(f"Recognized text: '{recognized_text}'")
            else:
                self.logger.warning("No speech recognized")
            
            return recognized_text
            
        except Exception as e:
            self.logger.error(f"Error during speech recognition: {e}")
            return None
    
    def _parse_recognition_results(self, results: List[str]) -> Optional[str]:
        """Parse VOSK recognition results"""
        try:
            import json
            
            best_result = None
            best_confidence = 0.0
            
            for result_str in results:
                if not result_str.strip():
                    continue
                
                try:
                    result = json.loads(result_str)
                    
                    # Check if we have a valid result
                    if 'text' in result and result['text'].strip():
                        # Get confidence score
                        confidence = self._calculate_confidence(result)
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_result = result['text'].strip()
                    
                    # Check alternatives if available
                    if 'alternatives' in result:
                        for alt in result['alternatives']:
                            if 'text' in alt and alt['text'].strip():
                                confidence = alt.get('confidence', 0.0)
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                    best_result = alt['text'].strip()
                
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON result: {result_str}")
                    continue
                except Exception as e:
                    self.logger.error(f"Error parsing result: {e}")
                    continue
            
            # Check confidence threshold
            if best_result and best_confidence >= self.confidence_threshold:
                self.logger.debug(f"Best result: '{best_result}' (confidence: {best_confidence:.3f})")
                return best_result
            elif best_result:
                self.logger.warning(f"Result below confidence threshold: '{best_result}' (confidence: {best_confidence:.3f})")
                return None
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing recognition results: {e}")
            return None
    
    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate confidence score for recognition result"""
        try:
            # Try to get confidence from result
            if 'confidence' in result:
                return float(result['confidence'])
            
            # If no direct confidence, try to calculate from alternatives
            if 'alternatives' in result and result['alternatives']:
                # Use the first alternative's confidence
                return float(result['alternatives'][0].get('confidence', 0.0))
            
            # Default confidence if no information available
            return 0.5
            
        except (ValueError, TypeError):
            return 0.5
    
    def recognize_speech_with_alternatives(self, audio_data: np.ndarray) -> List[Dict]:
        """Recognize speech and return multiple alternatives"""
        try:
            if self.recognizer is None:
                self.logger.error("Recognizer not initialized")
                return []
            
            # Convert numpy array to bytes
            audio_bytes = audio_data.tobytes()
            
            # Process audio in chunks
            chunk_size = 4000
            all_alternatives = []
            
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                
                if self.recognizer.AcceptWaveform(chunk):
                    result = self.recognizer.Result()
                    if result:
                        alternatives = self._parse_alternatives(result)
                        all_alternatives.extend(alternatives)
            
            # Get final result
            final_result = self.recognizer.FinalResult()
            if final_result:
                alternatives = self._parse_alternatives(final_result)
                all_alternatives.extend(alternatives)
            
            # Sort by confidence and return top alternatives
            all_alternatives.sort(key=lambda x: x['confidence'], reverse=True)
            return all_alternatives[:self.max_alternatives]
            
        except Exception as e:
            self.logger.error(f"Error during speech recognition with alternatives: {e}")
            return []
    
    def _parse_alternatives(self, result_str: str) -> List[Dict]:
        """Parse VOSK result for alternatives"""
        try:
            import json
            
            result = json.loads(result_str)
            alternatives = []
            
            # Main result
            if 'text' in result and result['text'].strip():
                confidence = self._calculate_confidence(result)
                alternatives.append({
                    'text': result['text'].strip(),
                    'confidence': confidence
                })
            
            # Additional alternatives
            if 'alternatives' in result:
                for alt in result['alternatives']:
                    if 'text' in alt and alt['text'].strip():
                        confidence = alt.get('confidence', 0.0)
                        alternatives.append({
                            'text': alt['text'].strip(),
                            'confidence': confidence
                        })
            
            return alternatives
            
        except Exception as e:
            self.logger.error(f"Error parsing alternatives: {e}")
            return []
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded VOSK model"""
        if not self.model:
            return {}
        
        try:
            return {
                'model_path': self.voice_config.get('model_path'),
                'sample_rate': self.sample_rate,
                'language': self.language,
                'confidence_threshold': self.confidence_threshold,
                'max_alternatives': self.max_alternatives
            }
        except Exception as e:
            self.logger.error(f"Error getting model info: {e}")
            return {}
    
    def test_recognition(self, test_audio: np.ndarray) -> bool:
        """Test speech recognition with sample audio"""
        try:
            self.logger.info("Testing speech recognition...")
            
            result = self.recognize_speech(test_audio)
            if result:
                self.logger.info(f"Test recognition successful: '{result}'")
                return True
            else:
                self.logger.warning("Test recognition failed - no speech detected")
                return False
                
        except Exception as e:
            self.logger.error(f"Test recognition error: {e}")
            return False
    
    def shutdown(self):
        """Shutdown voice processor"""
        self.logger.info("Shutting down voice processor...")
        
        try:
            if self.recognizer:
                self.recognizer = None
            
            if self.model:
                self.model = None
                
        except Exception as e:
            self.logger.error(f"Error during voice processor shutdown: {e}")
        
        self.logger.info("Voice processor shutdown complete") 

    def recognize_continuous(self, audio_manager, stop_callback=None):
        """
        Perform continuous real-time recognition from the microphone.
        Prints partial and final results as they come.
        Stops when stop_callback() returns True (or on KeyboardInterrupt if not provided).
        """
        import queue
        import threading
        import sys
        
        if self.recognizer is None:
            self.logger.error("Recognizer not initialized")
            return
        
        self.logger.info("Starting continuous recognition (press Ctrl+C or trigger stop_callback to stop)...")
        
        # Open input stream
        p = audio_manager.pyaudio
        stream = p.open(
            format=audio_manager.format,
            channels=audio_manager.channels,
            rate=audio_manager.sample_rate,
            input=True,
            frames_per_buffer=audio_manager.chunk_size
        )
        
        try:
            while True:
                data = stream.read(audio_manager.chunk_size, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    result = self.recognizer.Result()
                    print("\n[FINAL]", result)
                else:
                    partial = self.recognizer.PartialResult()
                    print("[PARTIAL]", partial, end='\r')
                if stop_callback and stop_callback():
                    print("\n[INFO] Stop callback triggered, stopping recognition.")
                    break
        except KeyboardInterrupt:
            print("\n[INFO] KeyboardInterrupt, stopping recognition.")
        finally:
            stream.stop_stream()
            stream.close()
            self.logger.info("Continuous recognition stopped.")
    
    def reset_recognizer(self):
        """Reset the VOSK recognizer to clear cached results"""
        try:
            if self.recognizer:
                # Create a new recognizer to clear state
                self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
                self.recognizer.SetWords(True)
                self.logger.debug("VOSK recognizer reset")
        except Exception as e:
            self.logger.error(f"Error resetting recognizer: {e}")
    
    def get_partial_result(self) -> Optional[str]:
        """Get the current partial recognition result"""
        try:
            if self.recognizer:
                partial = self.recognizer.PartialResult()
                if partial and partial.strip():
                    import json
                    try:
                        result = json.loads(partial)
                        if 'partial' in result and result['partial'].strip():
                            return result['partial'].strip()
                    except json.JSONDecodeError:
                        pass
            return None
        except Exception as e:
            self.logger.error(f"Error getting partial result: {e}")
            return None
    
    def get_final_result(self) -> Optional[str]:
        """Get the current final recognition result"""
        try:
            if self.recognizer:
                final = self.recognizer.FinalResult()
                if final and final.strip():
                    import json
                    try:
                        result = json.loads(final)
                        if 'text' in result and result['text'].strip():
                            return result['text'].strip()
                    except json.JSONDecodeError:
                        pass
            return None
        except Exception as e:
            self.logger.error(f"Error getting final result: {e}")
            return None
    
    def process_audio_chunk(self, audio_chunk: bytes) -> bool:
        """Process a chunk of audio data for continuous recognition"""
        try:
            if self.recognizer:
                return self.recognizer.AcceptWaveform(audio_chunk)
            return False
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
            return False 