#!/usr/bin/env python3

import os
import sys
import cv2
import numpy as np
from typing import Dict, List, Tuple
import argparse
from pathlib import Path
import cmd
import threading
import queue
import time

class PupilTunerShell(cmd.Cmd):
    intro = 'Welcome to pupil detector tuning shell. Type help or ? to list commands.\n'
    prompt = '(tune) '
    
    def __init__(self, tuner):
        super().__init__()
        self.tuner = tuner
        self.param_queue = queue.Queue()
        self.running = True
    
    def do_params(self, arg):
        'List all parameters and their current values'
        print("\nCurrent Parameters:")
        print("=" * 50)
        for param_name, value in self.tuner.params.items():
            info = self.tuner.PARAM_INFO[param_name]
            print(f"\n{param_name}:")
            print(f"  Value: {value}")
            print(f"  Range: {info['range']}")
            print(f"  Step: {info['step']}")
    
    def do_info(self, arg):
        'Show detailed information about a parameter: info param_name'
        param = arg.strip()
        if param in self.tuner.PARAM_INFO:
            info = self.tuner.PARAM_INFO[param]
            print(f"\n{param}:")
            print(f"  Description: {info['description']}")
            print(f"  Current value: {self.tuner.params[param]}")
            print(f"  Range: {info['range']}")
            print(f"  Step: {info['step']}")
        else:
            print(f"Unknown parameter: {param}")
    
    def do_set(self, arg):
        'Set parameter value: set param_name value'
        try:
            param, value = arg.split()
            value = float(value)
            if self.tuner.set_param(param, value):
                self.param_queue.put(('set', param, value))
                print(f"Set {param} to {value}")
        except ValueError:
            print("Usage: set param_name value")
    
    def do_inc(self, arg):
        'Increase parameter by one step: inc param_name'
        param = arg.strip()
        if param in self.tuner.PARAM_INFO:
            step = self.tuner.PARAM_INFO[param]['step']
            value = self.tuner.params[param] + step
            if self.tuner.set_param(param, value):
                self.param_queue.put(('set', param, value))
                print(f"Increased {param} to {value}")
        else:
            print(f"Unknown parameter: {param}")
    
    def do_dec(self, arg):
        'Decrease parameter by one step: dec param_name'
        param = arg.strip()
        if param in self.tuner.PARAM_INFO:
            step = self.tuner.PARAM_INFO[param]['step']
            value = self.tuner.params[param] - step
            if self.tuner.set_param(param, value):
                self.param_queue.put(('set', param, value))
                print(f"Decreased {param} to {value}")
        else:
            print(f"Unknown parameter: {param}")
    
    def do_save(self, arg):
        'Save current parameters to file: save filename'
        filename = arg.strip() or 'detection_params.txt'
        with open(filename, 'w') as f:
            for param_name, value in self.tuner.params.items():
                f.write(f"{param_name}: {value}\n")
        print(f"Parameters saved to {filename}")
    
    def do_load(self, arg):
        'Load parameters from file: load filename'
        filename = arg.strip()
        try:
            with open(filename) as f:
                for line in f:
                    param, value = line.strip().split(':')
                    param = param.strip()
                    value = float(value.strip())
                    if self.tuner.set_param(param, value):
                        self.param_queue.put(('set', param, value))
            print(f"Parameters loaded from {filename}")
        except FileNotFoundError:
            print(f"File not found: {filename}")
    
    def do_stats(self, arg):
        'Show current detection statistics'
        stats = self.tuner.get_current_stats()
        print("\nDetection Statistics:")
        print(f"  Frames processed: {stats['total_frames']}")
        if stats['total_frames'] > 0:
            print(f"  Iris detection rate: {stats['iris_detected']/stats['total_frames']*100:.1f}%")
            print(f"  Pupil detection rate: {stats['pupil_detected']/stats['total_frames']*100:.1f}%")
        if stats['pupil_sizes']:
            print(f"  Mean pupil size: {np.mean(stats['pupil_sizes']):.1f} ± {np.std(stats['pupil_sizes']):.1f} pixels")
    
    def do_quit(self, arg):
        'Exit the tuner'
        self.running = False
        self.param_queue.put(('quit', None, None))
        return True
    
    def do_EOF(self, arg):
        'Exit on Ctrl-D'
        return self.do_quit(arg)

class InteractivePupilTuner:
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

    def __init__(self, video_files: List[str]):
        self.video_files = video_files
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
        
        # Statistics
        self.stats = {
            'total_frames': 0,
            'iris_detected': 0,
            'pupil_detected': 0,
            'pupil_sizes': []
        }
        
        # Set up display
        os.environ["DISPLAY"] = ":0"
        cv2.namedWindow("Detection", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    def get_current_stats(self):
        """Get copy of current statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset detection statistics"""
        self.stats = {
            'total_frames': 0,
            'iris_detected': 0,
            'pupil_detected': 0,
            'pupil_sizes': []
        }
    
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
        
        # Update statistics
        self.stats['total_frames'] += 1
        if measurements['iris_detected']:
            self.stats['iris_detected'] += 1
        if measurements['pupil_detected']:
            self.stats['pupil_detected'] += 1
            self.stats['pupil_sizes'].append(measurements['pupil_radius'])
            # Keep only last 100 measurements for rolling average
            if len(self.stats['pupil_sizes']) > 100:
                self.stats['pupil_sizes'].pop(0)
        
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
                        
                        cv2.drawContours(frame, [pupil_contour], -1, (0, 255, 255), 1)
                        cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
        
        # Show the threshold image in a corner
        h, w = frame.shape[:2]
        small_thresh = cv2.resize(thresh, (w//4, h//4))
        frame[0:h//4, 0:w//4] = cv2.cvtColor(small_thresh, cv2.COLOR_GRAY2BGR)
        
        # Add parameter overlay
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
        
        return frame, measurements
    
    def run_with_shell(self):
        """Run video processing with interactive shell"""
        # Start command shell in a separate thread
        shell = PupilTunerShell(self)
        shell_thread = threading.Thread(target=shell.cmdloop)
        shell_thread.daemon = True
        shell_thread.start()
        
        try:
            while shell.running:
                # Open video if not already open
                if self.cap is None:
                    self.cap = cv2.VideoCapture(self.video_files[self.current_video_idx])
                    self.reset_stats()
                
                # Read frame
                ret, frame = self.cap.read()
                
                # If video ended, move to next video
                if not ret:
                    self.cap.release()
                    self.cap = None
                    self.current_video_idx = (self.current_video_idx + 1) % len(self.video_files)
                    continue
                
                # Process frame
                viz_frame, _ = self.process_frame(frame)
                
                # Display frame
                cv2.imshow("Detection", viz_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                # Check for parameter updates
                try:
                    cmd, param, value = shell.param_queue.get_nowait()
                    if cmd == 'quit':
                        break
                except queue.Empty:
                    pass
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
        
        finally:
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description="Interactive pupil detection parameter tuning")
    parser.add_argument("videos", nargs='+', help="Video files to process")
    args = parser.parse_args()
    
    tuner = InteractivePupilTuner(args.videos)
    tuner.run_with_shell()

if __name__ == "__main__":
    main() 