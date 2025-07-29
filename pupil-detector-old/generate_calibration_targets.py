#!/usr/bin/env python3
"""
Generate Calibration Targets for PyPupilEXT
Creates printable calibration targets with known diameters.
"""

import cv2
import numpy as np
import argparse
import os
from datetime import datetime


def create_calibration_target(diameter_mm: float, dpi: int = 300, margin_mm: float = 10.0) -> np.ndarray:
    """
    Create a calibration target with a circle of known diameter.
    
    Args:
        diameter_mm: Diameter of the circle in millimeters
        dpi: Dots per inch for printing
        margin_mm: Margin around the circle in millimeters
    
    Returns:
        Image with calibration target
    """
    # Convert mm to pixels (1 inch = 25.4 mm)
    mm_per_pixel = 25.4 / dpi
    diameter_pixels = int(diameter_mm / mm_per_pixel)
    margin_pixels = int(margin_mm / mm_per_pixel)
    
    # Create image with white background
    image_size = diameter_pixels + 2 * margin_pixels
    image = np.ones((image_size, image_size, 3), dtype=np.uint8) * 255
    
    # Draw black circle
    center = (image_size // 2, image_size // 2)
    radius = diameter_pixels // 2
    cv2.circle(image, center, radius, (0, 0, 0), -1)
    
    # Add text label
    font = cv2.FONT_HERSHEY_SIMPLEX
    text = f"{diameter_mm}mm"
    text_size = cv2.getTextSize(text, font, 1, 2)[0]
    text_x = center[0] - text_size[0] // 2
    text_y = center[1] + text_size[1] // 2
    cv2.putText(image, text, (text_x, text_y), font, 1, (255, 255, 255), 2)
    
    return image


def create_multi_target_image(targets: dict, dpi: int = 300) -> np.ndarray:
    """
    Create a single image with multiple calibration targets.
    
    Args:
        targets: Dictionary of {name: diameter_mm} pairs
        dpi: Dots per inch for printing
    
    Returns:
        Image with multiple calibration targets
    """
    # Calculate layout
    n_targets = len(targets)
    cols = min(3, n_targets)  # Max 3 columns
    rows = (n_targets + cols - 1) // cols
    
    # Calculate target size (use largest diameter)
    max_diameter = max(targets.values())
    mm_per_pixel = 25.4 / dpi
    max_diameter_pixels = int(max_diameter / mm_per_pixel)
    margin_pixels = int(20 / mm_per_pixel)  # 20mm margin
    target_size = max_diameter_pixels + 2 * margin_pixels
    
    # Create image
    image_width = cols * target_size
    image_height = rows * target_size
    image = np.ones((image_height, image_width, 3), dtype=np.uint8) * 255
    
    # Add title
    title = "PyPupilEXT Calibration Targets"
    font = cv2.FONT_HERSHEY_SIMPLEX
    title_size = cv2.getTextSize(title, font, 1.5, 3)[0]
    title_x = (image_width - title_size[0]) // 2
    cv2.putText(image, title, (title_x, 50), font, 1.5, (0, 0, 0), 3)
    
    # Add targets
    for i, (name, diameter) in enumerate(targets.items()):
        row = i // cols
        col = i % cols
        
        # Create individual target
        target = create_calibration_target(diameter, dpi)
        
        # Resize to fit
        target_resized = cv2.resize(target, (target_size, target_size))
        
        # Place in image
        y_start = row * target_size
        x_start = col * target_size
        image[y_start:y_start + target_size, x_start:x_start + target_size] = target_resized
    
    return image


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate calibration targets for PyPupilEXT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_calibration_targets.py                    # Generate all targets
  python generate_calibration_targets.py --single 4.0      # Generate single 4mm target
  python generate_calibration_targets.py --dpi 150         # Use 150 DPI for printing
        """
    )
    
    parser.add_argument(
        '--single',
        type=float,
        default=None,
        help='Generate single target with specified diameter (mm)'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='DPI for printing (default: 300)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output filename (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    # Define standard calibration targets
    targets = {
        'small': 2.0,    # 2mm diameter
        'medium': 4.0,   # 4mm diameter  
        'large': 6.0,    # 6mm diameter
    }
    
    if args.single:
        # Generate single target
        target = create_calibration_target(args.single, args.dpi)
        if args.output:
            filename = args.output
        else:
            filename = f"calibration_target_{args.single}mm.png"
        
        cv2.imwrite(filename, target)
        print(f"Generated single target: {filename}")
        print(f"Diameter: {args.single}mm, DPI: {args.dpi}")
        
    else:
        # Generate multi-target image
        image = create_multi_target_image(targets, args.dpi)
        
        if args.output:
            filename = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"calibration_targets_{timestamp}.png"
        
        cv2.imwrite(filename, image)
        print(f"Generated calibration targets: {filename}")
        print(f"DPI: {args.dpi}")
        print("Targets included:")
        for name, diameter in targets.items():
            print(f"  {name}: {diameter}mm")
    
    print(f"\nInstructions:")
    print(f"1. Print the image at {args.dpi} DPI")
    print(f"2. Ensure the print scale is 100% (no scaling)")
    print(f"3. Use the targets with the camera calibration script")
    print(f"4. Keep the camera at the same distance during calibration and detection")


if __name__ == "__main__":
    main() 