#!/usr/bin/env python3

import os
import time
import argparse
import numpy as np
from typing import Tuple, Optional
import cv2
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color

# Force local display on Pi (not SSH forwarded)
os.environ.pop('DISPLAY', None)  # Remove SSH forwarded display
os.environ.pop('SSH_CLIENT', None)  # Remove SSH indicators

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

class PupilMeasurement:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.setup_camera()
        self.setup_proximity_sensor()
        self.setup_ir_led()
        self.setup_leds()
        self.last_pupil_sizes = []
        
    def setup_camera(self):
        """Initialize camera and window if in debug mode"""
        self.camera = Picamera2()
        
        # Use the exact same configuration as our working test script
        preview_config = self.camera.create_preview_configuration(main={"size": (640, 480)})
        self.camera.configure(preview_config)
        
        if self.debug:
            # Use the exact method that worked in our test
            self.camera.start(show_preview=True)
        else:
            self.camera.start()
    
    def setup_proximity_sensor(self):
        """Initialize proximity sensor with internal pull-up"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PROXIMITY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    def setup_ir_led(self):
        """Initialize IR LED with PWM"""
        GPIO.setup(IR_LED_PIN, GPIO.OUT)
        self.ir_pwm = GPIO.PWM(IR_LED_PIN, IR_LED_FREQ)
        self.ir_pwm.start(0)  # Start with LED off
    
    def set_ir_led(self, duty_cycle: float):
        """Set IR LED brightness (0-100)"""
        self.ir_pwm.ChangeDutyCycle(duty_cycle)
    
    def setup_leds(self):
        """Initialize NeoPixel strip"""
        self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        self.set_all_color(0, 0, 0)  # Start with all LEDs off
    
    def set_all_color(self, red: int, green: int, blue: int, brightness_percent: float = 100):
        """Set all LEDs to specified RGB color with brightness percentage"""
        brightness = int((brightness_percent / 100.0) * 255)
        color = Color(red, green, blue)
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, color)
            self.strip.setBrightness(brightness)
        self.strip.show()

    def detect_pupil(self, frame: np.ndarray) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Detect pupil in the frame using OpenCV"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)
        
        # Use HoughCircles to find circles (potential pupils)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 100, param1=50, param2=30, minRadius=10, maxRadius=50)
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                # Check if the circle is within the frame boundaries
                if x - r > 0 and x + r < frame.shape[1] and y - r > 0 and y + r < frame.shape[0]:
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
        """Run the complete measurement sequence"""
        try:
            while True:
                # Wait for proximity trigger
                if GPIO.input(PROXIMITY_PIN):  # Active low
                    self.set_all_color(0, 0, 0)  # LEDs off
                    self.set_ir_led(0)  # IR LED off
                    time.sleep(0.1)
                    continue
                
                # Object detected - start measurement sequence
                print("Object detected - starting measurement")
                self.set_all_color(255, 255, 255, 5)  # 5% white
                self.set_ir_led(50)  # 50% IR LED brightness
                self.last_pupil_sizes = []  # Reset stability tracking
                
                measurement_start = time.time()
                while time.time() - measurement_start < 10:  # Timeout after 10 seconds
                    frame = self.camera.capture_array()
                    x, y, radius = self.detect_pupil(frame)
                    
                    if radius is not None:
                        if self.debug:
                            print(f"Detected pupil at ({x}, {y}) with radius {radius}")
                        
                        if self.is_pupil_stable(radius):
                            print(f"Pupil stable at size {radius}")
                            # Blink green
                            self.set_all_color(0, 255, 0, 15)
                            time.sleep(0.5)
                            # Back to white 5%
                            self.set_all_color(255, 255, 255, 5)
                            time.sleep(0.5)
                            # Fade to white 35%
                            for brightness in range(5, 36):
                                self.set_all_color(255, 255, 255, brightness)
                                time.sleep(0.02)
                            
                            # Wait for second measurement
                            second_measurement_start = time.time()
                            self.last_pupil_sizes = []  # Reset stability tracking
                            
                            while time.time() - second_measurement_start < 5:  # 5 second timeout
                                frame = self.camera.capture_array()
                                new_x, new_y, new_radius = self.detect_pupil(frame)
                                
                                if new_radius is not None and self.debug:
                                    print(f"Second measurement: pupil at ({new_x}, {new_y}) with radius {new_radius}")
                                
                                if new_radius is not None and self.is_pupil_stable(new_radius):
                                    print(f"Second measurement stable at {new_radius}")
                                    size_change = ((new_radius - radius) / radius) * 100
                                    print(f"Size change: {size_change:.1f}%")
                                    time.sleep(1)
                                    break
                            
                            # Reset for next measurement
                            self.set_all_color(0, 0, 0)
                            self.set_ir_led(0)  # Turn off IR LED
                            break
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
        except KeyboardInterrupt:
            print("Measurement stopped by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.camera.stop()
        self.ir_pwm.stop()  # Stop PWM for IR LED
        GPIO.cleanup()
        self.set_all_color(0, 0, 0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pupil Measurement System")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (camera window)")
    args = parser.parse_args()

    pupil_measurement = PupilMeasurement(debug=args.debug)
    pupil_measurement.run_measurement_sequence() 