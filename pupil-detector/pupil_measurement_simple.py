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
STABLE_THRESHOLD = 2.0  # Maximum allowed pupil size variation to consider stable (in pixels)
STABLE_FRAMES = 10   # Number of frames pupil size must be stable for

class CustomOutput(FileOutput):
    """Custom output that can handle overlay frames"""
    def __init__(self, file, overlay_callback=None):
        super().__init__(file)
        self.overlay_callback = overlay_callback
        
    def outputframe(self, frame, keyframe=True, timestamp=None):
        if self.overlay_callback:
            frame = self.overlay_callback(frame)
        return super().outputframe(frame, keyframe, timestamp)

class SimplePupilMeasurement:
    def __init__(self, record_video=True, show_preview=True):
        self.record_video = record_video
        self.show_preview = show_preview
        self.recording = False
        self.recording_dir = None
        self.frame_count = 0
        self.output_file = None
        self.current_phase = "Waiting"
        self.measurement_data = {}
        self.current_ir_duty = 0  # Track current IR LED duty cycle
        self.gpio_initialized = False  # Track GPIO initialization
        
        self.setup_camera()
        self.setup_gpio()
        self.last_pupil_sizes = []
        
    def setup_camera(self):
        """Initialize camera - use exact working method"""
        print("Setting up camera...")
        self.camera = Picamera2()
        
        # Use the exact same configuration that works
        preview_config = self.camera.create_preview_configuration(main={"size": (640, 480)})
        self.camera.configure(preview_config)
        
        # Start with or without preview based on option
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
        """Start video recording by saving individual frames"""
        if not self.record_video:
            return
            
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
        """Save frame as individual image file"""
        if self.recording:
            frame_filename = f"{self.recording_dir}/frame_{self.frame_count:06d}.jpg"
            cv2.imwrite(frame_filename, frame)
            self.frame_count += 1
            
            # Print progress every 50 frames
            if self.frame_count % 50 == 0:
                print(f"Recorded {self.frame_count} frames...")
            
    def add_debug_overlay(self, frame, pupil_x=None, pupil_y=None, pupil_radius=None):
        """Add debug overlay to frame with measurement information"""
        overlay_frame = frame.copy()
        
        # Add center crosshair for reference
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        cv2.line(overlay_frame, (center_x-20, center_y), (center_x+20, center_y), (128, 128, 128), 1)
        cv2.line(overlay_frame, (center_x, center_y-20), (center_x, center_y+20), (128, 128, 128), 1)
        
        # Add search area circle
        search_radius = min(width, height) // 3
        cv2.circle(overlay_frame, (center_x, center_y), search_radius, (64, 64, 64), 1)
        
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
        
        # Add pupil detection info
        if pupil_radius is not None:
            # Draw circle around detected pupil - use different color based on location
            distance_from_center = np.sqrt((pupil_x - center_x)**2 + (pupil_y - center_y)**2)
            if distance_from_center < search_radius:
                color = (0, 255, 0)  # Green for good detection
            else:
                color = (0, 255, 255)  # Yellow for detection outside expected area
                
            cv2.circle(overlay_frame, (pupil_x, pupil_y), pupil_radius, color, 2)
            cv2.circle(overlay_frame, (pupil_x, pupil_y), 2, color, -1)
            
            # Add pupil size text
            cv2.putText(overlay_frame, f"Pupil: ({pupil_x}, {pupil_y}) R={pupil_radius}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
            
            # Add distance from center
            cv2.putText(overlay_frame, f"Distance from center: {distance_from_center:.1f}px", (10, 140),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Add stability indicator
            stability_frames = len(self.last_pupil_sizes)
            cv2.putText(overlay_frame, f"Stability: {stability_frames}/{STABLE_FRAMES}", (10, 160),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        else:
            cv2.putText(overlay_frame, "No pupil detected", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        
        # Add measurement data if available
        if 'baseline_radius' in self.measurement_data:
            cv2.putText(overlay_frame, f"Baseline: {self.measurement_data['baseline_radius']}", (10, 190),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        if 'response_radius' in self.measurement_data:
            cv2.putText(overlay_frame, f"Response: {self.measurement_data['response_radius']}", (10, 220),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Calculate and show change
            change = ((self.measurement_data['response_radius'] - self.measurement_data['baseline_radius']) / 
                     self.measurement_data['baseline_radius']) * 100
            cv2.putText(overlay_frame, f"Change: {change:.1f}%", (10, 250),
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
        
    def detect_pupil(self, frame: np.ndarray) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Detect pupil in the frame using OpenCV - improved to avoid LED reflections"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply stronger blur to reduce noise
        gray = cv2.GaussianBlur(gray, (15, 15), 0)
        
        # Create a mask to focus on the center area (where pupil should be)
        height, width = gray.shape
        center_x, center_y = width // 2, height // 2
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(mask, (center_x, center_y), min(width, height) // 3, 255, -1)
        
        # Apply mask to focus on center region
        masked_gray = cv2.bitwise_and(gray, mask)
        
        # Invert the image so dark areas (pupils) become bright
        inverted = cv2.bitwise_not(masked_gray)
        
        # Apply threshold to isolate dark regions (pupils)
        _, thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Use HoughCircles on the thresholded image to find dark circular regions
        circles = cv2.HoughCircles(
            thresh, 
            cv2.HOUGH_GRADIENT, 
            dp=1.5,           # Inverse ratio of accumulator resolution
            minDist=80,       # Minimum distance between circle centers
            param1=50,        # Upper threshold for edge detection
            param2=20,        # Accumulator threshold for center detection (lower = more sensitive)
            minRadius=8,      # Minimum circle radius
            maxRadius=40      # Maximum circle radius
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            # Filter circles based on additional criteria
            valid_circles = []
            for (x, y, r) in circles:
                # Check if circle is within frame boundaries
                if x - r > 0 and x + r < width and y - r > 0 and y + r < height:
                    # Check if the area is actually dark (pupil-like)
                    roi = gray[y-r:y+r, x-r:x+r]
                    if roi.size > 0:
                        mean_intensity = np.mean(roi)
                        # Pupil should be darker than average
                        if mean_intensity < np.mean(gray) * 0.7:  # 70% of average brightness
                            valid_circles.append((x, y, r, mean_intensity))
            
            if valid_circles:
                # Sort by darkness (lowest mean intensity first) and size
                valid_circles.sort(key=lambda c: (c[3], -c[2]))  # Darkest first, then largest
                x, y, r, _ = valid_circles[0]
                return (x, y, r)
        
        return (None, None, None)
        
    def is_pupil_stable(self, current_radius: float) -> bool:
        """Check if the pupil size is stable over multiple frames"""
        if not self.last_pupil_sizes:
            self.last_pupil_sizes.append(current_radius)
            return False
        
        # Calculate the difference between the current and previous pupil sizes
        diff = abs(current_radius - self.last_pupil_sizes[-1])
        
        # If the difference is small enough and the number of stable frames is reached
        if diff < STABLE_THRESHOLD and len(self.last_pupil_sizes) >= STABLE_FRAMES:
            return True
        
        # Add the current radius to the list
        self.last_pupil_sizes.append(current_radius)
        
        # Keep only the last STABLE_FRAMES elements
        if len(self.last_pupil_sizes) > STABLE_FRAMES:
            self.last_pupil_sizes.pop(0)
            
        return False

    def run_measurement_sequence(self):
        """Run the complete measurement sequence with recording"""
        print("Starting full pupil measurement sequence with recording...")
        print("You should see the camera preview on your display")
        print("The system will wait for proximity trigger or start immediately")
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
                self.set_ir_led(50)  # 50% IR LED brightness only
                self.last_pupil_sizes = []  # Reset stability tracking
                
                measurement_start = time.time()
                first_radius = None
                
                while time.time() - measurement_start < 10:  # Timeout after 10 seconds
                    frame = self.camera.capture_array()
                    x, y, radius = self.detect_pupil(frame)
                    
                    # Add debug overlay and record frame
                    if self.record_video:
                        overlay_frame = self.add_debug_overlay(frame, x, y, radius)
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
                
                # Phase 2: Add 5% white light
                self.current_phase = "Phase 2: Adding Light"
                print("Phase 2: Adding 5% white light...")
                self.set_all_color(255, 255, 255, 5)  # 5% white light
                # Keep IR LED at 50%
                self.last_pupil_sizes = []  # Reset stability tracking
                
                # Wait a moment for pupil to adjust
                time.sleep(1)
                
                # Phase 3: Measure final pupil size
                self.current_phase = "Phase 3: Measuring Response"
                print("Phase 3: Measuring pupil response to light...")
                second_measurement_start = time.time()
                second_radius = None
                
                while time.time() - second_measurement_start < 10:  # 10 second timeout
                    frame = self.camera.capture_array()
                    new_x, new_y, new_radius = self.detect_pupil(frame)
                    
                    # Add debug overlay and record frame
                    if self.record_video:
                        overlay_frame = self.add_debug_overlay(frame, new_x, new_y, new_radius)
                        self.write_frame_to_video(overlay_frame)
                    
                    if new_radius is not None:
                        print(f"Phase 3 - Detected pupil: position=({new_x}, {new_y}), radius={new_radius}")
                        
                        if self.is_pupil_stable(new_radius):
                            second_radius = new_radius
                            self.measurement_data['response_radius'] = second_radius
                            print(f"✓ PHASE 3 MEASUREMENT STABLE: {second_radius} pixels (with 5% white)")
                            break
                    
                    time.sleep(0.1)
                
                if second_radius is None:
                    print("✗ Phase 3 failed - no stable pupil detected with white light")
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
                print(f"Response pupil size (5% white): {second_radius} pixels")
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
    print("Full Pupil Measurement System with Recording")
    print("=" * 50)
    
    try:
        # Try with preview first, fall back to no preview if display issues
        pupil_system = SimplePupilMeasurement(record_video=True, show_preview=True)
        pupil_system.run_measurement_sequence()
    except Exception as e:
        print(f"Error: {e}")
        GPIO.cleanup() 