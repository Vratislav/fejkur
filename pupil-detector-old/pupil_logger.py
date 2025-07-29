#!/usr/bin/env python3
"""
Headless pupil detection with data logging.
Suitable for Raspberry Pi deployment without GUI.
"""

import cv2
import numpy as np
import argparse
import sys
import time
import json
import os
from datetime import datetime
from typing import Optional, Tuple

try:
    import pypupilext
except ImportError:
    print("Error: PyPupilEXT not found. Please install it using:")
    print("pip install PyPupilEXT-0.0.1-cp310-cp310-macosx_14_0_universal2.whl")
    sys.exit(1)


class PupilLogger:
    def __init__(self, camera_id: int = 0, log_file: str = None, log_interval: float = 1.0):
        """
        Initialize the pupil logger.
        
        Args:
            camera_id: Camera device ID (default: 0)
            log_file: File to log data to (default: auto-generated)
            log_interval: How often to log data in seconds (default: 1.0)
        """
        self.camera_id = camera_id
        self.log_interval = log_interval
        self.cap = None
        self.pupil_detector = None
        self.frame_count = 0
        self.start_time = time.time()
        self.last_log_time = 0
        
        # Setup logging
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = f"pupil_data_{timestamp}.json"
        else:
            self.log_file = log_file
        
        # Initialize data storage
        self.data = []
        
    def initialize_camera(self) -> bool:
        """Initialize the webcam capture."""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                print(f"Error: Could not open camera {self.camera_id}")
                return False
                
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print(f"Camera {self.camera_id} initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            return False
    
    def initialize_pupil_detector(self) -> bool:
        """Initialize the PyPupilEXT detector."""
        try:
            # Use PuRe algorithm for robust pupil detection
            self.pupil_detector = pypupilext.PuRe()
            print("PyPupilEXT detector initialized successfully")
            return True
        except Exception as e:
            print(f"Error initializing PyPupilEXT: {e}")
            return False
    
    def process_frame(self, frame: np.ndarray) -> Optional[Tuple[float, float, float]]:
        """
        Process a single frame for pupil detection.
        
        Returns:
            Tuple of (pupil_diameter, confidence, processing_time) or None if detection failed
        """
        try:
            start_time = time.time()
            
            # Convert frame to grayscale for pupil detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect pupil using PyPupilEXT
            pupil = self.pupil_detector.run(gray)
            
            processing_time = time.time() - start_time
            
            if pupil and pupil.valid(0.5):  # Check if pupil is valid with confidence threshold
                # Extract pupil diameter and confidence
                pupil_diameter = pupil.physicalDiameter
                confidence = pupil.confidence
                
                return pupil_diameter, confidence, processing_time
            
            return None
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            return None
    
    def log_data(self, pupil_data: Optional[Tuple[float, float, float]]):
        """Log detection data to file."""
        current_time = time.time()
        
        # Only log at specified interval
        if current_time - self.last_log_time < self.log_interval:
            return
        
        self.last_log_time = current_time
        
        # Create data entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "frame_count": self.frame_count,
            "elapsed_time": current_time - self.start_time
        }
        
        if pupil_data:
            diameter, confidence, proc_time = pupil_data
            entry.update({
                "pupil_diameter": diameter,
                "confidence": confidence,
                "processing_time": proc_time,
                "detection_success": True
            })
        else:
            entry.update({
                "pupil_diameter": None,
                "confidence": None,
                "processing_time": None,
                "detection_success": False
            })
        
        # Add to data list
        self.data.append(entry)
        
        # Save to file (append mode for real-time logging)
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def run(self):
        """Main detection loop."""
        if not self.initialize_camera():
            return
        
        if not self.initialize_pupil_detector():
            return
        
        print(f"Starting pupil detection with logging to {self.log_file}")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Process frame for pupil detection
                pupil_data = self.process_frame(frame)
                self.frame_count += 1
                
                # Log data
                self.log_data(pupil_data)
                
                # Output results to console (less frequent)
                if self.frame_count % 30 == 0:  # Every 30 frames
                    if pupil_data:
                        diameter, confidence, proc_time = pupil_data
                        print(f"Frame {self.frame_count}: Pupil {diameter:.2f}mm (confidence: {confidence:.2f})")
                    else:
                        print(f"Frame {self.frame_count}: No pupil detected")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nDetection stopped by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.cap:
            self.cap.release()
        
        print(f"Data logged to {self.log_file}")
        print(f"Total frames processed: {self.frame_count}")
        print("Cleanup completed")


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Headless pupil detection with data logging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pupil_logger.py                           # Basic logging
  python pupil_logger.py --log-file data.json     # Custom log file
  python pupil_logger.py --camera 1 --interval 0.5 # Camera 1, log every 0.5s
        """
    )
    
    parser.add_argument(
        '--camera', 
        type=int, 
        default=0,
        help='Camera device ID (default: 0)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Log file path (default: auto-generated)'
    )
    
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Logging interval in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    # Create and run logger
    logger = PupilLogger(
        camera_id=args.camera,
        log_file=args.log_file,
        log_interval=args.interval
    )
    logger.run()


if __name__ == "__main__":
    main() 