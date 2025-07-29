#!/usr/bin/env python3
"""
Test script to demonstrate calibrated vs uncalibrated pupil detection.
"""

import cv2
import numpy as np
import sys
import time

try:
    import pypupilext
except ImportError:
    print("Error: PyPupilEXT not found. Please install it using:")
    print("pip install PyPupilEXT-0.0.1-cp310-cp310-macosx_14_0_universal2.whl")
    sys.exit(1)


def test_pupil_detection():
    """Test pupil detection with and without calibration."""
    print("Testing PyPupilEXT pupil detection...")
    print("="*50)
    
    # Initialize detector
    detector = pypupilext.PuRe()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Camera initialized. Press 'q' to quit, 'c' to capture a frame for analysis.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect pupil
            pupil = detector.run(gray)
            
            # Display frame with detection info
            display_frame = frame.copy()
            
            if pupil and pupil.valid(0.5):
                # Get measurements
                pixel_diameter = pupil.diameter()
                physical_diameter = pupil.physicalDiameter
                confidence = pupil.confidence
                
                # Draw pupil outline if available
                if pupil.hasOutline():
                    outline_points = pupil.rectPoints()
                    if outline_points:
                        points = np.array(outline_points, dtype=np.int32)
                        cv2.polylines(display_frame, [points], True, (0, 255, 0), 2)
                
                # Add text information
                cv2.putText(display_frame, f"Pixel Diameter: {pixel_diameter:.1f}px", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Physical Diameter: {physical_diameter:.2f}mm", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Confidence: {confidence:.2f}", (10, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Print to console
                print(f"Pupil detected: {pixel_diameter:.1f}px, {physical_diameter:.2f}mm (confidence: {confidence:.2f})")
                
                if physical_diameter == -1:
                    cv2.putText(display_frame, "NOT CALIBRATED - Use calibration script", (10, 120), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    print("  -> Physical diameter is -1.00mm (not calibrated)")
                    print("  -> Run camera_calibration.py to calibrate")
                else:
                    cv2.putText(display_frame, "CALIBRATED", (10, 120), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    print("  -> Physical diameter is calibrated")
            else:
                cv2.putText(display_frame, "No pupil detected", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                print("No pupil detected")
            
            cv2.putText(display_frame, "Press 'q' to quit, 'c' to capture", (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow('Pupil Detection Test', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                print("\n" + "="*50)
                print("CAPTURED FRAME ANALYSIS:")
                print("="*50)
                if pupil and pupil.valid(0.5):
                    print(f"Pixel diameter: {pupil.diameter():.1f}px")
                    print(f"Physical diameter: {pupil.physicalDiameter:.2f}mm")
                    print(f"Confidence: {pupil.confidence:.2f}")
                    print(f"Valid: {pupil.valid(0.5)}")
                    print(f"Has outline: {pupil.hasOutline()}")
                    print(f"Center: {pupil.center}")
                    print(f"Size: {pupil.size}")
                    print(f"Angle: {pupil.angle}")
                else:
                    print("No valid pupil detected in this frame")
                print("="*50 + "\n")
    
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()


def main():
    """Main function."""
    print("PyPupilEXT Calibration Test")
    print("This script demonstrates the difference between calibrated and uncalibrated detection.")
    print("If you see -1.00mm for physical diameter, you need to calibrate your camera.")
    print()
    
    test_pupil_detection()


if __name__ == "__main__":
    main() 