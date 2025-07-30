#!/usr/bin/env python3

import os
import time
import numpy as np
import cv2
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color
from datetime import datetime

# Fix display environment for Pi
os.environ.pop('DISPLAY', None)  # Remove any SSH forwarded display
os.environ.pop('SSH_CLIENT', None)  # Remove SSH indicators
os.environ['DISPLAY'] = ':0'  # Use local display

# Constants
LED_COUNT = 12        # Number of LED pixels
LED_PIN = 18         # GPIO pin connected to the pixels (must support PWM)
LED_FREQ_HZ = 800000 # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10         # DMA channel to use for generating signal
LED_BRIGHTNESS = 255 # Set to 0 for darkest and 255 for brightest
LED_CHANNEL = 0      # PWM channel
LED_INVERT = False   # True to invert the signal

PROXIMITY_PIN = 4    # GPIO pin for proximity sensor
IR_LED_PIN = 13     # GPIO pin for IR LED (PWM1)
IR_LED_FREQ = 100   # PWM frequency for IR LED

PHASE_1_DURATION = 5  # Phase 1 (IR only) duration in seconds
PHASE_2_DURATION = 5  # Phase 2 (IR + light) duration in seconds

class TestConditionRecorder:
    def __init__(self, show_preview=True):
        self.show_preview = show_preview
        self.recording = False
        self.recording_dir = None
        self.frame_count = 0
        self.output_file = None
        self.current_phase = "Waiting"
        self.current_ir_duty = 0  # Track current IR LED duty cycle
        self.gpio_initialized = False  # Track GPIO initialization
        
        self.setup_camera()
        self.setup_gpio()
        
    def setup_camera(self):
        """Initialize camera"""
        print("Setting up camera...")
        self.camera = Picamera2()
        
        # Use simple configuration for recording
        preview_config = self.camera.create_preview_configuration(main={"size": (640, 480)})
        self.camera.configure(preview_config)
        
        # Start with or without preview
        if self.show_preview:
            try:
                self.camera.start(show_preview=True)
                print("Camera started with preview")
            except Exception as e:
                print(f"Preview failed: {e}")
                print("Starting camera without preview...")
                self.camera.start()
                self.show_preview = False
        else:
            self.camera.start()
            print("Camera started without preview")
        
    def setup_gpio(self):
        """Initialize GPIO for LEDs and sensors"""
        print("Setting up GPIO...")
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PROXIMITY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(IR_LED_PIN, GPIO.OUT)
            self.ir_pwm = GPIO.PWM(IR_LED_PIN, IR_LED_FREQ)
            self.ir_pwm.start(0)
            
            # Setup LEDs
            self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
            self.strip.begin()
            self.set_all_color(0, 0, 0)  # Start with LEDs off
            self.gpio_initialized = True
            print("GPIO setup complete")
        except Exception as e:
            print(f"GPIO setup failed: {e}")
            self.gpio_initialized = False
            
    def start_recording(self):
        """Start recording by creating frame directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recordings_dir = "/home/fejkur/recordings"
        os.makedirs(recordings_dir, exist_ok=True)
        
        # Create directory for this recording's frames
        self.recording_dir = f"{recordings_dir}/test_conditions_{timestamp}"
        os.makedirs(self.recording_dir, exist_ok=True)
        
        self.output_file = f"{recordings_dir}/test_conditions_{timestamp}.mp4"
        self.frame_count = 0
        self.recording = True
        print(f"Starting test condition recording: {self.output_file}")
        print(f"Saving frames to: {self.recording_dir}")
        
    def stop_recording(self):
        """Stop recording and convert frames to video"""
        if not self.recording:
            return
            
        self.recording = False
        print(f"Converting {self.frame_count} frames to video...")
        
        try:
            # Use ffmpeg to convert frames to video
            import subprocess
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite existing files
                '-framerate', '10',  # 10 FPS
                '-i', f'{self.recording_dir}/frame_%06d.jpg',  # Input pattern
                '-c:v', 'libx264',  # H.264 codec
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                self.output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Video created successfully: {self.output_file}")
                # Keep frame files for algorithm tuning
                print(f"Frame files kept for tuning: {self.recording_dir}")
            else:
                print(f"FFmpeg error: {result.stderr}")
                print("Frame files kept for debugging")
                
        except FileNotFoundError:
            print("FFmpeg not found. Keeping frame files.")
            print(f"Frames saved in: {self.recording_dir}")
        except Exception as e:
            print(f"Error converting frames: {e}")
            print(f"Frames saved in: {self.recording_dir}")
            
    def write_frame(self, frame):
        """Save frame as individual image file without overlays"""
        if self.recording:
            # Save clean frame without overlays for better analysis
            frame_filename = f"{self.recording_dir}/frame_{self.frame_count:06d}.jpg"
            cv2.imwrite(frame_filename, frame)
            self.frame_count += 1
            
            # Print progress every 25 frames
            if self.frame_count % 25 == 0:
                print(f"Recorded {self.frame_count} frames... Phase: {self.current_phase}")
                
    def add_info_overlay(self, frame):
        """Add information overlay to frame"""
        overlay_frame = frame.copy()
        
        # Add phase information
        cv2.putText(overlay_frame, f"Phase: {self.current_phase}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cv2.putText(overlay_frame, f"Time: {timestamp}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add IR LED status
        ir_status = f"IR LED: {self.current_ir_duty}%"
        cv2.putText(overlay_frame, ir_status, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add frame counter
        cv2.putText(overlay_frame, f"Frame: {self.frame_count:06d}", (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add center crosshair for reference
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        cv2.line(overlay_frame, (center_x-20, center_y), (center_x+20, center_y), (128, 128, 128), 1)
        cv2.line(overlay_frame, (center_x, center_y-20), (center_x, center_y+20), (128, 128, 128), 1)
        
        # Add search area circle for reference
        search_radius = min(width, height) // 3
        cv2.circle(overlay_frame, (center_x, center_y), search_radius, (64, 64, 64), 1)
        
        return overlay_frame
        
    def set_all_color(self, red: int, green: int, blue: int, brightness_percent: float = 100):
        """Set all LEDs to specified RGB color with brightness percentage"""
        if self.gpio_initialized:
            brightness = int((brightness_percent / 100.0) * 255)
            color = Color(red, green, blue)
            for i in range(LED_COUNT):
                self.strip.setPixelColor(i, color)
                self.strip.setBrightness(brightness)
            self.strip.show()
        
    def set_ir_led(self, duty_cycle: float):
        """Set IR LED brightness (0-100)"""
        if self.gpio_initialized:
            self.ir_pwm.ChangeDutyCycle(duty_cycle)
            self.current_ir_duty = duty_cycle
            print(f"IR LED set to {duty_cycle}%")
            
    def blue_blink(self):
        """Blink blue to indicate end of recording"""
        print("Recording complete - blue blink indication")
        if self.gpio_initialized:
            for _ in range(3):
                self.set_all_color(0, 0, 255, 50)  # Blue
                time.sleep(0.3)
                self.set_all_color(0, 0, 0)  # Off
                time.sleep(0.3)

    def run_test_recording(self):
        """Run the test condition recording sequence"""
        print("Test Condition Recorder")
        print("=" * 40)
        print(f"Phase 1 (IR only): {PHASE_1_DURATION} seconds")
        print(f"Phase 2 (IR + light): {PHASE_2_DURATION} seconds")
        print("Waiting for proximity trigger...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.current_phase = "Waiting for presence"
                
                # Wait for proximity trigger (object detected)
                if GPIO.input(PROXIMITY_PIN):  # Active low - no object
                    self.set_all_color(0, 0, 0)  # LEDs off
                    self.set_ir_led(0)  # IR LED off
                    time.sleep(0.1)
                    continue
                
                # Object detected - start recording sequence
                print("\n=== PRESENCE DETECTED - STARTING TEST RECORDING ===")
                self.start_recording()
                
                # Phase 1: IR light only
                self.current_phase = "Phase 1: IR Only"
                print(f"Phase 1: IR only for {PHASE_1_DURATION} seconds...")
                self.set_all_color(0, 0, 0)  # No white light
                self.set_ir_led(50)  # 50% IR LED brightness
                
                phase1_start = time.time()
                while time.time() - phase1_start < PHASE_1_DURATION:
                    frame = self.camera.capture_array()
                    self.write_frame(frame)
                    time.sleep(0.1)  # 10 FPS
                
                print("Phase 1 complete")
                
                # Phase 2: IR + white light
                self.current_phase = "Phase 2: IR + Light"
                print(f"Phase 2: IR + 5% white light for {PHASE_2_DURATION} seconds...")
                self.set_all_color(255, 255, 255, 5)  # 5% white light
                # Keep IR LED at 50%
                
                phase2_start = time.time()
                while time.time() - phase2_start < PHASE_2_DURATION:
                    frame = self.camera.capture_array()
                    self.write_frame(frame)
                    time.sleep(0.1)  # 10 FPS
                
                print("Phase 2 complete")
                
                # End recording
                self.stop_recording()
                
                # Blue blink to indicate completion
                self.blue_blink()
                
                # Reset and wait for no presence
                self.current_phase = "Waiting for no presence"
                print("Waiting for object to be removed...")
                self.set_all_color(0, 0, 0)  # LEDs off
                self.set_ir_led(0)  # IR LED off
                
                # Wait for object to be removed
                while not GPIO.input(PROXIMITY_PIN):  # Wait for no object
                    time.sleep(0.1)
                
                print("Object removed - ready for next recording")
                time.sleep(1)  # Brief pause before next recording
                
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up...")
        if self.recording:
            self.stop_recording()
        self.camera.stop()
        
        if self.gpio_initialized:
            try:
                self.ir_pwm.stop()
                GPIO.cleanup()
            except Exception as e:
                print(f"GPIO cleanup warning: {e}")
        
        try:
            self.set_all_color(0, 0, 0)
        except:
            pass  # LED cleanup may fail if GPIO already cleaned
            
        print("Cleanup complete")

if __name__ == "__main__":
    print("Test Condition Recorder for Algorithm Tuning")
    print("=" * 50)
    
    try:
        recorder = TestConditionRecorder(show_preview=True)
        recorder.run_test_recording()
    except Exception as e:
        print(f"Error: {e}")
        GPIO.cleanup() 