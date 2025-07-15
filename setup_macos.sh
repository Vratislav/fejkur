#!/bin/bash

# Voice Recognition Door Opener - macOS Setup Script
# For development and testing on macOS

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        error "This script is designed for macOS"
    fi
    
    log "Running on macOS $(sw_vers -productVersion)"
}

# Check if Homebrew is installed
check_homebrew() {
    if ! command -v brew &> /dev/null; then
        error "Homebrew is not installed. Please install it first: https://brew.sh/"
    fi
    
    log "Homebrew is installed"
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    # Install audio dependencies
    brew install portaudio
    brew install ffmpeg
    
    log "System dependencies installed"
}

# Create virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log "Virtual environment created"
    else
        log "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    log "Python virtual environment ready"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    
    source venv/bin/activate
    
    # Install requirements
    pip install -r requirements-macos.txt
    
    log "Python dependencies installed"
}

# Download VOSK model
download_vosk_model() {
    log "Downloading VOSK Czech model..."
    
    MODEL_DIR="./vosk-model-cs"
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
            if curl -L -o model.tar.gz "$url" 2>/dev/null; then
                log "Successfully downloaded from: $url"
                download_success=true
                break
            else
                log "Failed to download from: $url"
            fi
        done
        
        if [ "$download_success" = false ]; then
            warn "Failed to download VOSK model from all URLs"
            log "Please download manually from: https://alphacephei.com/vosk/models/"
            log "Or use a different Czech model"
            return 1
        fi
        
        log "Extracting model..."
        tar -xzf model.tar.gz
        mv vosk-model-small-cs-0.4-sphere/* .
        rmdir vosk-model-small-cs-0.4-sphere
        rm model.tar.gz
        
        cd ..
        log "VOSK model downloaded and extracted"
    else
        log "VOSK model already exists"
    fi
}

# Test installation
test_installation() {
    log "Testing installation..."
    
    source venv/bin/activate
    
    # Test Python imports
    python3 -c "
import sys
sys.path.append('.')
try:
    from config_manager import ConfigManager
    from audio_manager import AudioManager
    from voice_processor import VoiceProcessor
    from mqtt_client import MQTTClient
    from password_manager import PasswordManager
    print('All modules imported successfully')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
"
    
    log "Installation test completed"
}

# Create sample passwords
create_sample_passwords() {
    log "Creating sample passwords..."
    
    if [ ! -f "passwords.txt" ]; then
        cat > passwords.txt << EOF
# Voice Recognition Passwords
# One password per line
# These will be matched against VOSK speech recognition output

v sklo
otevři dveře
heslo
EOF
        log "Sample passwords created"
    else
        log "Passwords file already exists"
    fi
}

# Main setup function
main() {
    log "Starting Voice Recognition Door Opener setup for macOS..."
    
    # Check requirements
    check_macos
    check_homebrew
    
    # Install dependencies
    install_system_deps
    setup_python_env
    install_python_deps
    
    # Setup components
    download_vosk_model
    create_sample_passwords
    
    # Test installation
    test_installation
    
    log "Setup completed successfully!"
    log ""
    log "Next steps:"
    log "1. Test the sound system:"
    log "   source venv/bin/activate"
    log "   python test_sounds.py"
    log ""
    log "2. Run the voice recognizer:"
    log "   source venv/bin/activate"
    log "   python run_macos.py"
    log ""
    log "3. Configure MQTT settings in config.yaml (optional)"
    log ""
    log "4. Add your passwords to passwords.txt"
    log ""
    log "Usage:"
    log "  - Press Enter to start voice recognition"
    log "  - Press 'q' to quit"
    log "  - Say one of the passwords in passwords.txt"
}

# Run main function
main "$@" 