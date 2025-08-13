#!/usr/bin/env python3

import os
import cv2
import numpy as np
import glob
from typing import Tuple, Optional, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time

# Import the actual JEOresearch functions
import sys
sys.path.append('./EyeTracker')
from OrloskyPupilDetectorRaspberryPi import (
    crop_to_aspect_ratio, apply_binary_threshold, get_darkest_area,
    mask_outside_square, filter_contours_by_area_and_return_largest
)

class RealJEOPupilDetectionTuner:
    def __init__(self, root):
        self.root = root
        self.root.title("Real JEO EyeTracker Tuner")
        self.root.geometry("800x600")
        
        # Detection parameters based on actual JEOresearch code
        self.params = {
            'ignore_bounds': 20,        # Ignore bounds for darkest area search
            'image_skip_size': 20,      # Skip size for darkest area search
            'search_area': 20,          # Search area size
            'internal_skip_size': 10,   # Internal skip size
            'added_threshold': 15,      # Added threshold for binary thresholding
            'mask_size': 250,           # Size of mask around darkest point
            'pixel_thresh': 1000,       # Minimum contour area
            'ratio_thresh': 3,          # Maximum length/width ratio
            'kernel_size': 5,           # Morphological kernel size
            'dilation_iterations': 2,   # Number of dilation iterations
            'center_weight': 0.4,       # Weight for center proximity
            'size_weight': 0.3,         # Weight for size preference
            'darkness_weight': 0.3      # Weight for darkness
        }
        
        # State variables
        self.recordings = []
        self.current_recording_idx = 0
        self.current_frame_idx = 0
        self.frames = []
        self.playing = False
        self.play_speed = 100  # ms between frames
        self.current_frame = None
        
        self.setup_ui()
        self.load_recordings()
        
        # Create OpenCV window for display
        cv2.namedWindow("Real JEO Pupil Detection", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Real JEO Pupil Detection", 640, 480)
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.setup_controls(main_frame)
        
    def setup_controls(self, parent):
        """Setup control panel with sliders"""
        # Recording selection
        ttk.Label(parent, text="Recording Selection", font=('Arial', 12, 'bold')).pack(pady=(0, 5))
        
        self.recording_var = tk.StringVar()
        self.recording_combo = ttk.Combobox(parent, textvariable=self.recording_var, width=50)
        self.recording_combo.pack(pady=(0, 10))
        self.recording_combo.bind('<<ComboboxSelected>>', self.on_recording_changed)
        
        # Playback controls
        ttk.Label(parent, text="Playback Controls", font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        
        playback_frame = ttk.Frame(parent)
        playback_frame.pack(pady=(0, 10))
        
        self.play_button = ttk.Button(playback_frame, text="Play", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(playback_frame, text="Reset", command=self.reset_playback).pack(side=tk.LEFT, padx=5)
        ttk.Button(playback_frame, text="Refresh", command=self.load_recordings).pack(side=tk.LEFT, padx=5)
        ttk.Button(playback_frame, text="Show Frame", command=self.display_current_frame).pack(side=tk.LEFT, padx=5)
        
        # Frame navigation
        ttk.Label(parent, text="Frame:").pack()
        self.frame_var = tk.IntVar()
        self.frame_scale = ttk.Scale(parent, from_=0, to=100, variable=self.frame_var, 
                                   orient=tk.HORIZONTAL, command=self.on_frame_changed)
        self.frame_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Play speed
        ttk.Label(parent, text="Play Speed (ms):").pack()
        self.speed_var = tk.IntVar(value=self.play_speed)
        ttk.Scale(parent, from_=50, to=500, variable=self.speed_var, 
                 orient=tk.HORIZONTAL, command=self.on_speed_changed).pack(fill=tk.X, pady=(0, 10))
        
        # Detection parameters in a grid
        ttk.Label(parent, text="Real JEO Detection Parameters", font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        
        params_frame = ttk.Frame(parent)
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create sliders for each parameter in a grid
        self.param_vars = {}
        param_configs = [
            ('ignore_bounds', 'Ignore Bounds', 10, 50, 5),
            ('image_skip_size', 'Image Skip Size', 10, 50, 5),
            ('search_area', 'Search Area', 10, 50, 5),
            ('internal_skip_size', 'Internal Skip', 5, 20, 1),
            ('added_threshold', 'Added Threshold', 5, 30, 1),
            ('mask_size', 'Mask Size', 100, 400, 20),
            ('pixel_thresh', 'Pixel Threshold', 500, 2000, 100),
            ('ratio_thresh', 'Ratio Threshold', 2, 5, 0.5),
            ('kernel_size', 'Kernel Size', 3, 9, 1),
            ('dilation_iterations', 'Dilation Iter', 1, 5, 1),
            ('center_weight', 'Center Weight', 0.1, 1.0, 0.1),
            ('size_weight', 'Size Weight', 0.1, 1.0, 0.1),
            ('darkness_weight', 'Darkness Weight', 0.1, 1.0, 0.1)
        ]
        
        # Create parameters in 3 columns
        for i, (param, label, min_val, max_val, step) in enumerate(param_configs):
            row = i // 3
            col = i % 3
            self.create_parameter_slider(params_frame, param, label, min_val, max_val, step, row, col)
        
        # Results display
        ttk.Label(parent, text="Detection Results", font=('Arial', 12, 'bold')).pack(pady=(20, 5))
        
        self.results_text = tk.Text(parent, height=8, width=80)
        self.results_text.pack(pady=(0, 10))
        
        # Info display
        self.info_text = tk.Text(parent, height=4, width=80)
        self.info_text.pack(fill=tk.X, pady=10)
        
        # Export button
        ttk.Button(parent, text="Export Parameters", command=self.export_parameters).pack(pady=10)
        
    def create_parameter_slider(self, parent, param, label, min_val, max_val, step, row, col):
        """Create a parameter slider in grid layout"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        
        ttk.Label(frame, text=f"{label}:").pack(anchor=tk.W)
        
        var = tk.DoubleVar(value=self.params[param])
        self.param_vars[param] = var
        
        slider = ttk.Scale(frame, from_=min_val, to=max_val, variable=var,
                          orient=tk.HORIZONTAL, command=lambda v, p=param: self.on_param_changed(p, v))
        slider.pack(fill=tk.X)
        
        # Value label
        value_label = ttk.Label(frame, text=f"{self.params[param]}")
        value_label.pack(anchor=tk.W)
        
        # Store reference to update label
        setattr(self, f"{param}_label", value_label)
        
        # Configure column weights
        parent.columnconfigure(col, weight=1)
        
    def load_recordings(self):
        """Load available recordings"""
        # Try multiple possible locations
        possible_dirs = [
            "./recordings",
            "/home/fejkur/recordings", 
            ".",
            os.path.expanduser("~/recordings")
        ]
        
        recordings_dir = None
        for dir_path in possible_dirs:
            if os.path.exists(dir_path):
                recordings_dir = dir_path
                break
        
        if not recordings_dir:
            print("No recordings directory found")
            return
            
        # Look for test condition recordings
        pattern = os.path.join(recordings_dir, "test_conditions_*")
        recording_dirs = glob.glob(pattern)
        
        self.recordings = []
        for dir_path in recording_dirs:
            if os.path.isdir(dir_path):
                # Check if it has frame files
                frame_files = glob.glob(os.path.join(dir_path, "frame_*.jpg"))
                if frame_files:
                    self.recordings.append({
                        'name': os.path.basename(dir_path),
                        'path': dir_path,
                        'frames': sorted(frame_files)
                    })
        
        # Update combo box
        recording_names = [rec['name'] for rec in self.recordings]
        self.recording_combo['values'] = recording_names
        
        if recording_names:
            self.recording_combo.set(recording_names[0])
            self.load_current_recording()
        
        print(f"Loaded {len(self.recordings)} recordings from {recordings_dir}")
        
    def load_current_recording(self):
        """Load the currently selected recording"""
        if not self.recordings:
            return
            
        recording = self.recordings[self.current_recording_idx]
        self.frames = recording['frames']
        
        # Update frame scale
        self.frame_scale.configure(to=len(self.frames) - 1)
        self.frame_var.set(0)
        self.current_frame_idx = 0
        
        # Load first frame
        self.display_current_frame()
        
        print(f"Loaded recording: {recording['name']} ({len(self.frames)} frames)")
        
    def on_recording_changed(self, event=None):
        """Handle recording selection change"""
        selected = self.recording_var.get()
        for i, rec in enumerate(self.recordings):
            if rec['name'] == selected:
                self.current_recording_idx = i
                break
        
        self.playing = False
        self.play_button.config(text="Play")
        self.load_current_recording()
        
    def on_frame_changed(self, value):
        """Handle frame slider change"""
        self.current_frame_idx = int(float(value))
        if not self.playing:
            self.display_current_frame()
            
    def on_speed_changed(self, value):
        """Handle play speed change"""
        self.play_speed = int(float(value))
        
    def on_param_changed(self, param, value):
        """Handle parameter slider change"""
        if param in ['ignore_bounds', 'image_skip_size', 'search_area', 'internal_skip_size', 
                    'added_threshold', 'mask_size', 'pixel_thresh', 'kernel_size', 'dilation_iterations']:
            # Ensure integer values for these parameters
            self.params[param] = int(float(value))
        else:
            self.params[param] = float(value)
        
        # Update value label
        label = getattr(self, f"{param}_label", None)
        if label:
            label.config(text=f"{self.params[param]:.3f}")
        
        # Update display if not playing
        if not self.playing:
            self.display_current_frame()
            
    def detect_pupil_real_jeo(self, frame):
        """Real JEOresearch EyeTracker pupil detection"""
        # Crop to aspect ratio
        frame = crop_to_aspect_ratio(frame)
        
        # Get darkest area with custom parameters
        darkest_point = self.get_darkest_area_custom(frame)
        
        if darkest_point is None:
            return [], None
        
        # Convert to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Get darkest pixel value
        darkest_pixel_value = gray_frame[darkest_point[1], darkest_point[0]]
        
        # Apply binary threshold with custom added threshold
        thresholded_image = apply_binary_threshold(gray_frame, darkest_pixel_value, self.params['added_threshold'])
        
        # Mask outside square with custom size
        thresholded_image = mask_outside_square(thresholded_image, darkest_point, self.params['mask_size'])
        
        # Process with custom parameters
        detected_pupils = self.process_frames_custom(thresholded_image, frame, gray_frame, darkest_point)
        
        return detected_pupils, thresholded_image
        
    def get_darkest_area_custom(self, image):
        """Custom version of get_darkest_area with adjustable parameters"""
        ignore_bounds = int(self.params['ignore_bounds'])
        image_skip_size = int(self.params['image_skip_size'])
        search_area = int(self.params['search_area'])
        internal_skip_size = int(self.params['internal_skip_size'])
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        min_sum = float('inf')
        darkest_point = None

        for y in range(ignore_bounds, gray.shape[0] - ignore_bounds, image_skip_size):
            for x in range(ignore_bounds, gray.shape[1] - ignore_bounds, image_skip_size):
                current_sum = 0
                num_pixels = 0
                for dy in range(0, search_area, internal_skip_size):
                    if y + dy >= gray.shape[0]:
                        break
                    for dx in range(0, search_area, internal_skip_size):
                        if x + dx >= gray.shape[1]:
                            break
                        current_sum += gray[y + dy][x + dx]
                        num_pixels += 1

                if current_sum < min_sum and num_pixels > 0:
                    min_sum = current_sum
                    darkest_point = (x + search_area // 2, y + search_area // 2)

        return darkest_point
        
    def process_frames_custom(self, thresholded_image, frame, gray_frame, darkest_point):
        """Custom version of process_frames with adjustable parameters"""
        kernel_size = int(self.params['kernel_size'])
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        dilation_iterations = int(self.params['dilation_iterations'])
        
        # Dilate the thresholded image
        dilated_image = cv2.dilate(thresholded_image, kernel, iterations=dilation_iterations)
        
        # Find contours
        contours, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours with custom parameters
        pixel_thresh = int(self.params['pixel_thresh'])
        ratio_thresh = self.params['ratio_thresh']
        reduced_contours = filter_contours_by_area_and_return_largest(contours, pixel_thresh, ratio_thresh)
        
        detected_pupils = []
        
        if len(reduced_contours) > 0 and len(reduced_contours[0]) > 5:
            try:
                ellipse = cv2.fitEllipse(reduced_contours[0])
                (x, y), (major_axis, minor_axis), angle = ellipse
                
                # Calculate scores
                height, width = frame.shape[:2]
                center_x, center_y = width // 2, height // 2
                
                # Distance from center
                distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                center_score = 1.0 - (distance_from_center / (min(width, height) / 2))
                
                # Size preference
                area = np.pi * (major_axis / 2) * (minor_axis / 2)
                size_score = 1.0 - abs(area - 1000) / 1000  # Prefer medium size
                
                # Darkness score
                mask_roi = np.zeros(gray_frame.shape, dtype=np.uint8)
                cv2.fillPoly(mask_roi, [reduced_contours[0]], 255)
                mean_intensity = cv2.mean(gray_frame, mask=mask_roi)[0]
                darkness_score = 1.0 - (mean_intensity / 255.0)
                
                # Combined score
                total_score = (center_score * self.params['center_weight'] + 
                             size_score * self.params['size_weight'] + 
                             darkness_score * self.params['darkness_weight'])
                
                detected_pupils.append({
                    'x': int(x), 'y': int(y),
                    'major_axis': major_axis, 'minor_axis': minor_axis,
                    'angle': angle, 'area': area,
                    'center_score': center_score,
                    'size_score': size_score,
                    'darkness_score': darkness_score,
                    'total_score': total_score,
                    'distance': distance_from_center,
                    'ellipse': ellipse
                })
                
            except:
                pass  # Skip if ellipse fitting fails
        
        # Sort by total score
        detected_pupils.sort(key=lambda p: p['total_score'], reverse=True)
        
        return detected_pupils
        
    def display_current_frame(self):
        """Display current frame with detection overlay"""
        if not self.frames or self.current_frame_idx >= len(self.frames):
            return
            
        # Load frame
        frame_path = self.frames[self.current_frame_idx]
        frame = cv2.imread(frame_path)
        if frame is None:
            return
            
        # Detect pupils using real JEO algorithm
        detected_pupils, thresholded_image = self.detect_pupil_real_jeo(frame)
        
        # Create display frame
        display_frame = frame.copy()
        
        # Get frame dimensions for calculations
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # Draw detected pupils
        for i, pupil in enumerate(detected_pupils):
            color = (0, 255, 0) if i == 0 else (0, 255, 255)  # Best in green, others in yellow
            
            # Draw ellipse
            cv2.ellipse(display_frame, pupil['ellipse'], color, 2)
            cv2.circle(display_frame, (pupil['x'], pupil['y']), 2, color, -1)
            
            # Add score text
            cv2.putText(display_frame, f"{pupil['total_score']:.2f}", 
                       (pupil['x'] + int(pupil['major_axis']/2) + 5, pupil['y']),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Add parameter info overlay
        y_offset = 30
        cv2.putText(display_frame, f"Mask Size: {self.params['mask_size']}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 20
        cv2.putText(display_frame, f"Pixel Thresh: {self.params['pixel_thresh']}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 20
        cv2.putText(display_frame, f"Added Thresh: {self.params['added_threshold']}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Store current frame
        self.current_frame = display_frame
        
        # Display in OpenCV window
        cv2.imshow("Real JEO Pupil Detection", display_frame)
        cv2.waitKey(1)  # Process window events
        
        # Update info display
        self.update_info_display(detected_pupils, frame_path)
        
    def update_info_display(self, detected_pupils, frame_path):
        """Update information display"""
        info = f"Frame: {self.current_frame_idx + 1}/{len(self.frames)}\n"
        info += f"File: {os.path.basename(frame_path)}\n"
        info += f"Detected pupils: {len(detected_pupils)}\n"
        
        if detected_pupils:
            best = detected_pupils[0]
            info += f"Best: ({best['x']}, {best['y']}) Size:{best['major_axis']:.1f}x{best['minor_axis']:.1f} Score={best['total_score']:.3f}"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        
        # Update results
        results = "Detection Results:\n"
        for i, pupil in enumerate(detected_pupils[:3]):  # Show top 3
            results += f"{i+1}. Pos:({pupil['x']},{pupil['y']}) "
            results += f"Size:{pupil['major_axis']:.1f}x{pupil['minor_axis']:.1f} "
            results += f"Area:{pupil['area']:.0f} "
            results += f"Score:{pupil['total_score']:.3f}\n"
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, results)
        
    def toggle_play(self):
        """Toggle playback"""
        self.playing = not self.playing
        self.play_button.config(text="Pause" if self.playing else "Play")
        
        if self.playing:
            self.play_frames()
            
    def play_frames(self):
        """Play frames automatically"""
        if not self.playing:
            return
            
        self.display_current_frame()
        
        # Advance frame
        self.current_frame_idx += 1
        if self.current_frame_idx >= len(self.frames):
            self.current_frame_idx = 0
            
        self.frame_var.set(self.current_frame_idx)
        
        # Schedule next frame
        self.root.after(self.play_speed, self.play_frames)
        
    def reset_playback(self):
        """Reset playback to beginning"""
        self.playing = False
        self.play_button.config(text="Play")
        self.current_frame_idx = 0
        self.frame_var.set(0)
        self.display_current_frame()
        
    def export_parameters(self):
        """Export current parameters to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            with open(filename, 'w') as f:
                f.write("# Real JEO EyeTracker Parameters\n")
                f.write("# Generated by Real JEO Pupil Detection Tuner\n")
                f.write("# Based on OrloskyPupilDetectorRaspberryPi.py\n\n")
                for param, value in self.params.items():
                    f.write(f"{param} = {value}\n")
            
            messagebox.showinfo("Export", f"Parameters exported to {filename}")

def main():
    root = tk.Tk()
    app = RealJEOPupilDetectionTuner(root)
    
    def on_closing():
        cv2.destroyAllWindows()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 