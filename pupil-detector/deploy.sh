#!/bin/bash
# Deployment script for pupil detector project
# Usage: ./deploy.sh [--install-deps]

# Configuration
PI_USER="fejkur"
PI_HOST="fejkur.local"
PI_PATH="/home/fejkur/pupil-detector"
LOCAL_PATH="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print with color
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

# Check if we can connect to the Pi
check_connection() {
    print_status "Checking connection to Raspberry Pi..."
    if ssh -q ${PI_USER}@${PI_HOST} exit; then
        print_status "Connection successful!"
        return 0
    else
        print_error "Cannot connect to ${PI_USER}@${PI_HOST}"
        print_warning "Make sure:"
        echo "  1. The Raspberry Pi is powered on"
        echo "  2. It's connected to the network"
        echo "  3. The hostname 'fejkur.local' resolves correctly"
        echo "  4. SSH is enabled on the Pi (sudo raspi-config)"
        return 1
    fi
}

# Create required directories
create_directories() {
    print_status "Creating project directories on Raspberry Pi..."
    ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_PATH}/{utils,vision,hardware,communication}"
}

# Sync project files
sync_files() {
    print_status "Syncing project files to Raspberry Pi..."
    
    # Create exclude list for rsync
    cat > /tmp/rsync-exclude << EOF
.git/
.gitignore
__pycache__/
*.pyc
venv/
.env
*.log
EOF
    
    # Sync files
    rsync -av --progress --exclude-from=/tmp/rsync-exclude \
        ${LOCAL_PATH}/ \
        ${PI_USER}@${PI_HOST}:${PI_PATH}/
        
    if [ $? -eq 0 ]; then
        print_status "Files synced successfully!"
    else
        print_error "Failed to sync files"
        exit 1
    fi
}

# Install dependencies if requested
install_dependencies() {
    print_status "Installing dependencies on Raspberry Pi..."
    
    ssh ${PI_USER}@${PI_HOST} "bash -s" << EOF
        set -e  # Exit on any error
        
        echo "Installing system dependencies..."
        # Install system dependencies
        sudo apt update
        sudo apt install -y python3-pip python3-venv python3-full
        sudo apt install -y libcap-dev  # Required for python-prctl
        sudo apt install -y python3-numpy python3-opencv  # Pre-built packages
        sudo apt install -y libatlas-base-dev  # Required for numpy/scipy
        sudo apt install -y libhdf5-dev libhdf5-serial-dev
        sudo apt install -y libopenblas-dev
        sudo apt install -y python3-picamera2
        
        echo "Setting up virtual environment..."
        # Navigate to project directory
        cd ${PI_PATH}
        
        # Remove existing venv if it exists
        rm -rf venv
        
        # Create new virtual environment
        python3 -m venv venv
        
        # Activate virtual environment and install dependencies
        source venv/bin/activate
        
        # Install dependencies in the virtual environment
        pip install --upgrade pip
        pip install adafruit-blinka
        pip install adafruit-circuitpython-neopixel
        pip install rpi_ws281x  # Install in virtual environment only
        
        # Install project dependencies
        if [ -f requirements.txt ]; then
            pip install -r requirements.txt
        else
            echo "requirements.txt not found in ${PI_PATH}"
            exit 1
        fi
        
        # Add user to required groups
        sudo usermod -a -G gpio,spi \$USER
        
        # Create udev rules for hardware access
        echo 'SUBSYSTEM=="mem", KERNEL=="mem", GROUP="gpio", MODE="0660"' | sudo tee /etc/udev/rules.d/99-mem.rules
        
        # Reload udev rules
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        
        # Enable SPI
        sudo raspi-config nonint do_spi 0
        
        # Configure audio to not use PWM
        sudo sed -i 's/^dtparam=audio=on/#dtparam=audio=on/' /boot/config.txt
        
        echo "Installation completed successfully!"
        echo "Please reboot the Raspberry Pi for changes to take effect."
EOF

    if [ $? -eq 0 ]; then
        print_status "Dependencies installed successfully!"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Make scripts executable
make_executable() {
    print_status "Making scripts executable..."
    ssh ${PI_USER}@${PI_HOST} "chmod +x ${PI_PATH}/utils/*.sh ${PI_PATH}/utils/*.py"
}

# Test camera setup
test_camera() {
    print_status "Testing camera setup..."
    ssh ${PI_USER}@${PI_HOST} "cd ${PI_PATH} && ./utils/simple_camera_test.sh info"
}

# Main deployment process
main() {
    print_status "Starting deployment to Raspberry Pi..."
    
    # Check connection first
    check_connection || exit 1
    
    # Create directories
    create_directories
    
    # Sync files
    sync_files
    
    # Install dependencies if --install-deps flag is provided
    if [[ "$1" == "--install-deps" ]]; then
        install_dependencies
    fi
    
    # Make scripts executable
    make_executable
    
    # Test camera
    test_camera
    
    print_status "Deployment completed!"
    echo
    echo "Next steps:"
    echo "1. SSH into your Raspberry Pi:"
    echo "   ssh ${PI_USER}@${PI_HOST}"
    echo
    echo "2. Test the camera:"
    echo "   cd ${PI_PATH}"
    echo "   ./utils/simple_camera_test.sh test"
    echo
    echo "3. View camera feed (with X11):"
    echo "   ssh -X ${PI_USER}@${PI_HOST}"
    echo "   cd ${PI_PATH}"
    echo "   python3 utils/camera_viewer.py --method ssh_x11"
}

# Run main with all arguments
main "$@" 