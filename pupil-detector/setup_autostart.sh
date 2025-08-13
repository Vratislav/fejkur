#!/bin/bash

# Setup script for automatic pupil measurement startup
echo "Setting up automatic pupil measurement startup..."

# Create a root-owned directory for the service
sudo mkdir -p /opt/pupil-detector
sudo cp pupil_measurement_headless.py /opt/pupil-detector/
sudo cp -r EyeTracker /opt/pupil-detector/

# Set proper permissions for the service directory
sudo chown -R root:root /opt/pupil-detector/
sudo chmod -R 755 /opt/pupil-detector/

# Copy the service file to systemd directory
sudo cp pupil-measurement.service /etc/systemd/system/

# Update the service file to use the new path
sudo sed -i 's|/home/fejkur/pupil-detector|/opt/pupil-detector|g' /etc/systemd/system/pupil-measurement.service

# Create recordings directory with proper permissions
sudo mkdir -p /home/fejkur/recordings
sudo chown fejkur:fejkur /home/fejkur/recordings
sudo chmod 755 /home/fejkur/recordings

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable pupil-measurement.service

# Start the service immediately
sudo systemctl start pupil-measurement.service

# Check the status
echo "Service status:"
sudo systemctl status pupil-measurement.service

echo ""
echo "Setup complete! The pupil measurement system will now:"
echo "- Start automatically on boot as root user"
echo "- Restart automatically if it crashes"
echo "- Run without requiring a display"
echo "- Have full access to GPIO and camera hardware"
echo "- Save all recordings to /home/fejkur/recordings/"
echo "- Files are in /opt/pupil-detector/ (root-owned)"
echo ""
echo "To check status: sudo systemctl status pupil-measurement.service"
echo "To stop: sudo systemctl stop pupil-measurement.service"
echo "To disable: sudo systemctl disable pupil-measurement.service"
echo "To view logs: journalctl -u pupil-measurement.service -f"
echo ""
echo "To update files:"
echo "1. Copy new files to /home/fejkur/pupil-detector/"
echo "2. Run: sudo cp /home/fejkur/pupil-detector/pupil_measurement_headless.py /opt/pupil-detector/"
echo "3. Run: sudo systemctl restart pupil-measurement.service" 