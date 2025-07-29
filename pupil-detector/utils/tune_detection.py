#!/usr/bin/env python3

import os
import sys
import cv2
import numpy as np
from typing import Dict, List, Tuple
import argparse
from pathlib import Path

class PupilTuner:
    def __init__(self, video_files: List[str]):
        self.video_files = video_files
        self.current_video_idx = 0
        self.cap = None
        
        # Detection parameters with defaults
        self.params = {
            'clahe_clip': 2.0,        # CLAHE clip limit
            'clahe_grid': 8,          # CLAHE grid size
            'bilateral_d': 10,        # Bilateral filter diameter
            'bilateral_sigma': 75,    # Bilateral filter sigma
            'thresh_block': 11,       # Adaptive threshold block size
            'thresh_c': 2,           # Adaptive threshold C value
            'min_area': 100,         # Minimum pupil contour area
            'min_radius': 5,         # Minimum pupil radius
            'iris_min_dist': 200,    # Iris detection minimum distance
            'iris_param1': 50,       # Iris detection param1 (edge threshold)
            'iris_param2': 30,       # Iris detection param2 (circle threshold)
            'iris_min_radius': 50,   # Minimum iris radius
            'iris_max_radius': 150,  # Maximum iris radius
        }
        
        # Current parameter being adjusted
        self.current_param = list(self.params.keys())[0]
        self.param_step = 1
        
        # Set display for Raspberry Pi
        os.environ["DISPLAY"] = ":0"
        cv2.namedWindow("Tuning", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Tuning", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    def preprocess_eye_image(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess image for better pupil detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(
            clipLimit=self.params['clahe_clip'],
            tileGridSize=(self.params['clahe_grid'], self.params['clahe_grid'])
        )
        gray = clahe.apply(gray)
        
        # Bilateral filter
        gray = cv2.bilateralFilter(
            gray,
            self.params['bilateral_d'],
            self.params['bilateral_sigma'],
            self.params['bilateral_sigma']
        )
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self.params['thresh_block'],
            self.params['thresh_c']
        )
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return thresh, gray
    
    def detect_pupil(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Detect pupil and return visualization frame and measurements"""
        # Make a copy for visualization
        viz_frame = frame.copy()
        
        # Preprocess the image
        thresh, gray = self.preprocess_eye_image(frame)
        
        # First detect iris
        iris_circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=self.params['iris_min_dist'],
            param1=self.params['iris_param1'],
            param2=self.params['iris_param2'],
            minRadius=self.params['iris_min_radius'],
            maxRadius=self.params['iris_max_radius']
        )
        
        measurements = {'iris_detected': False, 'pupil_detected': False}
        
        if iris_circles is not None:
            measurements['iris_detected'] = True
            iris = np.uint16(np.around(iris_circles[0][0]))
            ix, iy, ir = iris
            
            # Draw iris circle
            cv2.circle(viz_frame, (ix, iy), ir, (255, 0, 0), 2)
            
            # Create ROI mask for iris region
            mask = np.zeros_like(gray)
            cv2.circle(mask, (ix, iy), ir, 255, -1)
            
            # Apply mask to thresholded image
            masked_thresh = cv2.bitwise_and(thresh, thresh, mask=mask)
            
            # Find contours
            contours, _ = cv2.findContours(masked_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find the largest contour
                pupil_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(pupil_contour)
                
                if area >= self.params['min_area']:
                    # Fit circle to the contour
                    (x, y), radius = cv2.minEnclosingCircle(pupil_contour)
                    
                    if radius >= self.params['min_radius'] and radius <= ir * 0.7:
                        measurements['pupil_detected'] = True
                        measurements['pupil_x'] = int(x)
                        measurements['pupil_y'] = int(y)
                        measurements['pupil_radius'] = int(radius)
                        measurements['pupil_area'] = area
                        
                        # Draw pupil contour and circle
                        cv2.drawContours(viz_frame, [pupil_contour], -1, (0, 255, 255), 1)
                        cv2.circle(viz_frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
        
        # Show the threshold image in a corner
        h, w = frame.shape[:2]
        small_thresh = cv2.resize(thresh, (w//4, h//4))
        viz_frame[0:h//4, 0:w//4] = cv2.cvtColor(small_thresh, cv2.COLOR_GRAY2BGR)
        
        return viz_frame, measurements
    
    def draw_parameter_overlay(self, frame: np.ndarray, measurements: Dict):
        """Draw parameter values and controls on frame"""
        h, w = frame.shape[:2]
        overlay = np.zeros((h, w//4, 3), dtype=np.uint8)
        
        # Draw parameters
        y_pos = 30
        line_height = 25
        
        # Draw detection status
        if measurements['iris_detected']:
            cv2.putText(frame, "Iris: Detected", (w-200, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        else:
            cv2.putText(frame, "Iris: Not Detected", (w-200, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        y_pos += line_height
        
        if measurements['pupil_detected']:
            cv2.putText(frame, f"Pupil: r={measurements['pupil_radius']}", (w-200, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Pupil: Not Detected", (w-200, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        y_pos += line_height * 2
        
        # Draw all parameters
        for param_name, value in self.params.items():
            color = (0, 255, 0) if param_name == self.current_param else (200, 200, 200)
            cv2.putText(frame, f"{param_name}: {value}", (w-200, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_pos += line_height
        
        # Draw controls help
        y_pos = h - 120
        cv2.putText(frame, "Controls:", (w-200, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_pos += line_height
        cv2.putText(frame, "UP/DOWN: Select param", (w-200, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y_pos += line_height
        cv2.putText(frame, "LEFT/RIGHT: Adjust value", (w-200, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y_pos += line_height
        cv2.putText(frame, "N: Next video, S: Save", (w-200, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Show current video name
        video_name = Path(self.video_files[self.current_video_idx]).name
        cv2.putText(frame, video_name, (10, h - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def handle_keyboard(self) -> bool:
        """Handle keyboard input, return False if should quit"""
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            return False
        elif key == ord('n'):
            # Skip to next video
            self.cap.release()
            self.cap = None
            self.current_video_idx = (self.current_video_idx + 1) % len(self.video_files)
        elif key == ord('s'):
            # Save current parameters
            param_file = 'detection_params.txt'
            with open(param_file, 'w') as f:
                for param_name, value in self.params.items():
                    f.write(f'{param_name}: {value}\n')
            print(f"Parameters saved to {param_file}")
        elif key == 82:  # Up arrow
            # Select previous parameter
            param_keys = list(self.params.keys())
            current_idx = param_keys.index(self.current_param)
            self.current_param = param_keys[(current_idx - 1) % len(param_keys)]
        elif key == 84:  # Down arrow
            # Select next parameter
            param_keys = list(self.params.keys())
            current_idx = param_keys.index(self.current_param)
            self.current_param = param_keys[(current_idx + 1) % len(param_keys)]
        elif key == 81:  # Left arrow
            # Decrease current parameter
            self.params[self.current_param] = max(0, self.params[self.current_param] - self.param_step)
        elif key == 83:  # Right arrow
            # Increase current parameter
            self.params[self.current_param] += self.param_step
        
        return True
    
    def run(self):
        """Main loop for video processing and parameter tuning"""
        while True:
            # Open video if not already open
            if self.cap is None:
                self.cap = cv2.VideoCapture(self.video_files[self.current_video_idx])
            
            # Read frame
            ret, frame = self.cap.read()
            
            # If video ended, move to next video
            if not ret:
                self.cap.release()
                self.cap = None
                self.current_video_idx = (self.current_video_idx + 1) % len(self.video_files)
                continue
            
            # Process frame
            viz_frame, measurements = self.detect_pupil(frame)
            
            # Add parameter overlay
            self.draw_parameter_overlay(viz_frame, measurements)
            
            # Display frame
            cv2.imshow("Tuning", viz_frame)
            
            # Handle keyboard input
            if not self.handle_keyboard():
                break
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description="Tune pupil detection parameters")
    parser.add_argument("videos", nargs='+', help="Video files to process")
    args = parser.parse_args()
    
    tuner = PupilTuner(args.videos)
    try:
        tuner.run()
    finally:
        tuner.cleanup()

if __name__ == "__main__":
    main() 