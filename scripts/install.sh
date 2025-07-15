#!/bin/bash

# Voice Recognition Door Opener Installation Script
# For Raspberry Pi 4

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/home/sluchatko/voice-recognizer"
SERVICE_NAME="voice-recognizer"

# Logging
LOG_FILE="/tmp/voice-recognizer-install.log"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as pi user."
    fi
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check if running on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        warn "This script is designed for Raspberry Pi. Continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log "Python version: $python_version"
    
    # Check available memory
    mem_total=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ "$mem_total" -lt 2048 ]; then
        warn "System has less than 2GB RAM. Performance may be limited."
    fi
    
    log "System requirements check completed"
}

# Update system packages
update_system() {
    log "Updating system packages..."
    
    sudo apt-get update
    sudo apt-get upgrade -y
    
    log "System packages updated"
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    # Audio dependencies
    sudo apt-get install -y \
        python3-pip \
        python3-dev \
        python3-venv \
        portaudio19-dev \
        libasound2-dev \
        libbluetooth-dev \
        bluetooth \
        bluez \
        bluez-tools \
        pulseaudio \
        pulseaudio-module-bluetooth \
        alsa-utils \
        libatlas-base-dev \
        libffi-dev \
        libssl-dev \
        ffmpeg \
        git \
        curl \
        wget \
        unzip
    
    # Enable Bluetooth
    sudo systemctl enable bluetooth
    sudo systemctl start bluetooth
    
    log "System dependencies installed"
}

# Create virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    log "Python virtual environment created"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Install requirements
    pip install -r "$INSTALL_DIR/requirements.txt"
    
    log "Python dependencies installed"
}

