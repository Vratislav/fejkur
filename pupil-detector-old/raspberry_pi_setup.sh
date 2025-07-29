#!/bin/bash
# Raspberry Pi setup script for pupil detector

echo "Setting up Pupil Detector for Raspberry Pi..."
echo "=============================================="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-opencv libatlas-base-dev libgtk-3-dev

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Test installation
echo "Testing installation..."
python3 test_installation.py

echo ""
echo "Setup complete! You can now run:"
echo "  python3 pupil_detector.py"
echo "  python3 pupil_detector.py --debug" 