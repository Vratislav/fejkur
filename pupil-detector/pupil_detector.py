#!/usr/bin/env python3
"""
Pupil Detection Script using PyPupilEXT
Detects pupil size from webcam feed with optional debug visualization.
"""

import cv2
import numpy as np
import argparse
import sys
import time
from typing import Optional, Tuple

try:
    import pypupilext
except ImportError:
    print("Error: PyPupilEXT not found. Please install it using:")
    print("pip install PyPupilEXT-0.0.1-cp310-cp310-macosx_14_0_universal2.whl")
    sys.exit(1)


class PupilDetector:
    def __init__(self, debug: bool = False, camera_id: int = 0):
        """
        Initialize the pupil detector.
        
        Args:
            debug: Whether to show debug visualization
            camera_id: Camera device ID (default: 0)
        """
        self.debug = debug
        self.camera_id = camera_id
        self.cap = None
        self.pupil_detector = None
        self.frame_count = 0
        self.start_time = time.time()
        
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
        
        if pupil_data:
            diameter, confidence, proc_time = pupil_data
            cv2.putText(debug_frame, f"Pupil Diameter: {diameter:.2f}mm", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(debug_frame, f"Confidence: {confidence:.2f}", (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(debug_frame, f"Processing Time: {proc_time*1000:.1f}ms", (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(debug_frame, "No pupil detected", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return debug_frame
    
    def run(self):
        """Main detection loop."""
        if not self.initialize_camera():
            return
        
        if not self.initialize_pupil_detector():
            return
        
        print("Starting pupil detection...")
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
                    print(f"Pupil: {diameter:.2f}mm (confidence: {confidence:.2f}, time: {proc_time*1000:.1f}ms)")
                else:
                    print("No pupil detected")
                
                # Show debug window if enabled
                if self.debug:
                    debug_frame = self.draw_debug_info(frame, pupil_data)
                    cv2.imshow('Pupil Detection Debug', debug_frame)
                    
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
        description="Pupil detection using PyPupilEXT from webcam feed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pupil_detector.py                    # Basic detection
  python pupil_detector.py --debug           # With debug visualization
  python pupil_detector.py --camera 1        # Use camera 1
  python pupil_detector.py --debug --camera 1 # Debug mode with camera 1
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
    
    args = parser.parse_args()
    
    # Create and run detector
    detector = PupilDetector(debug=args.debug, camera_id=args.camera)
    detector.run()


if __name__ == "__main__":
    main() 