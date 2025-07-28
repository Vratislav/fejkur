#!/usr/bin/env python3
"""
Proximity Sensor Reader
Reads digital input from MH Flying Fish IR sensor connected to GPIO 4
Supports internal pull-up/pull-down resistor configuration
"""

import RPi.GPIO as GPIO
import time
import argparse

class ProximitySensor:
    def __init__(self, pin=4, debug=False, pull='up'):
        """
        Initialize proximity sensor
        pin: GPIO pin number (BCM)
        debug: Enable debug output
        pull: Resistor configuration ('up', 'down', or 'none')
        """
        self.pin = pin
        self.debug = debug
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)  # Use BCM numbering
        
        # Configure pull-up/pull-down resistor
        if pull == 'up':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print(f"GPIO {self.pin} configured with internal pull-up resistor")
        elif pull == 'down':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            print(f"GPIO {self.pin} configured with internal pull-down resistor")
        else:
            GPIO.setup(self.pin, GPIO.IN)
            print(f"GPIO {self.pin} configured without pull-up/down resistor")
        
        print(f"Proximity sensor initialized on GPIO {self.pin}")
        print("Press Ctrl+C to exit")
        
    def read(self):
        """Read current sensor state"""
        return GPIO.input(self.pin)
    
    def monitor(self, interval=0.1):
        """Continuously monitor sensor"""
        last_state = None
        
        try:
            while True:
                current_state = self.read()
                
                # If debug mode, print every reading
                if self.debug:
                    print(f"Sensor state: {'HIGH' if current_state else 'LOW'}")
                # Otherwise, only print on state change
                elif current_state != last_state:
                    print(f"Sensor state changed: {'HIGH' if current_state else 'LOW'}")
                    
                last_state = current_state
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping sensor monitor...")
        finally:
            GPIO.cleanup()
            
    def wait_for_detection(self, timeout=None, active_low=False):
        """
        Wait for object detection
        active_low: If True, consider LOW state as detection
        """
        print("Waiting for object detection...")
        
        try:
            start_time = time.time()
            while timeout is None or (time.time() - start_time) < timeout:
                state = self.read()
                if active_low:
                    detected = not state  # LOW = detected
                else:
                    detected = state      # HIGH = detected
                    
                if detected:
                    print("Object detected!")
                    return True
                time.sleep(0.1)
                
            print("Timeout reached, no object detected")
            return False
            
        except KeyboardInterrupt:
            print("\nStopping detection wait...")
            return False
        finally:
            GPIO.cleanup()

def parse_args():
    parser = argparse.ArgumentParser(description='Proximity Sensor Monitor')
    parser.add_argument('--pin', type=int, default=4,
                       help='GPIO pin number (BCM numbering)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output (print all readings)')
    parser.add_argument('--interval', type=float, default=0.1,
                       help='Reading interval in seconds')
    parser.add_argument('--wait', action='store_true',
                       help='Wait for single detection')
    parser.add_argument('--timeout', type=float,
                       help='Detection timeout in seconds')
    parser.add_argument('--pull', choices=['up', 'down', 'none'], default='up',
                       help='Internal resistor configuration (default: up)')
    parser.add_argument('--active-low', action='store_true',
                       help='Consider LOW state as detection')
    return parser.parse_args()

def main():
    args = parse_args()
    sensor = ProximitySensor(pin=args.pin, debug=args.debug, pull=args.pull)
    
    if args.wait:
        sensor.wait_for_detection(args.timeout, args.active_low)
    else:
        sensor.monitor(args.interval)

if __name__ == "__main__":
    main() 