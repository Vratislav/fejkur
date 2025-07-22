# Pupil Detector

A command-line tool for real-time pupil size detection using PyPupilEXT and webcam feed.

## Features

- Real-time pupil diameter detection from webcam
- Debug mode with visualization window
- Cross-platform compatibility (macOS, Linux, Raspberry Pi)
- Configurable camera selection
- Performance metrics (FPS, processing time)
- Clean command-line interface

## Installation

### Prerequisites

- Python 3.7 or higher
- Webcam access
- OpenCV dependencies

### Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### macOS Specific Setup

If you encounter issues with camera access on macOS:

```bash
# Install additional dependencies if needed
brew install opencv
```

### Raspberry Pi Setup

For Raspberry Pi deployment:

```bash
# Update system
sudo apt update && sudo apt upgrade

# Install system dependencies
sudo apt install python3-pip python3-opencv libatlas-base-dev

# Install Python dependencies
pip3 install -r requirements.txt

# For headless operation (without GUI), you may need:
sudo apt install libgtk-3-dev
```

## Usage

### Basic Usage

```bash
# Start pupil detection with default camera (0)
python pupil_detector.py

# Enable debug mode with visualization
python pupil_detector.py --debug

# Use a different camera
python pupil_detector.py --camera 1

# Debug mode with specific camera
python pupil_detector.py --debug --camera 1
```

### Command Line Options

- `--debug`: Enable debug mode with visualization window
- `--camera <id>`: Specify camera device ID (default: 0)

### Debug Mode Controls

When debug mode is enabled:
- Press `q` to quit the application
- Press `d` to toggle debug mode on/off

### Output Format

The script outputs detection results to the console:

```
Pupil: 4.25mm (confidence: 0.85, time: 12.3ms)
No pupil detected
Pupil: 3.98mm (confidence: 0.92, time: 11.8ms)
```

## Raspberry Pi Deployment

### Headless Operation

For Raspberry Pi without display:

```bash
# Run without debug mode (no GUI required)
python3 pupil_detector.py

# Or redirect output to file
python3 pupil_detector.py > pupil_data.log 2>&1
```

### Performance Optimization

For better performance on Raspberry Pi:

1. Reduce camera resolution in the code if needed
2. Use a USB camera for better compatibility
3. Ensure adequate lighting for better detection

### Camera Setup

```bash
# List available cameras
ls /dev/video*

# Test camera access
v4l2-ctl --list-devices
```

## Troubleshooting

### Common Issues

1. **Camera not found**: Try different camera IDs (0, 1, 2, etc.)
2. **PyPupilEXT import error**: Ensure the repository is accessible
3. **OpenCV errors**: Install system dependencies for your platform
4. **No pupil detection**: Ensure good lighting and face visibility

### Debug Tips

- Use debug mode to visualize detection
- Check camera permissions on macOS
- Ensure adequate lighting conditions
- Position face clearly in camera view

## Development

### Project Structure

```
pupil-detector/
├── pupil_detector.py    # Main detection script
├── requirements.txt     # Python dependencies
└── README.md          # This file
```

### Adding Features

The `PupilDetector` class is designed to be extensible:

- Add new detection algorithms
- Implement data logging
- Add calibration features
- Extend debug visualization

## License

This project uses PyPupilEXT which is licensed under its own terms. Please refer to the PyPupilEXT repository for licensing information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on both macOS and Raspberry Pi
5. Submit a pull request 