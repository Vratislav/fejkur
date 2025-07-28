#!/usr/bin/env python3
"""
Proximity Sensor with NeoPixel LED
- Uses GPIO 4 for proximity sensor (with pull-up)
- Uses GPIO 17 for NeoPixel LED
- Fades LED to white when object detected
"""

import os
import sys

import RPi.GPIO as GPIO
import time
import argparse
from collections import deque
from rpi_ws281x import PixelStrip, Color

class ProximityLED:
    def __init__(self, sensor_pin=4, brightness=1.0):
        print("DEBUG: Initializing ProximityLED...")
        
        # NeoPixel configuration
        LED_COUNT = 12       # Number of LED pixels
        LED_PIN = 18        # GPIO pin connected to the pixels (18 uses PWM!)
        LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
        LED_DMA = 10        # DMA channel to use for generating signal
        LED_BRIGHTNESS = int(brightness * 255)  # Set to 0 for darkest and 255 for brightest
        LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
        LED_CHANNEL = 0     # set to '1' for GPIOs 13, 19, 41, 45 or 53
        
        print(f"DEBUG: Setting up {LED_COUNT} NeoPixels on GPIO{LED_PIN} with brightness {LED_BRIGHTNESS}")
        try:
            self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
            self.strip.begin()
            print("DEBUG: NeoPixels initialized successfully")
            # Turn all LEDs off at start
            self.set_all_leds(0)
        except Exception as e:
            print(f"ERROR: Failed to initialize NeoPixels: {e}")
            raise
        
        # Sensor configuration
        print(f"DEBUG: Setting up proximity sensor on GPIO {sensor_pin}")
        self.sensor_pin = sensor_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print("DEBUG: Proximity sensor initialized")
        
        # Debouncing configuration
        self.debounce_time = 0.05  # 50ms debounce
        self.last_detection = 0
        
        # Smoothing configuration
        self.history = deque([0] * 5, maxlen=5)  # Keep last 5 readings
        self.current_brightness = 0
        self.target_brightness = 0
        self.fade_speed = 0.1  # Adjust for faster/slower fading
        
    def read_sensor(self):
        """Read sensor with debouncing"""
        current_time = time.time()
        
        # Check if enough time has passed since last detection
        if current_time - self.last_detection < self.debounce_time:
            return False
            
        # Sensor is active LOW (pulls to ground when detecting)
        detected = not GPIO.input(self.sensor_pin)
        
        if detected:
            self.last_detection = current_time
            print("DEBUG: Proximity sensor detected object")
            
        return detected
    
    def smooth_reading(self, detected):
        """Smooth sensor readings"""
        # Add current reading to history
        self.history.append(1 if detected else 0)
        
        # Calculate average (0.0 to 1.0)
        return sum(self.history) / len(self.history)
    
    def set_all_leds(self, brightness_percent):
        """Set all LEDs to the same brightness level"""
        # Convert percentage (0-100) to value (0-255)
        value = int(brightness_percent * 255 / 100)
        print(f"DEBUG: Setting all LEDs to {brightness_percent}% (value: {value})")
        try:
            # Set all LEDs to the same white color
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, Color(value, value, value))
            self.strip.show()
            print("DEBUG: LED brightness set successfully")
        except Exception as e:
            print(f"ERROR: Failed to set LED brightness: {e}")
    
    def update_led(self):
        """Update LEDs with smooth fading"""
        if abs(self.current_brightness - self.target_brightness) > 0.1:
            # Smoothly move towards target brightness
            if self.current_brightness < self.target_brightness:
                self.current_brightness += self.fade_speed
                print(f"DEBUG: Fading up to {self.current_brightness:.1f}")
            else:
                self.current_brightness -= self.fade_speed
                print(f"DEBUG: Fading down to {self.current_brightness:.1f}")
            
            # Ensure we stay within bounds
            self.current_brightness = max(0, min(5, self.current_brightness))  # Changed max to 5%
            
            # Update all LEDs
            self.set_all_leds(self.current_brightness)
    
    def run(self):
        """Main loop"""
        try:
            print("DEBUG: Starting main loop")
            print("Running... (Ctrl+C to exit)")
            
            # Start with LEDs off
            print("DEBUG: Setting initial LED state to off")
            self.set_all_leds(0)
            
            while True:
                # Read sensor (with debouncing)
                detected = self.read_sensor()
                
                # Smooth the readings
                smooth_value = self.smooth_reading(detected)
                print(f"DEBUG: Smooth sensor value: {smooth_value:.2f}")
                
                # Set target brightness (0% to 5%)
                self.target_brightness = smooth_value * 5  # Changed to 5%
                print(f"DEBUG: Target brightness: {self.target_brightness:.1f}%")
                
                # Update LEDs with smooth fading
                self.update_led()
                
                # Small delay to prevent CPU hogging
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nDEBUG: Received keyboard interrupt")
            print("Stopping...")
        except Exception as e:
            print(f"ERROR: Unexpected error in main loop: {e}")
        finally:
            # Clean up
            print("DEBUG: Cleaning up...")
            self.set_all_leds(0)  # Turn off all LEDs
            GPIO.cleanup()
            print("DEBUG: Cleanup complete")

def parse_args():
    parser = argparse.ArgumentParser(description='Proximity Sensor with NeoPixel LED')
    parser.add_argument('--sensor-pin', type=int, default=4,
                       help='GPIO pin for proximity sensor (BCM numbering)')
    parser.add_argument('--brightness', type=float, default=1.0,
                       help='Maximum LED brightness (0.0-1.0)')
    parser.add_argument('--debounce', type=float, default=0.05,
                       help='Debounce time in seconds')
    parser.add_argument('--fade-speed', type=float, default=0.1,
                       help='LED fade speed (0.01-1.0)')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Create and run controller
    controller = ProximityLED(
        sensor_pin=args.sensor_pin,
        brightness=args.brightness
    )
    
    # Set custom parameters
    controller.debounce_time = args.debounce
    controller.fade_speed = args.fade_speed
    
    # Run the controller
    controller.run()

if __name__ == "__main__":
    main() 