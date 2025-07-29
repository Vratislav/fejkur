#!/usr/bin/env python3

import os
import sys
import time
import argparse
from datetime import datetime
import cv2
import RPi.GPIO as GPIO
from rpi_ws281x import PixelStrip, Color

# Add system Python path for libcamera
sys.path.append('/usr/lib/python3/dist-packages')
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

# Constants for NeoPixel strip
LED_COUNT = 12        # Number of LED pixels
LED_PIN = 18         # GPIO pin connected to the pixels (must support PWM)
LED_FREQ_HZ = 800000 # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10         # DMA channel to use for generating signal
LED_BRIGHTNESS = 255 # Set to 0 for darkest and 255 for brightest
LED_CHANNEL = 0      # PWM channel
LED_INVERT = False   # True to invert the signal

class EyeRecorder:
    def __init__(self, output_dir: str, preview: bool = False):
        self.output_dir = output_dir
        self.preview = preview
        os.makedirs(output_dir, exist_ok=True)
        
        self.setup_camera()
        self.setup_leds()
        
        if preview:
            os.environ["DISPLAY"] = ":0"
            cv2.namedWindow("Recording", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Recording", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    def setup_camera(self):
        """Initialize camera for recording"""
        self.camera = Picamera2()
        video_config = self.camera.create_video_configuration(
            main={"size": (1280, 720), "format": "RGB888"},
            lores={"size": (640, 480), "format": "YUV420"})
        self.camera.configure(video_config)
        self.camera.start()
        
    def setup_leds(self):
        """Initialize NeoPixel strip"""
        self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        self.set_all_color(0, 0, 0)  # Start with all LEDs off
    
    def set_all_color(self, red: int, green: int, blue: int, brightness_percent: float = 100):
        """Set all LEDs to specified RGB color with brightness percentage"""
        brightness = int((brightness_percent / 100.0) * 255)
        color = Color(red, green, blue)
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, color)
            self.strip.setBrightness(brightness)
        self.strip.show()
    
    def record_sequence(self):
        """Record a complete LED sequence"""
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = os.path.join(self.output_dir, f"eye_recording_{timestamp}.mp4")
        
        # Setup video encoder
        encoder = H264Encoder(bitrate=10000000)  # 10Mbps for good quality
        output = FfmpegOutput(video_path)
        
        # Start recording
        self.camera.start_recording(encoder, output)
        print(f"Recording started: {video_path}")
        
        try:
            # Phase 1: LEDs off (5 seconds)
            print("Phase 1: LEDs off")
            self.set_all_color(0, 0, 0)
            self.record_phase(5)
            
            # Phase 2: 10% white (10 seconds)
            print("Phase 2: 10% white")
            self.set_all_color(255, 255, 255, 10)
            self.record_phase(10)
            
            # Phase 3: 35% white (10 seconds)
            print("Phase 3: 35% white")
            self.set_all_color(255, 255, 255, 35)
            self.record_phase(10)
            
        finally:
            # Stop recording and cleanup
            print("Recording complete")
            self.camera.stop_recording()
            self.set_all_color(0, 0, 0)
            
            if self.preview:
                cv2.destroyAllWindows()
    
    def record_phase(self, duration: int):
        """Record a single phase with optional preview"""
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.preview:
                frame = self.camera.capture_array()
                
                # Add recording time overlay
                elapsed = time.time() - start_time
                remaining = duration - elapsed
                cv2.putText(frame, f"Time remaining: {remaining:.1f}s", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow("Recording", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.1)
    
    def cleanup(self):
        """Clean up resources"""
        self.camera.stop()
        if self.preview:
            cv2.destroyAllWindows()
        self.set_all_color(0, 0, 0)

def main():
    parser = argparse.ArgumentParser(description="Record eye video with LED sequence")
    parser.add_argument("--output-dir", default="/home/fejkur/recordings",
                      help="Directory to store recordings")
    parser.add_argument("--preview", action="store_true",
                      help="Show preview window during recording")
    args = parser.parse_args()
    
    recorder = EyeRecorder(args.output_dir, args.preview)
    try:
        recorder.record_sequence()
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        recorder.cleanup()

if __name__ == "__main__":
    main() 