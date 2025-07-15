"""
Button Handler for Voice Recognition Door Opener
Manages GPIO button input for triggering voice recognition
"""

import time
import logging
import threading
from typing import Optional, Callable
import RPi.GPIO as GPIO


class ButtonHandler:
    """Manages GPIO button input and LED status indicator"""
    
    def __init__(self, config):
        """Initialize button handler"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.gpio_config = config.get_gpio_config()
        
        # GPIO components
        self.button_pin = None
        self.led_pin = None
        self.button_callback = None
        
        # Button settings
        self.button_pin = self.gpio_config.get('button_pin', 17)
        self.led_pin = self.gpio_config.get('led_pin', 18)
        self.button_bounce_time = self.gpio_config.get('button_bounce_time', 0.3)
        
        # State management
        self.button_pressed = False
        self.last_press_time = 0
        self.press_count = 0
        self.running = False
        
        # Threading
        self.monitor_thread = None
    
    def initialize(self):
        """Initialize GPIO button and LED"""
        try:
            self.logger.info("Initializing button handler...")
            
            # Set up GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Set up LED if configured
            if self.led_pin is not None:
                try:
                    GPIO.setup(self.led_pin, GPIO.OUT)
                    GPIO.output(self.led_pin, GPIO.LOW)  # Start with LED off
                    self.logger.info(f"Status LED initialized on GPIO {self.led_pin}")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize status LED: {e}")
                    self.led_pin = None
            
            # Start monitoring thread
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_button, daemon=True)
            self.monitor_thread.start()
            
            self.logger.info(f"Button handler initialized successfully on GPIO {self.button_pin}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize button handler: {e}")
            return False
    
    def _monitor_button(self):
        """Monitor button state in background thread"""
        while self.running:
            try:
                # Check button state
                button_state = GPIO.input(self.button_pin)
                
                if button_state == GPIO.LOW and not self.button_pressed:  # Button pressed
                    current_time = time.time()
                    
                    # Debounce check
                    if current_time - self.last_press_time < self.button_bounce_time:
                        time.sleep(0.1)
                        continue
                    
                    self.last_press_time = current_time
                    self.button_pressed = True
                    self.press_count += 1
                    
                    self.logger.info(f"Button pressed (count: {self.press_count})")
                    
                    # Update LED status
                    self._set_led_status('pressed')
                    
                    # Call callback if set
                    if self.button_callback:
                        try:
                            self.button_callback()
                        except Exception as e:
                            self.logger.error(f"Error in button callback: {e}")
                
                elif button_state == GPIO.HIGH and self.button_pressed:  # Button released
                    self.button_pressed = False
                    self.logger.debug("Button released")
                    
                    # Update LED status
                    self._set_led_status('released')
                
                time.sleep(0.01)  # Check every 10ms
                
            except Exception as e:
                self.logger.error(f"Error in button monitor: {e}")
                time.sleep(1)
    
    def _set_led_status(self, status):
        """Set LED status indicator"""
        if not self.led_pin:
            return
        
        try:
            if status == 'pressed':
                GPIO.output(self.led_pin, GPIO.HIGH)
            elif status == 'released':
                GPIO.output(self.led_pin, GPIO.LOW)
            elif status == 'processing':
                # Blink LED during processing
                for _ in range(3):
                    GPIO.output(self.led_pin, GPIO.HIGH)
                    time.sleep(0.2)
                    GPIO.output(self.led_pin, GPIO.LOW)
                    time.sleep(0.2)
            elif status == 'success':
                # Quick blink for success
                for _ in range(3):
                    GPIO.output(self.led_pin, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(self.led_pin, GPIO.LOW)
                    time.sleep(0.1)
            elif status == 'error':
                # Slow blink for error
                for _ in range(2):
                    GPIO.output(self.led_pin, GPIO.HIGH)
                    time.sleep(0.5)
                    GPIO.output(self.led_pin, GPIO.LOW)
                    time.sleep(0.5)
            elif status == 'ready':
                # Solid on for ready state
                GPIO.output(self.led_pin, GPIO.HIGH)
                
        except Exception as e:
            self.logger.error(f"Error setting LED status: {e}")
    
    def set_callback(self, callback: Callable):
        """Set button press callback function"""
        self.button_callback = callback
        self.logger.info("Button callback set")
    
    def is_button_pressed(self):
        """Check if button is currently pressed"""
        return self.button_pressed
    
    def get_press_count(self):
        """Get total button press count"""
        return self.press_count
    
    def reset_press_count(self):
        """Reset button press counter"""
        self.press_count = 0
        self.logger.info("Button press count reset")
    
    def set_led_status(self, status: str):
        """Set LED status indicator"""
        self._set_led_status(status)
    
    def test_button(self) -> bool:
        """Test button functionality"""
        try:
            self.logger.info("Testing button functionality...")
            
            # Check if button is accessible
            if not self.running:
                self.logger.error("Button handler not initialized")
                return False
            
            # Simple test - check if we can read the button state
            initial_state = GPIO.input(self.button_pin)
            self.logger.info(f"Initial button state: {'pressed' if initial_state == GPIO.LOW else 'released'}")
            
            # Wait a moment and check again
            time.sleep(0.5)
            current_state = GPIO.input(self.button_pin)
            self.logger.info(f"Current button state: {'pressed' if current_state == GPIO.LOW else 'released'}")
            
            self.logger.info("Button test completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Button test failed: {e}")
            return False
    
    def get_button_info(self):
        """Get button information"""
        return {
            'pin': self.button_pin,
            'press_count': self.press_count,
            'is_pressed': self.button_pressed,
            'running': self.running
        }
    
    def shutdown(self):
        """Shutdown button handler"""
        try:
            self.logger.info("Shutting down button handler...")
            self.running = False
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1)
            
            # Clean up GPIO
            GPIO.cleanup()
            
            self.logger.info("Button handler shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during button handler shutdown: {e}") 