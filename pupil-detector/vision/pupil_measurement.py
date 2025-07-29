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

# Constants
LED_COUNT = 12        # Number of LED pixels
LED_PIN = 18         # GPIO pin connected to the pixels (must support PWM)
LED_FREQ_HZ = 800000 # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10         # DMA channel to use for generating signal
LED_BRIGHTNESS = 255 # Set to 0 for darkest and 255 for brightest
LED_CHANNEL = 0      # PWM channel
LED_INVERT = False   # True to invert the signal

PROXIMITY_PIN = 4    # GPIO pin for proximity sensor
STABLE_THRESHOLD = 2.0  # Maximum allowed pupil size variation to consider stable (in pixels)
STABLE_FRAMES = 10   # Number of frames pupil size must be stable for

class PupilMeasurement:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.setup_camera()
        self.setup_proximity_sensor()
        self.setup_leds()
        self.last_pupil_sizes = []
        
    def setup_camera(self):
        """Initialize camera and window if in debug mode"""
        self.camera = Picamera2()
        preview_config = self.camera.create_preview_configuration(
            main={"size": (640, 480)},
            lores={"size": (320, 240), "format": "YUV420"})
        self.camera.configure(preview_config)
        self.camera.start()
        
        if self.debug:
            os.environ["DISPLAY"] = ":0"
            cv2.namedWindow("Pupil Detection", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Pupil Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    def setup_proximity_sensor(self):
        """Initialize proximity sensor with internal pull-up"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PROXIMITY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
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
    
    def detect_pupil(self, frame) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Detect pupil in frame, return (x, y, radius) or (None, None, None)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        
        # First detect iris (larger circle)
        iris_circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=200,
            param1=50,
            param2=30,
            minRadius=50,
            maxRadius=150
        )
        
        if iris_circles is None:
            return None, None, None
        
        # Get the largest circle (iris)
        iris = np.uint16(np.around(iris_circles[0][0]))
        ix, iy, ir = iris
        
        # Create mask for iris region
        mask = np.zeros_like(gray)
        cv2.circle(mask, (ix, iy), ir, 255, -1)
        masked = cv2.bitwise_and(gray, gray, mask=mask)
        
        # Detect pupil within iris
        pupil_circles = cv2.HoughCircles(
            masked,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=25,
            minRadius=20,
            maxRadius=int(ir * 0.7)  # Pupil should be smaller than iris
        )
        
        if pupil_circles is None:
            return None, None, None
            
        pupil = np.uint16(np.around(pupil_circles[0][0]))
        return pupil[0], pupil[1], pupil[2]
    
    def is_pupil_stable(self, radius: int) -> bool:
        """Check if pupil size has been stable for the required number of frames"""
        self.last_pupil_sizes.append(radius)
        if len(self.last_pupil_sizes) > STABLE_FRAMES:
            self.last_pupil_sizes.pop(0)
            if len(self.last_pupil_sizes) == STABLE_FRAMES:
                variation = np.std(self.last_pupil_sizes)
                return variation < STABLE_THRESHOLD
        return False
    
    def run_measurement_sequence(self):
        """Run the complete measurement sequence"""
        try:
            while True:
                # Wait for proximity trigger
                if GPIO.input(PROXIMITY_PIN):  # Active low
                    self.set_all_color(0, 0, 0)  # LEDs off
                    time.sleep(0.1)
                    continue
                
                # Object detected - start measurement sequence
                print("Object detected - starting measurement")
                self.set_all_color(255, 255, 255, 5)  # 5% white
                self.last_pupil_sizes = []  # Reset stability tracking
                
                measurement_start = time.time()
                while time.time() - measurement_start < 10:  # Timeout after 10 seconds
                    frame = self.camera.capture_array()
                    x, y, radius = self.detect_pupil(frame)
                    
                    if radius is not None:
                        # Draw detection visualization if in debug mode
                        if self.debug:
                            cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
                            cv2.putText(frame, f"Pupil size: {radius}", (10, 30),
                                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
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
                                    cv2.circle(frame, (new_x, new_y), new_radius, (0, 255, 0), 2)
                                    cv2.putText(frame, f"New size: {new_radius}", (10, 60),
                                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                
                                if self.debug:
                                    cv2.imshow("Pupil Detection", frame)
                                    if cv2.waitKey(1) & 0xFF == ord('q'):
                                        return
                                
                                if new_radius is not None and self.is_pupil_stable(new_radius):
                                    print(f"Second measurement stable at {new_radius}")
                                    size_change = ((new_radius - radius) / radius) * 100
                                    print(f"Size change: {size_change:.1f}%")
                                    time.sleep(1)
                                    break
                            
                            # Reset for next measurement
                            self.set_all_color(0, 0, 0)
                            break
                    
                    if self.debug:
                        cv2.imshow("Pupil Detection", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            return
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
        except KeyboardInterrupt:
            print("Measurement stopped by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.debug:
            cv2.destroyAllWindows()
        self.camera.stop()
        GPIO.cleanup()
        self.set_all_color(0, 0, 0)

def main():
    parser = argparse.ArgumentParser(description="Pupil measurement with proximity trigger and LED feedback")
    parser.add_argument("--debug", action="store_true", help="Enable debug visualization")
    args = parser.parse_args()
    
    measurement = PupilMeasurement(debug=args.debug)
    measurement.run_measurement_sequence()

if __name__ == "__main__":
    main() 