# Download VOSK model
download_vosk_model() {
    log "Downloading VOSK Czech model..."
    
    MODEL_DIR="$INSTALL_DIR/vosk-model-cs"
    MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4-sphere.tar.gz"
    
    # Try alternative URLs if the main one fails
    ALTERNATIVE_URLS=(
        "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4-sphere.tar.gz"
        "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4.tar.gz"
        "https://alphacephei.com/vosk/models/vosk-model-cs-0.4.tar.gz"
    )
    
    if [ ! -d "$MODEL_DIR" ]; then
        mkdir -p "$MODEL_DIR"
        cd "$MODEL_DIR"
        
        log "Downloading model (this may take a while)..."
        
        # Try different URLs
        download_success=false
        for url in "${ALTERNATIVE_URLS[@]}"; do
            log "Trying URL: $url"
            if wget -O model.tar.gz "$url" 2>/dev/null; then
                log "Successfully downloaded from: $url"
                download_success=true
                break
            else
                log "Failed to download from: $url"
            fi
        done
        
        if [ "$download_success" = false ]; then
            error "Failed to download VOSK model from all URLs"
            log "Please download manually from: https://alphacephei.com/vosk/models/"
            log "Or use a different Czech model"
            return 1
        fi
        
        log "Extracting model..."
        tar -xzf model.tar.gz
        mv vosk-model-small-cs-0.4-sphere/* .
        rmdir vosk-model-small-cs-0.4-sphere
        rm model.tar.gz
        
        log "VOSK model downloaded and extracted"
    else
        log "VOSK model already exists"
    fi
}

# Configure audio
configure_audio() {
    log "Configuring audio system..."
    
    # Create audio directory
    mkdir -p "$INSTALL_DIR/audio"
    
    # Generate sample audio files if they don't exist
    if [ ! -f "$INSTALL_DIR/audio/password_prompt.wav" ]; then
        log "Creating sample audio files..."
        
        # Create a simple beep sound using sox (if available)
        if command -v sox &> /dev/null; then
            sox -n -r 16000 -c 1 "$INSTALL_DIR/audio/password_prompt.wav" synth 1 sine 1000
            sox -n -r 16000 -c 1 "$INSTALL_DIR/audio/success.wav" synth 0.5 sine 2000
            sox -n -r 16000 -c 1 "$INSTALL_DIR/audio/failure.wav" synth 0.5 sine 500
            sox -n -r 16000 -c 1 "$INSTALL_DIR/audio/error.wav" synth 1 sine 300
            log "Created audio files using sox"
        else
            # Create empty files as placeholders
            touch "$INSTALL_DIR/audio/password_prompt.wav"
            touch "$INSTALL_DIR/audio/success.wav"
            touch "$INSTALL_DIR/audio/failure.wav"
            touch "$INSTALL_DIR/audio/error.wav"
            log "Created placeholder audio files (sox not available)"
            log "You can create custom audio files in $INSTALL_DIR/audio/"
        fi
    fi
    
    log "Audio configuration completed"
}

# Configure Bluetooth
configure_bluetooth() {
    log "Configuring Bluetooth..."
    
    # Add current user to bluetooth group
    CURRENT_USER=$(whoami)
    sudo usermod -a -G bluetooth "$CURRENT_USER"
    
    # Configure Bluetooth audio
    cat > ~/.asoundrc << EOF
pcm.!default {
    type plug
    slave.pcm {
        type bluealsa
        device "00:00:00:00:00:00"
        profile "a2dp"
    }
}
EOF
    
    log "Bluetooth configuration completed"
    log "Please pair your Bluetooth handsfree device manually"
}

# Setup systemd service
setup_systemd() {
    log "Setting up systemd service..."
    
    # Copy service file
    sudo cp "$INSTALL_DIR/systemd/$SERVICE_NAME.service" "/etc/systemd/system/"
    
    # Update service file with correct paths
    sudo sed -i "s|/home/pi/voice-recognizer|$INSTALL_DIR|g" "/etc/systemd/system/$SERVICE_NAME.service"
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable "$SERVICE_NAME"
    
    log "Systemd service configured"
}

# Set permissions
set_permissions() {
    log "Setting file permissions..."
    
    # Set ownership
    sudo chown -R sluchatko:sluchatko "$INSTALL_DIR"
    
    # Set executable permissions
    chmod +x "$INSTALL_DIR/main.py"
    chmod +x "$INSTALL_DIR/install.sh"
    
    # Set log directory permissions
    sudo mkdir -p /var/log
    sudo touch /var/log/voice-recognizer.log
    sudo chown sluchatko:sluchatko /var/log/voice-recognizer.log
    
    log "Permissions set"
}

# Create configuration
create_config() {
    log "Creating configuration..."
    
    # Update config.yaml with correct paths
    sed -i "s|/home/pi/vosk-model-cs|$INSTALL_DIR/vosk-model-cs|g" "$INSTALL_DIR/config.yaml"
    
    log "Configuration created"
}

# Test installation
test_installation() {
    log "Testing installation..."
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    # Test Python imports
    python3 -c "
import sys
sys.path.append('.')
try:
    from config_manager import ConfigManager
    from bluetooth_manager import BluetoothManager
    from audio_manager import AudioManager
    from voice_processor import VoiceProcessor
    from mqtt_client import MQTTClient
    from button_handler import ButtonHandler
    from password_manager import PasswordManager
    print('All modules imported successfully')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
"
    
    log "Installation test completed"
}

# Main installation function
main() {
    log "Starting Voice Recognition Door Opener installation..."
    
    # Check requirements
    check_root
    check_system
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy files to installation directory
    if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
        log "Copying files to installation directory..."
        cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
    fi
    
    # Install dependencies
    update_system
    install_system_deps
    setup_python_env
    install_python_deps
    
    # Setup components
    download_vosk_model
    configure_audio
    configure_bluetooth
    setup_systemd
    set_permissions
    create_config
    
    # Test installation
    test_installation
    
    log "Installation completed successfully!"
    log ""
    log "Next steps:"
    log "1. Pair your Bluetooth handsfree device:"
    log "   bluetoothctl"
    log "   scan on"
    log "   pair <device_mac>"
    log "   connect <device_mac>"
    log ""
    log "2. Configure MQTT broker settings in config.yaml"
    log ""
    log "3. Test the system:"
    log "   sudo systemctl start voice-recognizer"
    log "   sudo systemctl status voice-recognizer"
    log ""
    log "4. Enable auto-start:"
    log "   sudo systemctl enable voice-recognizer"
    log ""
    log "Installation log: $LOG_FILE"
}

# Run main function
main "$@" 