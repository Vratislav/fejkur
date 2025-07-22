#!/usr/bin/env python3
"""
Simple GPIO test using RPi.GPIO directly
"""

import time
import logging
import RPi.GPIO as GPIO

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_gpio():
    """Test GPIO functionality"""
    try:
        logger.info("Testing GPIO with RPi.GPIO...")
        
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        logger.info("GPIO 17 set up as input with pull-up")
        logger.info("Press the button to test (Ctrl+C to exit)")
        
        press_count = 0
        
        while True:
            # Check button state
            if GPIO.input(17) == GPIO.LOW:  # Button pressed (connected to GND)
                press_count += 1
                logger.info(f"Button PRESSED! (count: {press_count})")
                
                # Wait for button release
                while GPIO.input(17) == GPIO.LOW:
                    time.sleep(0.1)
                
                logger.info("Button released")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"GPIO test failed: {e}")
    finally:
        GPIO.cleanup()
        logger.info("GPIO cleaned up")

if __name__ == "__main__":
    test_gpio() 