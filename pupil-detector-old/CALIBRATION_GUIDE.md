# Camera Calibration Guide for PyPupilEXT

## Why You're Getting -1.00mm Pupil Size

The -1.00mm pupil size indicates that PyPupilEXT is detecting the pupil but cannot convert pixel measurements to physical measurements (millimeters) because the camera is not calibrated.

## The Problem

PyPupilEXT's `physicalDiameter` property returns -1 when:
1. The camera is not calibrated
2. The calibration data is missing or incorrect
3. The detection algorithm cannot determine the physical size

## Solution: Camera Calibration

### Step 1: Generate Calibration Targets

First, create printable calibration targets:

```bash
# Generate all calibration targets
python generate_calibration_targets.py

# Or generate a single target
python generate_calibration_targets.py --single 4.0
```

This creates `calibration_targets_YYYYMMDD_HHMMSS.png` with circles of known diameters:
- Small: 2mm diameter
- Medium: 4mm diameter  
- Large: 6mm diameter

### Step 2: Print Calibration Targets

1. Print the generated image at **300 DPI** (or your printer's native resolution)
2. Ensure **100% scale** (no scaling)
3. Use high-quality paper for better contrast

### Step 3: Run Camera Calibration

```bash
# Run the calibration script
python camera_calibration.py --debug
```

The calibration process:
1. Shows each target size on screen
2. Detects circles in the camera feed
3. Measures pixel diameters of detected circles
4. Calculates calibration factor (mm per pixel)
5. Saves calibration data to JSON file

### Step 4: Use Calibrated Detection

```bash
# Run calibrated pupil detection
python pupil_detector_calibrated.py --calibration calibration_YYYYMMDD_HHMMSS.json --debug
```

## Alternative Calibration Methods

### Method 1: Physical Objects
Use objects with known diameters:
- Coins (check your country's coin specifications)
- Standard washers or nuts
- Calibrated rulers or measuring tools

### Method 2: Digital Calibration
Display calibration targets on screen:
1. Open the generated PNG on your computer
2. Display at 100% zoom
3. Measure the actual displayed size
4. Use these measurements in calibration

### Method 3: Manual Calibration
If you know your camera's specifications:
1. Calculate mm per pixel based on sensor size and resolution
2. Create a simple calibration file manually
3. Test with known objects

## Calibration File Format

The calibration script creates a JSON file like this:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "calibration_factor_mm_per_pixel": 0.0123,
  "camera_id": 0,
  "resolution": {
    "width": 640,
    "height": 480
  }
}
```

## Important Notes

### Distance Consistency
- Keep the same camera distance during calibration and detection
- Mark the position of your head/eyes relative to the camera
- Use a chin rest or head support for consistency

### Lighting Conditions
- Use consistent lighting during calibration and detection
- Avoid shadows and reflections on calibration targets
- Ensure good contrast between targets and background

### Camera Settings
- Use the same camera settings (resolution, focus, etc.)
- Avoid auto-focus changes between calibration and detection
- Keep camera position fixed

## Troubleshooting

### Still Getting -1.00mm
1. Check if calibration file is loaded correctly
2. Verify calibration factor is reasonable (typically 0.01-0.05 mm/px)
3. Ensure camera distance is the same
4. Try recalibrating with better targets

### Poor Calibration Results
1. Use higher contrast targets (black circles on white paper)
2. Ensure good lighting and no shadows
3. Keep targets flat and perpendicular to camera
4. Use multiple measurements and average the results

### Detection Issues
1. Ensure good lighting on the eye
2. Keep eye clearly visible and centered
3. Avoid rapid movements
4. Try different detection algorithms (PuRe, ElSe, etc.)

## Quick Test

To verify calibration is working:

```bash
# Test without calibration (should show pixels)
python pupil_detector_calibrated.py --debug

# Test with calibration (should show mm)
python pupil_detector_calibrated.py --calibration your_calibration.json --debug
```

The first should show measurements in pixels, the second in millimeters.

## Expected Results

After proper calibration, you should see:
- Pupil diameters between 2-8mm (normal human range)
- Consistent measurements across frames
- Reasonable confidence values (>0.5)
- No more -1.00mm readings

## Advanced Usage

### Multiple Calibrations
You can create different calibration files for:
- Different camera distances
- Different lighting conditions
- Different camera settings

### Calibration Validation
Use the calibration script to verify your calibration:
1. Run calibration with known objects
2. Compare measured vs. actual sizes
3. Adjust if necessary

### Raspberry Pi Deployment
For Raspberry Pi deployment:
1. Calibrate on the target system
2. Use the same camera and settings
3. Account for different lighting conditions
4. Test with the headless logger script 