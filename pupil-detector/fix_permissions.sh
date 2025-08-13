#!/bin/bash

# Fix permissions script - makes files accessible for transfer again
echo "Fixing file permissions for transfer..."

# Change ownership back to fejkur user
sudo chown -R fejkur:fejkur /home/fejkur/pupil-detector/

# Set proper permissions for user access
sudo chmod -R 755 /home/fejkur/pupil-detector/

# Make sure the setup script is executable
sudo chmod +x /home/fejkur/pupil-detector/setup_autostart.sh

echo "Permissions fixed! You can now transfer files again."
echo ""
echo "To transfer files:"
echo "scp pupil_measurement_headless.py fejkur@fejkur.local:/home/fejkur/pupil-detector/"
echo "scp pupil-measurement.service fejkur@fejkur.local:/home/fejkur/pupil-detector/"
echo "scp setup_autostart.sh fejkur@fejkur.local:/home/fejkur/pupil-detector/"
echo "scp -r EyeTracker fejkur@fejkur.local:/home/fejkur/pupil-detector/"
echo ""
echo "Then run setup again:"
echo "ssh fejkur@fejkur.local"
echo "cd /home/fejkur/pupil-detector"
echo "./setup_autostart.sh" 