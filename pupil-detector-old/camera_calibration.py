#!/usr/bin/env python3
"""
Camera Calibration Script for PyPupilEXT
This script helps calibrate the camera for accurate pupil size measurements.
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


class CameraCalibrator:
    def __init__(self, camera_id: int = 0):
        """
        Initialize the camera calibrator.
        
        Args:
            camera_id: Camera device ID (default: 0)
        """
        self.camera_id = camera_id
        self.cap = None
        self.calibration_data = {}
        self.known_sizes = {
            'small': 2.0,    # 2mm diameter
            'medium': 4.0,   # 4mm diameter  
            'large': 6.0,    # 6mm diameter
        }
        
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
    
    def detect_circles(self, frame: np.ndarray) -> list:
        """Detect circles in the frame for calibration targets."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use Hough Circle Transform to detect circles
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=100
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            return circles
        return []
    
    def measure_circle_diameter(self, frame: np.ndarray, circle: tuple) -> float:
        """Measure the diameter of a detected circle in pixels."""
        x, y, radius = circle
        diameter_pixels = radius * 2
        
        # Draw the detected circle for visualization
        cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
        cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)
        
        return diameter_pixels
    
    def calculate_calibration_factor(self, pixel_measurements: dict, known_sizes: dict) -> float:
        """Calculate the calibration factor (mm per pixel)."""
        total_factor = 0
        count = 0
        
        for size_name, pixel_diameter in pixel_measurements.items():
            if size_name in known_sizes:
                known_diameter_mm = known_sizes[size_name]
                factor = known_diameter_mm / pixel_diameter
                total_factor += factor
                count += 1
                print(f"{size_name}: {pixel_diameter:.1f}px = {known_diameter_mm}mm (factor: {factor:.4f} mm/px)")
        
        if count > 0:
            avg_factor = total_factor / count
            print(f"Average calibration factor: {avg_factor:.4f} mm/px")
            return avg_factor
        else:
            print("No valid measurements found for calibration")
            return None
    
    def save_calibration(self, calibration_factor: float, filename: str = None):
        """Save calibration data to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"calibration_{timestamp}.json"
        
        calibration_data = {
            "timestamp": datetime.now().isoformat(),
            "calibration_factor_mm_per_pixel": calibration_factor,
            "camera_id": self.camera_id,
            "resolution": {
                "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(calibration_data, f, indent=2)
        
        print(f"Calibration saved to {filename}")
        return filename
    
    def run_calibration(self, debug_mode=False):
        """Run the calibration process."""
        if not self.initialize_camera():
            return
        
        print("Camera Calibration for PyPupilEXT")
        print("="*50)
        print("This script helps calibrate your camera for accurate pupil measurements.")
        print("You'll need calibration targets with known sizes.")
        print("\nCalibration targets needed:")
        for name, size in self.known_sizes.items():
            print(f"  {name}: {size}mm diameter circle")
        print("\nYou can create these using:")
        print("1. Printed circles on paper")
        print("2. Physical objects with known diameters")
        print("3. Digital calibration targets on screen")
        
        if debug_mode:
            print("\nDEBUG MODE: Press Enter to start calibration...")
        else:
            input("\nPress Enter when ready to start calibration...")
        
        pixel_measurements = {}
        
        for size_name, known_size in self.known_sizes.items():
            print(f"\nCalibrating {size_name} target ({known_size}mm)...")
            print(f"Show the {size_name} target to the camera and press 'c' to capture")
            print("Press 'q' to quit or 's' to skip this target")
            
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Detect circles
                circles = self.detect_circles(frame)
                
                # Draw detected circles
                for circle in circles:
                    x, y, radius = circle
                    cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
                    cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)
                
                # Add instructions to frame
                cv2.putText(frame, f"Show {size_name} target ({known_size}mm)", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, "Press 'c' to capture, 's' to skip, 'q' to quit", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                if debug_mode:
                    cv2.putText(frame, "DEBUG MODE", (10, 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                cv2.imshow('Camera Calibration', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    return
                elif key == ord('s'):
                    print(f"Skipping {size_name} target")
                    break
                elif key == ord('c') and len(circles) > 0:
                    # Use the largest circle detected
                    largest_circle = max(circles, key=lambda x: x[2])
                    diameter_pixels = largest_circle[2] * 2
                    pixel_measurements[size_name] = diameter_pixels
                    print(f"Captured {size_name}: {diameter_pixels:.1f} pixels")
                    break
        
        cv2.destroyAllWindows()
        
        if len(pixel_measurements) < 2:
            print("Need at least 2 measurements for calibration")
            return
        
        # Calculate calibration factor
        calibration_factor = self.calculate_calibration_factor(pixel_measurements, self.known_sizes)
        
        if calibration_factor:
            # Save calibration
            filename = self.save_calibration(calibration_factor)
            
            print(f"\nCalibration completed!")
            print(f"Calibration factor: {calibration_factor:.4f} mm/px")
            print(f"Use this factor in your pupil detection scripts")
            print(f"Calibration saved to: {filename}")
            
            # Show how to use the calibration
            print("\nTo use this calibration in your scripts:")
            print("1. Load the calibration file")
            print("2. Apply the calibration factor to pupil measurements")
            print("3. Update your detection scripts to use calibrated measurements")
        else:
            print("Calibration failed. Please try again with better targets.")


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Camera calibration for PyPupilEXT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python camera_calibration.py                    # Basic calibration
  python camera_calibration.py --camera 1        # Use camera 1
  python camera_calibration.py --debug           # Debug mode
        """
    )
    
    parser.add_argument(
        '--camera', 
        type=int, 
        default=0,
        help='Camera device ID (default: 0)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with additional visual feedback'
    )
    
    args = parser.parse_args()
    
    # Create and run calibrator
    calibrator = CameraCalibrator(camera_id=args.camera)
    calibrator.run_calibration(debug_mode=args.debug)


if __name__ == "__main__":
    main() 