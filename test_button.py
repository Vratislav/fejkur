#!/usr/bin/env python3
"""
Simple button test script
Tests GPIO button functionality
"""

import time
import logging
from gpiozero import Button

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_button():
    """Test button functionality"""
    try:
        logger.info("Testing button on GPIO 17...")
        
        # Initialize button with pull-up (for GND-connected button)
        button = Button(
            pin=17,
            pull_up=True,
            bounce_time=0.1
        )
        
        logger.info("Button initialized successfully")
        logger.info("Press the button to test (Ctrl+C to exit)")
        
        press_count = 0
        
        while True:
            # Check button state
            if button.is_pressed:
                press_count += 1
                logger.info(f"Button PRESSED! (count: {press_count})")
                
                # Wait for button release
                while button.is_pressed:
                    time.sleep(0.1)
                
                logger.info("Button released")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Button test failed: {e}")

if __name__ == "__main__":
    test_button() 