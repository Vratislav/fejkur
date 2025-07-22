#!/usr/bin/env python3
"""
Calibrated Pupil Detection Script using PyPupilEXT
Detects pupil size from webcam feed with calibration for accurate measurements.
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


class CalibratedPupilDetector:
    def __init__(self, debug: bool = False, camera_id: int = 0, calibration_file: str = None):
        """
        Initialize the calibrated pupil detector.
        
        Args:
            debug: Whether to show debug visualization
            camera_id: Camera device ID (default: 0)
            calibration_file: Path to calibration JSON file
        """
        self.debug = debug
        self.camera_id = camera_id
        self.cap = None
        self.pupil_detector = None
        self.frame_count = 0
        self.start_time = time.time()
        self.calibration_factor = None
        
        # Load calibration if provided
        if calibration_file:
            self.load_calibration(calibration_file)
        
    def load_calibration(self, calibration_file: str) -> bool:
        """Load calibration data from file."""
        try:
            with open(calibration_file, 'r') as f:
                calibration_data = json.load(f)
            
            self.calibration_factor = calibration_data.get('calibration_factor_mm_per_pixel')
            if self.calibration_factor:
                print(f"Loaded calibration factor: {self.calibration_factor:.4f} mm/px")
                return True
            else:
                print("No calibration factor found in file")
                return False
                
        except Exception as e:
            print(f"Error loading calibration: {e}")
            return False
    
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
    
    def apply_calibration(self, pixel_diameter: float) -> float:
        """Apply calibration factor to convert pixels to millimeters."""
        if self.calibration_factor:
            return pixel_diameter * self.calibration_factor
        else:
            return pixel_diameter  # Return pixels if no calibration
    
    def process_frame(self, frame: np.ndarray) -> Optional[Tuple[float, float, float]]:
        """
        Process a single frame for pupil detection.
        
        Returns:
            Tuple of (pupil_diameter_mm, confidence, processing_time) or None if detection failed
        """
        try:
            start_time = time.time()
            
            # Convert frame to grayscale for pupil detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect pupil using PyPupilEXT
            pupil = self.pupil_detector.run(gray)
            
            processing_time = time.time() - start_time
            
            if pupil and pupil.valid(0.5):  # Check if pupil is valid with confidence threshold
                # Get pixel diameter from PyPupilEXT
                pixel_diameter = pupil.diameter()
                confidence = pupil.confidence
                
                # Apply calibration to get physical diameter
                physical_diameter = self.apply_calibration(pixel_diameter)
                
                return physical_diameter, confidence, processing_time
            
            return None
            
        except Exception as e:
            if self.debug:
                print(f"Error processing frame: {e}")
            return None
    
    def draw_debug_info(self, frame: np.ndarray, pupil_data: Optional[Tuple[float, float, float]]) -> np.ndarray:
        """Draw debug information on the frame."""
        debug_frame = frame.copy()
        
        # Add frame counter and FPS
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0
        
        cv2.putText(debug_frame, f"Frame: {self.frame_count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(debug_frame, f"FPS: {fps:.1f}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show calibration status
        if self.calibration_factor:
            cv2.putText(debug_frame, f"Calibrated: {self.calibration_factor:.4f} mm/px", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
            cv2.putText(debug_frame, "Not calibrated (pixels only)", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        if pupil_data:
            diameter, confidence, proc_time = pupil_data
            unit = "mm" if self.calibration_factor else "px"
            cv2.putText(debug_frame, f"Pupil Diameter: {diameter:.2f}{unit}", (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(debug_frame, f"Confidence: {confidence:.2f}", (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(debug_frame, f"Processing Time: {proc_time*1000:.1f}ms", (10, 180), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(debug_frame, "No pupil detected", (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return debug_frame
    
    def run(self):
        """Main detection loop."""
        if not self.initialize_camera():
            return
        
        if not self.initialize_pupil_detector():
            return
        
        print("Starting calibrated pupil detection...")
        if self.calibration_factor:
            print(f"Using calibration factor: {self.calibration_factor:.4f} mm/px")
        else:
            print("No calibration loaded - measurements in pixels only")
        print("Press 'q' to quit, 'd' to toggle debug mode")
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Process frame for pupil detection
                pupil_data = self.process_frame(frame)
                
                # Output results to console
                if pupil_data:
                    diameter, confidence, proc_time = pupil_data
                    unit = "mm" if self.calibration_factor else "px"
                    print(f"Pupil: {diameter:.2f}{unit} (confidence: {confidence:.2f}, time: {proc_time*1000:.1f}ms)")
                else:
                    print("No pupil detected")
                
                # Show debug window if enabled
                if self.debug:
                    debug_frame = self.draw_debug_info(frame, pupil_data)
                    cv2.imshow('Calibrated Pupil Detection Debug', debug_frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('d'):
                        self.debug = not self.debug
                        if not self.debug:
                            cv2.destroyAllWindows()
                
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
        cv2.destroyAllWindows()
        print("Cleanup completed")


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Calibrated pupil detection using PyPupilEXT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pupil_detector_calibrated.py                                    # Basic detection
  python pupil_detector_calibrated.py --debug                           # With debug visualization
  python pupil_detector_calibrated.py --calibration calibration.json    # With calibration file
  python pupil_detector_calibrated.py --debug --calibration cal.json   # Debug with calibration
        """
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode with visualization window'
    )
    
    parser.add_argument(
        '--camera', 
        type=int, 
        default=0,
        help='Camera device ID (default: 0)'
    )
    
    parser.add_argument(
        '--calibration',
        type=str,
        default=None,
        help='Path to calibration JSON file'
    )
    
    args = parser.parse_args()
    
    # Create and run detector
    detector = CalibratedPupilDetector(
        debug=args.debug, 
        camera_id=args.camera,
        calibration_file=args.calibration
    )
    detector.run()


if __name__ == "__main__":
    main() 