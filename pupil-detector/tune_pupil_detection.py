#!/usr/bin/env python3

import os
import cv2
import numpy as np
import glob
from typing import Tuple, Optional, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time

class PupilDetectionTuner:
    def __init__(self, root):
        self.root = root
        self.root.title("Pupil Detection Parameter Tuner")
        self.root.geometry("800x600")
        
        # Detection parameters (with defaults)
        self.params = {
            'blur_kernel': 15,
            'dp': 1.5,
            'min_dist': 80,
            'param1': 50,
            'param2': 20,
            'min_radius': 8,
            'max_radius': 40,
            'darkness_threshold': 0.7,
            'center_weight': 1.0
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
        cv2.namedWindow("Pupil Detection", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Pupil Detection", 640, 480)
        
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
        ttk.Label(parent, text="Detection Parameters", font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        
        params_frame = ttk.Frame(parent)
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create sliders for each parameter in a grid
        self.param_vars = {}
        param_configs = [
            ('blur_kernel', 'Blur Kernel', 3, 31, 2),
            ('dp', 'DP (Resolution)', 1.0, 3.0, 0.1),
            ('min_dist', 'Min Distance', 20, 150, 5),
            ('param1', 'Param1 (Edge)', 10, 100, 5),
            ('param2', 'Param2 (Center)', 5, 50, 1),
            ('min_radius', 'Min Radius', 3, 20, 1),
            ('max_radius', 'Max Radius', 20, 80, 2),
            ('darkness_threshold', 'Darkness Thresh', 0.3, 0.9, 0.05),
            ('center_weight', 'Center Weight', 0.5, 2.0, 0.1)
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
            "/home/fejkur/recordings",
            "./recordings", 
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
        if param == 'blur_kernel':
            # Ensure odd number for blur kernel
            val = int(float(value))
            if val % 2 == 0:
                val += 1
            self.params[param] = val
        else:
            self.params[param] = float(value)
        
        # Update value label
        label = getattr(self, f"{param}_label", None)
        if label:
            label.config(text=f"{self.params[param]:.3f}")
        
        # Update display if not playing
        if not self.playing:
            self.display_current_frame()
            
    def detect_pupil_with_params(self, frame):
        """Detect pupil using current parameters"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply blur with current kernel size
        kernel_size = int(self.params['blur_kernel'])
        if kernel_size % 2 == 0:
            kernel_size += 1
        gray = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
        
        # Create center mask
        height, width = gray.shape
        center_x, center_y = width // 2, height // 2
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(mask, (center_x, center_y), min(width, height) // 3, 255, -1)
        
        # Apply mask
        masked_gray = cv2.bitwise_and(gray, mask)
        
        # Invert for dark region detection
        inverted = cv2.bitwise_not(masked_gray)
        
        # Threshold
        _, thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # HoughCircles with current parameters
        circles = cv2.HoughCircles(
            thresh,
            cv2.HOUGH_GRADIENT,
            dp=self.params['dp'],
            minDist=int(self.params['min_dist']),
            param1=int(self.params['param1']),
            param2=int(self.params['param2']),
            minRadius=int(self.params['min_radius']),
            maxRadius=int(self.params['max_radius'])
        )
        
        detected_pupils = []
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            # Filter and score circles
            for (x, y, r) in circles:
                if x - r > 0 and x + r < width and y - r > 0 and y + r < height:
                    # Check darkness
                    roi = gray[y-r:y+r, x-r:x+r]
                    if roi.size > 0:
                        mean_intensity = np.mean(roi)
                        if mean_intensity < np.mean(gray) * self.params['darkness_threshold']:
                            # Calculate distance from center
                            distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                            
                            # Score based on darkness and center proximity
                            darkness_score = 1.0 - (mean_intensity / 255.0)
                            center_score = 1.0 - (distance_from_center / (min(width, height) / 2))
                            total_score = darkness_score + (center_score * self.params['center_weight'])
                            
                            detected_pupils.append({
                                'x': x, 'y': y, 'r': r,
                                'darkness': darkness_score,
                                'center_score': center_score,
                                'total_score': total_score,
                                'distance': distance_from_center
                            })
        
        # Sort by total score
        detected_pupils.sort(key=lambda p: p['total_score'], reverse=True)
        
        return detected_pupils, thresh
        
    def display_current_frame(self):
        """Display current frame with detection overlay"""
        if not self.frames or self.current_frame_idx >= len(self.frames):
            return
            
        # Load frame
        frame_path = self.frames[self.current_frame_idx]
        frame = cv2.imread(frame_path)
        if frame is None:
            return
            
        # Detect pupils
        detected_pupils, thresh = self.detect_pupil_with_params(frame)
        
        # Create display frame
        display_frame = frame.copy()
        
        # Add reference overlays
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # Center crosshair
        cv2.line(display_frame, (center_x-20, center_y), (center_x+20, center_y), (128, 128, 128), 1)
        cv2.line(display_frame, (center_x, center_y-20), (center_x, center_y+20), (128, 128, 128), 1)
        
        # Search area
        search_radius = min(width, height) // 3
        cv2.circle(display_frame, (center_x, center_y), search_radius, (64, 64, 64), 1)
        
        # Draw detected pupils
        for i, pupil in enumerate(detected_pupils):
            color = (0, 255, 0) if i == 0 else (0, 255, 255)  # Best in green, others in yellow
            cv2.circle(display_frame, (pupil['x'], pupil['y']), pupil['r'], color, 2)
            cv2.circle(display_frame, (pupil['x'], pupil['y']), 2, color, -1)
            
            # Add score text
            cv2.putText(display_frame, f"{pupil['total_score']:.2f}", 
                       (pupil['x'] + pupil['r'] + 5, pupil['y']),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Add parameter info overlay
        y_offset = 30
        cv2.putText(display_frame, f"Blur: {self.params['blur_kernel']}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 20
        cv2.putText(display_frame, f"DP: {self.params['dp']:.1f}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 20
        cv2.putText(display_frame, f"MinDist: {self.params['min_dist']}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Store current frame
        self.current_frame = display_frame
        
        # Display in OpenCV window
        cv2.imshow("Pupil Detection", display_frame)
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
            info += f"Best: ({best['x']}, {best['y']}) R={best['r']} Score={best['total_score']:.3f}"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        
        # Update results
        results = "Detection Results:\n"
        for i, pupil in enumerate(detected_pupils[:3]):  # Show top 3
            results += f"{i+1}. Pos:({pupil['x']},{pupil['y']}) R:{pupil['r']} "
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
                f.write("# Pupil Detection Parameters\n")
                f.write("# Generated by Pupil Detection Tuner\n\n")
                for param, value in self.params.items():
                    f.write(f"{param} = {value}\n")
            
            messagebox.showinfo("Export", f"Parameters exported to {filename}")

def main():
    root = tk.Tk()
    app = PupilDetectionTuner(root)
    
    def on_closing():
        cv2.destroyAllWindows()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 