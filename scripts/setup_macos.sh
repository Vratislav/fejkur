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

# Download VOSK models
download_vosk_models() {
    log "Downloading VOSK models..."
    
    CZECH_MODEL_DIR="./models/vosk-model-cs"
    ENGLISH_MODEL_DIR="./models/vosk-model-en"
    
    # Current model URLs
    CZECH_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4-rhasspy.zip"
    ENGLISH_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    
    # Alternative URLs if the main ones fail
    CZECH_ALTERNATIVE_URLS=(
        "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4-rhasspy.zip"
        "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4-sphere.tar.gz"
        "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4.tar.gz"
        "https://alphacephei.com/vosk/models/vosk-model-cs-0.4.tar.gz"
    )
    
    ENGLISH_ALTERNATIVE_URLS=(
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.tar.gz"
        "https://alphacephei.com/vosk/models/vosk-model-en-us-0.15.tar.gz"
    )
    
    download_model() {
        local model_type=$1
        local model_dir=$2
        local model_url=$3
        local alternative_urls=("${@:4}")
        
        log "Downloading VOSK ${model_type} model..."
        
        if [ ! -d "$model_dir" ]; then
            mkdir -p "$model_dir"
            cd "$model_dir"
            
            log "Downloading ${model_type} model (this may take a while)..."
            
            # Try different URLs
            download_success=false
            for url in "$model_url" "${alternative_urls[@]}"; do
                log "Trying URL: $url"
                if curl -L -o model.zip "$url" 2>/dev/null; then
                    log "Successfully downloaded from: $url"
                    download_success=true
                    break
                else
                    log "Failed to download from: $url"
                fi
            done
            
            if [ "$download_success" = false ]; then
                warn "Failed to download ${model_type} model from all URLs"
                log "Please download manually from: https://alphacephei.com/vosk/models/"
                log "Or use a different ${model_type} model"
                return 1
            fi
            
            log "Extracting ${model_type} model..."
            
            # Handle both .zip and .tar.gz files
            if [[ "$model_url" == *.zip ]]; then
                unzip -q model.zip
                # Find the extracted directory
                extracted_dir=$(find . -maxdepth 1 -type d -name "vosk-model*" | head -1)
                if [ -n "$extracted_dir" ]; then
                    mv "$extracted_dir"/* .
                    rmdir "$extracted_dir"
                fi
            else
                tar -xzf model.zip
                # Find the extracted directory
                extracted_dir=$(find . -maxdepth 1 -type d -name "vosk-model*" | head -1)
                if [ -n "$extracted_dir" ]; then
                    mv "$extracted_dir"/* .
                    rmdir "$extracted_dir"
                fi
            fi
            
            rm model.zip
            
            cd ../..
            log "VOSK ${model_type} model downloaded and extracted"
        else
            log "VOSK ${model_type} model already exists"
        fi
    }
    
    # Download Czech model
    download_model "Czech" "$CZECH_MODEL_DIR" "$CZECH_MODEL_URL" "${CZECH_ALTERNATIVE_URLS[@]}"
    
    # Download English model
    download_model "English" "$ENGLISH_MODEL_DIR" "$ENGLISH_MODEL_URL" "${ENGLISH_ALTERNATIVE_URLS[@]}"
    
    log "All VOSK models downloaded successfully!"
}

# Test installation
test_installation() {
    log "Testing installation..."
    
    source venv/bin/activate
    
    # Test Python imports
    python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from core.config_manager import ConfigManager
    from core.audio_manager import AudioManager
    from core.voice_processor import VoiceProcessor
    from core.mqtt_client import MQTTClient
    from core.password_manager import PasswordManager
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
    
    if [ ! -f "config/passwords.txt" ]; then
        mkdir -p config
        cat > config/passwords.txt << EOF
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
    download_vosk_models
    create_sample_passwords
    
    # Test installation
    test_installation
    
    log "Setup completed successfully!"
    log ""
    log "Next steps:"
    log "1. Test the sound system:"
    log "   source venv/bin/activate"
    log "   python tests/test_sounds.py"
    log ""
    log "2. Run the voice recognizer:"
    log "   source venv/bin/activate"
    log "   python run_macos.py"
    log ""
    log "3. Edit config/config.yaml to customize settings"
    log "4. Edit config/passwords.txt to add your passwords"
}

# Run main function
main "$@" 