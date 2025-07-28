#!/usr/bin/env python3
"""
Iris and Pupil Detection Script
Shows live camera feed with iris and pupil detection, plus calibration circles
"""

import cv2
import numpy as np
from picamera2 import Picamera2
import time
import os
import argparse

class EyeDetector:
    def __init__(self, args):
        self.resolution = (args.width, args.height)
        
        # Initialize camera
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(
            main={"size": self.resolution},
            buffer_count=2
        ))
        
        # Iris detection parameters
        self.iris_min_radius = args.iris_min_radius
        self.iris_max_radius = args.iris_max_radius
        self.iris_dp = args.iris_dp
        self.iris_min_dist = args.iris_min_dist
        self.iris_param1 = args.iris_param1
        self.iris_param2 = args.iris_param2
        
        # Pupil detection parameters
        self.pupil_min_radius = args.pupil_min_radius
        self.pupil_max_radius = args.pupil_max_radius
        self.pupil_dp = args.pupil_dp
        self.pupil_min_dist = args.pupil_min_dist
        self.pupil_param1 = args.pupil_param1
        self.pupil_param2 = args.pupil_param2
        
        # Calibration circles
        self.show_calibration = True
        self.calibration_sizes = [10, 20, 30, 40, 50, 60, 70, 80]  # pixels
        self.calibration_color = (128, 128, 128)  # Gray color
        self.calibration_thickness = 1
        
        # Set up display
        os.environ["DISPLAY"] = ":0"
        cv2.namedWindow("Eye Detector", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Eye Detector", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
    def start(self):
        """Start camera and processing loop"""
        self.picam2.start()
        time.sleep(2)  # Wait for camera to initialize
        
        try:
            while True:
                # Capture frame
                frame = self.picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Process frame
                iris_info = self.detect_iris(frame)
                pupil_info = None
                
                if iris_info['detected']:
                    # If iris is detected, look for pupil inside it
                    pupil_info = self.detect_pupil(frame, iris_info['circle'])
                
                # Draw calibration circles if enabled
                if self.show_calibration:
                    self.draw_calibration_circles(frame)
                
                # Draw detections
                self.draw_detections(frame, iris_info, pupil_info)
                
                # Show frame
                cv2.imshow("Eye Detector", frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):  # Toggle calibration circles
                    self.show_calibration = not self.show_calibration
                elif key == ord('+'): # Increase circle sizes
                    self.calibration_sizes = [s + 5 for s in self.calibration_sizes]
                elif key == ord('-'): # Decrease circle sizes
                    self.calibration_sizes = [max(5, s - 5) for s in self.calibration_sizes]
                elif key == ord('1'):  # Decrease edge detection sensitivity
                    self.iris_param1 = max(1, self.iris_param1 - 5)
                    print(f"Iris edge detection (param1): {self.iris_param1}")
                elif key == ord('2'):  # Increase edge detection sensitivity
                    self.iris_param1 = min(255, self.iris_param1 + 5)
                    print(f"Iris edge detection (param1): {self.iris_param1}")
                elif key == ord('3'):  # Decrease circle detection threshold
                    self.iris_param2 = max(1, self.iris_param2 - 2)
                    print(f"Iris circle detection (param2): {self.iris_param2}")
                elif key == ord('4'):  # Increase circle detection threshold
                    self.iris_param2 = min(100, self.iris_param2 + 2)
                    print(f"Iris circle detection (param2): {self.iris_param2}")
                elif key == ord('5'):  # Decrease pupil edge detection
                    self.pupil_param1 = max(1, self.pupil_param1 - 5)
                    print(f"Pupil edge detection (param1): {self.pupil_param1}")
                elif key == ord('6'):  # Increase pupil edge detection
                    self.pupil_param1 = min(255, self.pupil_param1 + 5)
                    print(f"Pupil edge detection (param1): {self.pupil_param1}")
                elif key == ord('7'):  # Decrease pupil circle detection
                    self.pupil_param2 = max(1, self.pupil_param2 - 2)
                    print(f"Pupil circle detection (param2): {self.pupil_param2}")
                elif key == ord('8'):  # Increase pupil circle detection
                    self.pupil_param2 = min(100, self.pupil_param2 + 2)
                    print(f"Pupil circle detection (param2): {self.pupil_param2}")
                elif key == ord('d'):  # Display current parameters
                    print("\nCurrent Parameters:")
                    print(f"Iris: edge={self.iris_param1} circle={self.iris_param2}")
                    print(f"Pupil: edge={self.pupil_param1} circle={self.pupil_param2}")

        finally:
            self.picam2.stop()
            cv2.destroyAllWindows()
    
    def detect_iris(self, frame):
        """Detect iris in frame"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply preprocessing for iris detection
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        
        # Create info dictionary
        info = {
            'detected': False,
            'circle': None,
            'diameter_px': 0
        }
        
        # Detect iris using Hough transform
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=self.iris_dp,
            minDist=self.iris_min_dist,
            param1=self.iris_param1,
            param2=self.iris_param2,
            minRadius=self.iris_min_radius,
            maxRadius=self.iris_max_radius
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            # Get the most prominent circle
            circle = circles[0][0]
            info['circle'] = circle
            info['detected'] = True
            info['diameter_px'] = circle[2] * 2
        
        return info
    
    def detect_pupil(self, frame, iris_circle):
        """Detect pupil inside iris region"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Extract ROI around iris
        x, y, r = iris_circle
        roi_size = int(r * 1.5)  # Make ROI slightly larger than iris
        x1 = max(0, x - roi_size)
        y1 = max(0, y - roi_size)
        x2 = min(frame.shape[1], x + roi_size)
        y2 = min(frame.shape[0], y + roi_size)
        
        roi = gray[y1:y2, x1:x2]
        
        # Create info dictionary
        info = {
            'detected': False,
            'circle': None,
            'diameter_px': 0,
            'roi': (x1, y1, x2, y2)
        }
        
        if roi.size == 0:
            return info
        
        # Enhance contrast in ROI
        roi = cv2.equalizeHist(roi)
        
        # Apply threshold to isolate darker regions
        _, thresh = cv2.threshold(roi, 50, 255, cv2.THRESH_BINARY_INV)
        
        # Apply morphological operations
        kernel = np.ones((3,3), np.uint8)
        thresh = cv2.erode(thresh, kernel, iterations=1)
        thresh = cv2.dilate(thresh, kernel, iterations=1)
        
        # Detect pupil using Hough transform
        circles = cv2.HoughCircles(
            thresh,
            cv2.HOUGH_GRADIENT,
            dp=self.pupil_dp,
            minDist=self.pupil_min_dist,
            param1=self.pupil_param1,
            param2=self.pupil_param2,
            minRadius=self.pupil_min_radius,
            maxRadius=min(self.pupil_max_radius, int(r * 0.8))  # Pupil should be smaller than iris
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            # Get the most prominent circle
            circle = circles[0][0]
            # Adjust coordinates to original frame
            circle[0] += x1
            circle[1] += y1
            info['circle'] = circle
            info['detected'] = True
            info['diameter_px'] = circle[2] * 2
        
        return info
    
    def draw_calibration_circles(self, frame):
        """Draw calibration circles in the corner"""
        height, width = frame.shape[:2]
        margin = 10
        spacing = 5
        
        # Calculate starting position (top-right corner)
        x = width - margin - max(self.calibration_sizes)
        y = margin + max(self.calibration_sizes)
        
        # Draw circles
        for radius in self.calibration_sizes:
            # Draw circle
            cv2.circle(frame, (x, y), radius, self.calibration_color, self.calibration_thickness)
            # Add size label
            cv2.putText(frame, f"{radius*2}px", (x + radius + 5, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.calibration_color, 1)
            # Move down for next circle
            y += radius * 2 + spacing
            
        # Add instructions
        cv2.putText(frame, "C: Toggle calibration", (10, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.calibration_color, 1)
        cv2.putText(frame, "+/-: Adjust sizes", (10, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.calibration_color, 1)
    
    def draw_detections(self, frame, iris_info, pupil_info=None):
        """Draw iris and pupil detections"""
        # Add parameter info at the top
        param_text = [
            f"Iris: edge={self.iris_param1} circle={self.iris_param2}",
            f"Pupil: edge={self.pupil_param1} circle={self.pupil_param2}"
        ]
        for i, text in enumerate(param_text):
            cv2.putText(frame, text, (10, 70 + i*25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Add control instructions
        controls = [
            "1/2: Iris edge detection",
            "3/4: Iris circle detection",
            "5/6: Pupil edge detection",
            "7/8: Pupil circle detection",
            "D: Print parameters"
        ]
        for i, text in enumerate(controls):
            cv2.putText(frame, text, (frame.shape[1] - 250, 25 + i*20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)

        # Draw iris
        if iris_info['detected']:
            circle = iris_info['circle']
            # Draw the iris circle in blue
            cv2.circle(frame, (circle[0], circle[1]), circle[2], (255, 0, 0), 2)
            
            # Add iris diameter text
            text = f"Iris: {iris_info['diameter_px']}px"
            cv2.putText(frame, text, (10, frame.shape[0] - 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw pupil
        if pupil_info and pupil_info['detected']:
            circle = pupil_info['circle']
            # Draw the pupil circle in green
            cv2.circle(frame, (circle[0], circle[1]), circle[2], (0, 255, 0), 2)
            # Draw the center point in red
            cv2.circle(frame, (circle[0], circle[1]), 2, (0, 0, 255), 3)
            
            # Add pupil diameter text
            text = f"Pupil: {pupil_info['diameter_px']}px"
            cv2.putText(frame, text, (10, frame.shape[0] - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Calculate and display pupil/iris ratio
            if iris_info['detected']:
                ratio = (pupil_info['diameter_px'] / iris_info['diameter_px']) * 100
                ratio_text = f"Pupil/Iris Ratio: {ratio:.1f}%"
                cv2.putText(frame, ratio_text, (10, frame.shape[0] - 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

def parse_args():
    parser = argparse.ArgumentParser(description='Eye Detection Parameters')
    
    # Camera parameters
    parser.add_argument('--width', type=int, default=640, help='Camera width')
    parser.add_argument('--height', type=int, default=480, help='Camera height')
    
    # Iris detection parameters
    parser.add_argument('--iris-min-radius', type=int, default=50,
                       help='Minimum iris radius in pixels')
    parser.add_argument('--iris-max-radius', type=int, default=150,
                       help='Maximum iris radius in pixels')
    parser.add_argument('--iris-dp', type=float, default=1.2,
                       help='Accumulator resolution: 1.0 = full, 2.0 = half')
    parser.add_argument('--iris-min-dist', type=int, default=200,
                       help='Minimum distance between detected irises')
    parser.add_argument('--iris-param1', type=int, default=70,
                       help='Edge detection sensitivity (higher=more edges)')
    parser.add_argument('--iris-param2', type=int, default=30,
                       help='Circle detection threshold (lower=more circles)')
    
    # Pupil detection parameters
    parser.add_argument('--pupil-min-radius', type=int, default=10,
                       help='Minimum pupil radius in pixels')
    parser.add_argument('--pupil-max-radius', type=int, default=100,
                       help='Maximum pupil radius in pixels')
    parser.add_argument('--pupil-dp', type=float, default=1.2,
                       help='Accumulator resolution: 1.0 = full, 2.0 = half')
    parser.add_argument('--pupil-min-dist', type=int, default=50,
                       help='Minimum distance between detected pupils')
    parser.add_argument('--pupil-param1', type=int, default=50,
                       help='Edge detection sensitivity (higher=more edges)')
    parser.add_argument('--pupil-param2', type=int, default=25,
                       help='Circle detection threshold (lower=more circles)')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    detector = EyeDetector(args)
    
    try:
        detector.start()
    except KeyboardInterrupt:
        print("\nStopping eye detector...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 