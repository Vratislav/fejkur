#!/usr/bin/env python3

import os
import sys
import cv2
import numpy as np
from typing import Dict, List, Tuple
import argparse
from pathlib import Path

class PupilTuner:
    # Parameter descriptions and reasonable ranges
    PARAM_INFO = {
        'clahe_clip': {
            'description': 'Contrast Limited Adaptive Histogram Equalization clip limit. Higher values increase contrast but may amplify noise.',
            'range': (0.5, 5.0),
            'step': 0.5
        },
        'clahe_grid': {
            'description': 'CLAHE grid size. Smaller values adapt to more local features.',
            'range': (2, 16),
            'step': 2
        },
        'bilateral_d': {
            'description': 'Bilateral filter diameter. Larger values smooth more but are slower.',
            'range': (5, 20),
            'step': 1
        },
        'bilateral_sigma': {
            'description': 'Bilateral filter sigma. Controls how much smoothing is applied.',
            'range': (25, 150),
            'step': 5
        },
        'thresh_block': {
            'description': 'Adaptive threshold block size. Must be odd. Larger values use more surrounding pixels.',
            'range': (3, 21),
            'step': 2
        },
        'thresh_c': {
            'description': 'Adaptive threshold constant. Higher values make thresholding more aggressive.',
            'range': (-10, 10),
            'step': 1
        },
        'min_area': {
            'description': 'Minimum pupil contour area in pixels. Filters out small noise.',
            'range': (50, 500),
            'step': 10
        },
        'min_radius': {
            'description': 'Minimum pupil radius in pixels.',
            'range': (3, 20),
            'step': 1
        },
        'iris_min_dist': {
            'description': 'Minimum distance between detected iris circles.',
            'range': (100, 300),
            'step': 10
        },
        'iris_param1': {
            'description': 'First Hough Circle parameter. Edge detection sensitivity.',
            'range': (10, 100),
            'step': 5
        },
        'iris_param2': {
            'description': 'Second Hough Circle parameter. Circle detection sensitivity.',
            'range': (10, 100),
            'step': 5
        },
        'iris_min_radius': {
            'description': 'Minimum iris radius in pixels.',
            'range': (30, 100),
            'step': 5
        },
        'iris_max_radius': {
            'description': 'Maximum iris radius in pixels.',
            'range': (100, 200),
            'step': 5
        }
    }

    def __init__(self, video_files: List[str], display: bool = True):
        self.video_files = video_files
        self.display = display
        self.current_video_idx = 0
        self.cap = None
        
        # Detection parameters with defaults
        self.params = {
            'clahe_clip': 2.0,
            'clahe_grid': 8,
            'bilateral_d': 10,
            'bilateral_sigma': 75,
            'thresh_block': 11,
            'thresh_c': 2,
            'min_area': 100,
            'min_radius': 5,
            'iris_min_dist': 200,
            'iris_param1': 50,
            'iris_param2': 30,
            'iris_min_radius': 50,
            'iris_max_radius': 150
        }
        
        if display:
            os.environ["DISPLAY"] = ":0"
            cv2.namedWindow("Detection", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def print_param_help(self):
        """Print detailed help about parameters"""
        print("\nParameter Information:")
        print("=" * 80)
        for param_name, info in self.PARAM_INFO.items():
            print(f"\n{param_name}:")
            print(f"  Description: {info['description']}")
            print(f"  Range: {info['range']}")
            print(f"  Step size: {info['step']}")
            print(f"  Current value: {self.params[param_name]}")
        print("\n" + "=" * 80)

    def set_param(self, param_name: str, value: float) -> bool:
        """Set parameter value with validation"""
        if param_name not in self.params:
            print(f"Error: Unknown parameter '{param_name}'")
            return False
        
        info = self.PARAM_INFO[param_name]
        min_val, max_val = info['range']
        
        if value < min_val or value > max_val:
            print(f"Warning: Value {value} for {param_name} is outside recommended range {info['range']}")
        
        # Special handling for parameters that must be integers
        if param_name in ['clahe_grid', 'bilateral_d', 'thresh_block', 'min_area', 'min_radius',
                         'iris_min_dist', 'iris_min_radius', 'iris_max_radius']:
            value = int(value)
            
        # Ensure thresh_block is odd
        if param_name == 'thresh_block':
            value = value if value % 2 == 1 else value + 1
        
        self.params[param_name] = value
        return True

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Process a single frame and return visualization and measurements"""
        # Preprocess
        thresh, gray = self.preprocess_eye_image(frame)
        
        # Detect pupil
        viz_frame, measurements = self.detect_pupil(frame.copy(), thresh, gray)
        
        return viz_frame, measurements

    def preprocess_eye_image(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess image for better pupil detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(
            clipLimit=self.params['clahe_clip'],
            tileGridSize=(self.params['clahe_grid'], self.params['clahe_grid'])
        )
        gray = clahe.apply(gray)
        
        gray = cv2.bilateralFilter(
            gray,
            self.params['bilateral_d'],
            self.params['bilateral_sigma'],
            self.params['bilateral_sigma']
        )
        
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self.params['thresh_block'],
            self.params['thresh_c']
        )
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return thresh, gray

    def detect_pupil(self, frame: np.ndarray, thresh: np.ndarray, gray: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Detect pupil and return visualization frame and measurements"""
        measurements = {'iris_detected': False, 'pupil_detected': False}
        
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
        
        if iris_circles is not None:
            measurements['iris_detected'] = True
            iris = np.uint16(np.around(iris_circles[0][0]))
            ix, iy, ir = iris
            
            if self.display:
                cv2.circle(frame, (ix, iy), ir, (255, 0, 0), 2)
            
            # Create ROI mask for iris region
            mask = np.zeros_like(gray)
            cv2.circle(mask, (ix, iy), ir, 255, -1)
            
            # Apply mask to thresholded image
            masked_thresh = cv2.bitwise_and(thresh, thresh, mask=mask)
            
            # Find contours
            contours, _ = cv2.findContours(masked_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                pupil_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(pupil_contour)
                
                if area >= self.params['min_area']:
                    (x, y), radius = cv2.minEnclosingCircle(pupil_contour)
                    
                    if radius >= self.params['min_radius'] and radius <= ir * 0.7:
                        measurements['pupil_detected'] = True
                        measurements['pupil_x'] = int(x)
                        measurements['pupil_y'] = int(y)
                        measurements['pupil_radius'] = int(radius)
                        measurements['pupil_area'] = area
                        
                        if self.display:
                            cv2.drawContours(frame, [pupil_contour], -1, (0, 255, 255), 1)
                            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
        
        if self.display:
            # Show the threshold image in a corner
            h, w = frame.shape[:2]
            small_thresh = cv2.resize(thresh, (w//4, h//4))
            frame[0:h//4, 0:w//4] = cv2.cvtColor(small_thresh, cv2.COLOR_GRAY2BGR)
        
        return frame, measurements

    def process_video(self, video_path: str, frames: int = None) -> Dict:
        """Process video and return detection statistics"""
        cap = cv2.VideoCapture(video_path)
        stats = {
            'total_frames': 0,
            'iris_detected': 0,
            'pupil_detected': 0,
            'pupil_sizes': []
        }
        
        try:
            while True:
                if frames is not None and stats['total_frames'] >= frames:
                    break
                    
                ret, frame = cap.read()
                if not ret:
                    break
                
                viz_frame, measurements = self.process_frame(frame)
                
                stats['total_frames'] += 1
                if measurements['iris_detected']:
                    stats['iris_detected'] += 1
                if measurements['pupil_detected']:
                    stats['pupil_detected'] += 1
                    stats['pupil_sizes'].append(measurements['pupil_radius'])
                
                if self.display:
                    cv2.imshow("Detection", viz_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        
        finally:
            cap.release()
        
        if stats['pupil_sizes']:
            stats['mean_pupil_size'] = np.mean(stats['pupil_sizes'])
            stats['std_pupil_size'] = np.std(stats['pupil_sizes'])
        
        return stats

    def cleanup(self):
        """Clean up resources"""
        if self.display:
            cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description="Tune pupil detection parameters")
    parser.add_argument("videos", nargs='+', help="Video files to process")
    parser.add_argument("--no-display", action="store_true", help="Run without display")
    parser.add_argument("--frames", type=int, help="Number of frames to process per video")
    parser.add_argument("--param", nargs=2, action='append', metavar=('PARAM', 'VALUE'),
                      help="Set parameter value (can be used multiple times)")
    parser.add_argument("--list-params", action="store_true", help="List all parameters and their descriptions")
    parser.add_argument("--save", help="Save parameters to file")
    parser.add_argument("--load", help="Load parameters from file")
    args = parser.parse_args()
    
    tuner = PupilTuner(args.videos, display=not args.no_display)
    
    if args.list_params:
        tuner.print_param_help()
        return
    
    if args.load:
        with open(args.load) as f:
            for line in f:
                param, value = line.strip().split(':')
                tuner.set_param(param.strip(), float(value.strip()))
    
    if args.param:
        for param_name, value in args.param:
            tuner.set_param(param_name, float(value))
    
    print("\nProcessing videos with current parameters:")
    for param_name, value in tuner.params.items():
        print(f"{param_name}: {value}")
    
    for video in args.videos:
        print(f"\nProcessing {video}...")
        stats = tuner.process_video(video, args.frames)
        print(f"Results:")
        print(f"  Total frames: {stats['total_frames']}")
        print(f"  Iris detection rate: {stats['iris_detected']/stats['total_frames']*100:.1f}%")
        print(f"  Pupil detection rate: {stats['pupil_detected']/stats['total_frames']*100:.1f}%")
        if 'mean_pupil_size' in stats:
            print(f"  Mean pupil size: {stats['mean_pupil_size']:.1f} ± {stats['std_pupil_size']:.1f} pixels")
    
    if args.save:
        with open(args.save, 'w') as f:
            for param_name, value in tuner.params.items():
                f.write(f"{param_name}: {value}\n")
        print(f"\nParameters saved to {args.save}")
    
    tuner.cleanup()

if __name__ == "__main__":
    main() 