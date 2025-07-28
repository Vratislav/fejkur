#!/usr/bin/env python3
"""
Camera Viewer Utility for Raspberry Pi
Provides multiple ways to view camera feed over SSH
"""

import cv2
import numpy as np
import argparse
import time
import os
import sys
from picamera2 import Picamera2
import threading
import socket
import struct

class CameraViewer:
    def __init__(self, method='ssh_x11', resolution=(640, 480), fps=30):
        self.method = method
        self.resolution = resolution
        self.fps = fps
        self.running = False
        
        # Initialize camera
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(
            main={"size": self.resolution},
            buffer_count=4
        ))
        
    def start(self):
        """Start camera and display based on selected method"""
        self.picam2.start()
        self.running = True
        
        if self.method == 'ssh_x11':
            self.display_ssh_x11()
        elif self.method == 'vnc':
            self.display_vnc()
        elif self.method == 'stream':
            self.display_stream()
        elif self.method == 'save_frames':
            self.save_frames()
        else:
            print(f"Unknown method: {self.method}")
            
    def display_ssh_x11(self):
        """Display camera feed using X11 forwarding over SSH"""
        print("Starting X11 display...")
        print("Make sure to connect with: ssh -X pi@raspberrypi")
        
        try:
            while self.running:
                frame = self.picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                cv2.imshow('Raspberry Pi Camera', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            print(f"X11 display error: {e}")
            print("Try connecting with: ssh -X pi@raspberrypi")
        finally:
            cv2.destroyAllWindows()
            
    def display_vnc(self):
        """Display camera feed using VNC"""
        print("Starting VNC display...")
        print("Connect via VNC to view the camera feed")
        
        try:
            while self.running:
                frame = self.picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                cv2.imshow('Raspberry Pi Camera', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            print(f"VNC display error: {e}")
        finally:
            cv2.destroyAllWindows()
            
    def display_stream(self):
        """Stream camera feed over network"""
        print("Starting network stream...")
        print("Connect to stream at: http://raspberrypi:8080")
        
        # Create video writer for streaming
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('appsrc ! videoconvert ! x264enc ! rtph264pay ! udpsink host=0.0.0.0 port=8080',
                             cv2.CAP_GSTREAMER, fourcc, self.fps, self.resolution)
        
        try:
            while self.running:
                frame = self.picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                out.write(frame)
                
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            out.release()
            
    def save_frames(self):
        """Save frames to disk for later viewing"""
        print("Saving frames to /tmp/camera_frames/")
        os.makedirs('/tmp/camera_frames', exist_ok=True)
        
        frame_count = 0
        try:
            while self.running:
                frame = self.picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                filename = f"/tmp/camera_frames/frame_{frame_count:04d}.jpg"
                cv2.imwrite(filename, frame)
                
                frame_count += 1
                time.sleep(1/self.fps)  # Control frame rate
                
                if frame_count > 100:  # Limit frames
                    frame_count = 0
                    
        except Exception as e:
            print(f"Save frames error: {e}")
            
    def stop(self):
        """Stop camera and cleanup"""
        self.running = False
        self.picam2.stop()

def main():
    parser = argparse.ArgumentParser(description='Raspberry Pi Camera Viewer')
    parser.add_argument('--method', choices=['ssh_x11', 'vnc', 'stream', 'save_frames'],
                       default='ssh_x11', help='Display method')
    parser.add_argument('--resolution', nargs=2, type=int, default=[640, 480],
                       help='Camera resolution (width height)')
    parser.add_argument('--fps', type=int, default=30, help='Frame rate')
    
    args = parser.parse_args()
    
    viewer = CameraViewer(method=args.method, 
                         resolution=tuple(args.resolution), 
                         fps=args.fps)
    
    try:
        viewer.start()
    except KeyboardInterrupt:
        print("\nStopping camera viewer...")
    finally:
        viewer.stop()

if __name__ == "__main__":
    main() 