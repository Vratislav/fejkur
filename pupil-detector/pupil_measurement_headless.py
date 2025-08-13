#!/usr/bin/env python3

import os
import time
import numpy as np
from typing import Tuple, Optional
import cv2
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color
from datetime import datetime

# Import JEOresearch EyeTracker functions
import sys
sys.path.append('./EyeTracker')
from OrloskyPupilDetectorRaspberryPi import (
    crop_to_aspect_ratio, apply_binary_threshold, get_darkest_area,
    mask_outside_square, filter_contours_by_area_and_return_largest
)

# Fix display environment for Pi - headless mode
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
STABLE_THRESHOLD = 3  # Maximum allowed pupil size variation to consider stable (in pixels)
STABLE_FRAMES = 10   # Number of frames pupil size must be stable for

class HeadlessPupilMeasurement:
    def __init__(self):
        self.recording = False
        self.recording_dir = None
        self.frame_count = 0
        self.output_file = None
        self.current_phase = "Waiting"
        self.measurement_data = {}
        self.current_ir_duty = 0  # Track current IR LED duty cycle
        self.gpio_initialized = False  # Track GPIO initialization
        
        # Always start recording to save all frames
        self.start_recording()
        
        self.setup_camera()
        self.setup_gpio()
        self.last_pupil_sizes = []
        
    def setup_camera(self):
        """Initialize camera - headless mode"""
        print("Setting up camera in headless mode...")
        self.camera = Picamera2()
        
        # Use simple configuration for headless operation
        config = self.camera.create_preview_configuration(main={"size": (640, 480)})
        self.camera.configure(config)
        self.camera.start()
        print("Camera started in headless mode")
        
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
        """Start video recording by saving individual frames"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recordings_dir = "/home/fejkur/recordings"
        os.makedirs(recordings_dir, exist_ok=True)
        
        # Create directory for this recording's frames
        self.recording_dir = f"{recordings_dir}/frames_{timestamp}"
        os.makedirs(self.recording_dir, exist_ok=True)
        
        self.output_file = f"{recordings_dir}/pupil_measurement_{timestamp}.mp4"
        self.frame_count = 0
        self.recording = True
        print(f"Starting recording: {self.output_file}")
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
                # Clean up frame files
                import shutil
                shutil.rmtree(self.recording_dir)
                print("Frame files cleaned up")
            else:
                print(f"FFmpeg error: {result.stderr}")
                print("Frame files kept for debugging")
                
        except FileNotFoundError:
            print("FFmpeg not found. Keeping frame files.")
            print(f"Frames saved in: {self.recording_dir}")
        except Exception as e:
            print(f"Error converting frames: {e}")
            print(f"Frames saved in: {self.recording_dir}")
            
    def write_frame_to_video(self, frame):
        """Save frame as individual image file - always save regardless of recording flag"""
        if self.recording:
            frame_filename = f"{self.recording_dir}/frame_{self.frame_count:06d}.jpg"
            cv2.imwrite(frame_filename, frame)
            self.frame_count += 1
            
            # Print progress every 50 frames
            if self.frame_count % 50 == 0:
                print(f"Recorded {self.frame_count} frames...")
        else:
            # Even when not recording, save frames if directory exists
            if self.recording_dir and os.path.exists(self.recording_dir):
                frame_filename = f"{self.recording_dir}/frame_{self.frame_count:06d}.jpg"
                cv2.imwrite(frame_filename, frame)
                self.frame_count += 1
    
    def add_debug_overlay(self, frame, pupil_x=None, pupil_y=None, pupil_radius=None, ellipse=None):
        """Add debug overlay to frame with measurement information - matches JEOresearch visualization"""
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
        
        # Add pupil detection info - use JEOresearch style visualization
        if pupil_radius is not None and ellipse is not None:
            # Draw ellipse like JEOresearch algorithm (green ellipse, yellow center dot)
            cv2.ellipse(overlay_frame, ellipse, (0, 255, 0), 2)  # Green ellipse
            cv2.circle(overlay_frame, (pupil_x, pupil_y), 3, (255, 255, 0), -1)  # Yellow center dot
            
            # Add pupil size text
            cv2.putText(overlay_frame, f"Pupil: ({pupil_x}, {pupil_y}) R={pupil_radius}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            
            # Add stability indicator
            stability_frames = len(self.last_pupil_sizes)
            cv2.putText(overlay_frame, f"Stability: {stability_frames}/{STABLE_FRAMES}", (10, 140),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        else:
            cv2.putText(overlay_frame, "No pupil detected", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        
        # Add measurement data if available
        if 'baseline_radius' in self.measurement_data:
            cv2.putText(overlay_frame, f"Baseline: {self.measurement_data['baseline_radius']}", (10, 160),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        if 'response_radius' in self.measurement_data:
            cv2.putText(overlay_frame, f"Response: {self.measurement_data['response_radius']}", (10, 190),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Calculate and show change
            change = ((self.measurement_data['response_radius'] - self.measurement_data['baseline_radius']) / 
                     self.measurement_data['baseline_radius']) * 100
            cv2.putText(overlay_frame, f"Change: {change:.1f}%", (10, 220),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return overlay_frame
        
    def set_all_color(self, red: int, green: int, blue: int, brightness_percent: float = 100):
        """Set all LEDs to specified RGB color with brightness percentage"""
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
        
    def detect_pupil(self, frame: np.ndarray) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[tuple]]:
        """Detect pupil using JEOresearch EyeTracker algorithm with optimized parameters"""
        try:
            # Crop to aspect ratio (4:3)
            frame = crop_to_aspect_ratio(frame)
            
            # Get darkest area with optimized ignore_bounds=60
            darkest_point = self.get_darkest_area_optimized(frame)
            
            if darkest_point is None:
                return (None, None, None, None)
            
            # Convert to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Get darkest pixel value
            darkest_pixel_value = gray_frame[darkest_point[1], darkest_point[0]]
            
            # Apply binary threshold with default added_threshold=15
            thresholded_image = apply_binary_threshold(gray_frame, darkest_pixel_value, 15)
            
            # Mask outside square with default mask_size=250
            thresholded_image = mask_outside_square(thresholded_image, darkest_point, 250)
            
            # Process with JEOresearch algorithm
            kernel_size = 5
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            dilated_image = cv2.dilate(thresholded_image, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours with default parameters
            reduced_contours = filter_contours_by_area_and_return_largest(contours, 1000, 3)
            
            if len(reduced_contours) > 0 and len(reduced_contours[0]) > 5:
                try:
                    ellipse = cv2.fitEllipse(reduced_contours[0])
                    (x, y), (major_axis, minor_axis), angle = ellipse
                    
                    # Return center coordinates, average radius, and ellipse for visualization
                    radius = int((major_axis + minor_axis) / 4)  # Average radius
                    return (int(x), int(y), radius, ellipse)
                    
                except:
                    return (None, None, None, None)
            
            return (None, None, None, None)
            
        except Exception as e:
            print(f"Pupil detection error: {e}")
            return (None, None, None, None)
    
    def get_darkest_area_optimized(self, image):
        """Get darkest area with optimized ignore_bounds=60"""
        ignore_bounds = 60  # Optimized parameter
        image_skip_size = 20
        search_area = 20
        internal_skip_size = 10
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        min_sum = float('inf')
        darkest_point = None

        for y in range(ignore_bounds, gray.shape[0] - ignore_bounds, image_skip_size):
            for x in range(ignore_bounds, gray.shape[1] - ignore_bounds, image_skip_size):
                current_sum = 0
                num_pixels = 0
                for dy in range(0, search_area, internal_skip_size):
                    if y + dy >= gray.shape[0]:
                        break
                    for dx in range(0, search_area, internal_skip_size):
                        if x + dx >= gray.shape[1]:
                            break
                        current_sum += gray[y + dy][x + dx]
                        num_pixels += 1

                if current_sum < min_sum and num_pixels > 0:
                    min_sum = current_sum
                    darkest_point = (x + search_area // 2, y + search_area // 2)

        return darkest_point
        
    def is_pupil_stable(self, current_radius: float) -> bool:
        """Check if the pupil size is stable over multiple frames - more robust checking"""
        if not self.last_pupil_sizes:
            self.last_pupil_sizes.append(current_radius)
            return False
        
        # Add the current radius to the list
        self.last_pupil_sizes.append(current_radius)
        
        # Keep only the last STABLE_FRAMES elements
        if len(self.last_pupil_sizes) > STABLE_FRAMES:
            self.last_pupil_sizes.pop(0)
        
        # Need at least STABLE_FRAMES measurements to check stability
        if len(self.last_pupil_sizes) < STABLE_FRAMES:
            return False
        
        # Check if all recent measurements are within threshold of each other
        recent_sizes = self.last_pupil_sizes[-STABLE_FRAMES:]
        min_size = min(recent_sizes)
        max_size = max(recent_sizes)
        
        # All measurements should be within STABLE_THRESHOLD of each other
        if (max_size - min_size) <= STABLE_THRESHOLD:
            # Additional check: standard deviation should be low
            mean_size = sum(recent_sizes) / len(recent_sizes)
            variance = sum((size - mean_size) ** 2 for size in recent_sizes) / len(recent_sizes)
            std_dev = variance ** 0.5
            
            # Standard deviation should be less than 1 pixel for true stability
            if std_dev < 1.0:
                return True
        
        return False

    def run_measurement_sequence(self):
        """Run the complete measurement sequence with recording - headless mode"""
        print("Starting headless pupil measurement sequence...")
        print("System will wait for proximity trigger or start immediately")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.current_phase = "Waiting for trigger"
                
                # Wait for proximity trigger
                if GPIO.input(PROXIMITY_PIN):  # Active low
                    self.set_all_color(0, 0, 0)  # LEDs off
                    self.set_ir_led(0)  # IR LED off
                    print("Waiting for object detection...")
                    time.sleep(0.1)
                    continue
                
                # Object detected - start recording and measurement
                print("\n=== OBJECT DETECTED - STARTING MEASUREMENT ===")
                self.start_recording()
                self.measurement_data = {}  # Reset measurement data
                
                # Phase 1: IR light only, no white light
                self.current_phase = "Phase 1: IR Only"
                print("Phase 1: IR light only - measuring baseline pupil size...")
                self.set_all_color(0, 0, 0)  # No white light
                self.set_ir_led(25)  # 25% IR LED brightness only
                self.last_pupil_sizes = []  # Reset stability tracking
                
                measurement_start = time.time()
                first_radius = None
                
                while time.time() - measurement_start < 10:  # Timeout after 10 seconds
                    frame = self.camera.capture_array()
                    x, y, radius, ellipse = self.detect_pupil(frame)
                    
                    # Always save frame with overlay (even in headless mode)
                    overlay_frame = self.add_debug_overlay(frame, x, y, radius, ellipse)
                    self.write_frame_to_video(overlay_frame)
                    
                    if radius is not None:
                        print(f"Phase 1 - Detected pupil: position=({x}, {y}), radius={radius}")
                        
                        if self.is_pupil_stable(radius):
                            first_radius = radius
                            self.measurement_data['baseline_radius'] = first_radius
                            print(f"✓ PHASE 1 MEASUREMENT STABLE: {first_radius} pixels (IR only)")
                            
                            # Visual feedback - green flash to confirm stable measurement
                            self.set_all_color(0, 255, 0, 15)
                            time.sleep(0.5)
                            self.set_all_color(0, 0, 0)  # Back to no white light
                            time.sleep(0.5)
                            break
                    
                    time.sleep(0.1)
                
                if first_radius is None:
                    print("✗ Phase 1 failed - no stable pupil detected with IR only")
                    self.set_ir_led(0)  # Turn off IR
                    self.stop_recording()
                    continue
                
                # Phase 2: Measure pupil response with 15% white light
                self.current_phase = "Phase 2: Measuring Response"
                print("Phase 2: Measuring pupil response to 15% white light...")
                self.set_all_color(255, 255, 255, 15)  # 15% white light
                # Keep IR LED at 25%
                self.last_pupil_sizes = []  # Reset stability tracking
                
                # Wait a moment for pupil to adjust
                time.sleep(1)
                
                second_measurement_start = time.time()
                second_radius = None
                
                while time.time() - second_measurement_start < 10:  # 10 second timeout
                    frame = self.camera.capture_array()
                    new_x, new_y, new_radius, new_ellipse = self.detect_pupil(frame)
                    
                    # Always save frame with overlay (even in headless mode)
                    overlay_frame = self.add_debug_overlay(frame, new_x, new_y, new_radius, new_ellipse)
                    self.write_frame_to_video(overlay_frame)
                    
                    if new_radius is not None:
                        print(f"Phase 2 - Detected pupil: position=({new_x}, {new_y}), radius={new_radius}")
                        
                        if self.is_pupil_stable(new_radius):
                            second_radius = new_radius
                            self.measurement_data['response_radius'] = second_radius
                            print(f"✓ PHASE 2 MEASUREMENT STABLE: {second_radius} pixels (with 15% white)")
                            break
                    
                    time.sleep(0.1)
                
                if second_radius is None:
                    print("✗ Phase 2 failed - no stable pupil detected with white light")
                    self.set_all_color(0, 0, 0)
                    self.set_ir_led(0)
                    self.stop_recording()
                    continue
                
                # Analysis and feedback
                self.current_phase = "Analysis Complete"
                size_change = ((second_radius - first_radius) / first_radius) * 100
                size_difference = abs(second_radius - first_radius)
                
                print(f"\n=== MEASUREMENT COMPLETE ===")
                print(f"Baseline pupil size (IR only): {first_radius} pixels")
                print(f"Response pupil size (15% white): {second_radius} pixels")
                print(f"Size change: {size_change:.1f}%")
                print(f"Absolute difference: {size_difference:.1f} pixels")
                
                # Visual feedback based on pupil size comparison
                if size_difference <= STABLE_THRESHOLD:
                    # Similar pupil size - GREEN
                    print("Result: SIMILAR PUPIL SIZE (minimal light response)")
                    self.set_all_color(0, 255, 0, 25)  # Green feedback
                    time.sleep(2)
                else:
                    # Different pupil size - RED
                    if size_change < 0:
                        print("Result: PUPIL CONSTRICTION (normal light response)")
                    else:
                        print("Result: PUPIL DILATION (unusual light response)")
                    self.set_all_color(255, 0, 0, 25)  # Red feedback
                    time.sleep(2)
                
                # Stop recording
                self.stop_recording()
                
                # Reset for next measurement
                print("Resetting for next measurement...")
                self.set_all_color(0, 0, 0)
                self.set_ir_led(0)  # Turn off IR LED
                self.current_phase = "Reset"
                time.sleep(2)  # Wait before next measurement
                
        except KeyboardInterrupt:
            print("\nMeasurement stopped by user")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up...")
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
    print("Headless Pupil Measurement System")
    print("=" * 50)
    print("All frames will be saved for analysis")
    print("Stability requires 10 consecutive frames with <3px variation")
    print("=" * 50)
    
    try:
        pupil_system = HeadlessPupilMeasurement()
        pupil_system.run_measurement_sequence()
    except Exception as e:
        print(f"Error: {e}")
        GPIO.cleanup() 