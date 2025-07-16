#!/bin/bash

# Manual VOSK Model Download Script
# Downloads Czech and English VOSK models

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

# Configuration
CZECH_MODEL_DIR="./models/vosk-model-cs"
ENGLISH_MODEL_DIR="./models/vosk-model-en"
DOWNLOAD_DIR="./downloads"

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
            if wget -O model.zip "$url" 2>/dev/null; then
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

# Create download directory
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

log "Starting VOSK model downloads..."

# Download Czech model
download_model "Czech" "$CZECH_MODEL_DIR" "$CZECH_MODEL_URL" "${CZECH_ALTERNATIVE_URLS[@]}"

# Download English model
download_model "English" "$ENGLISH_MODEL_DIR" "$ENGLISH_MODEL_URL" "${ENGLISH_ALTERNATIVE_URLS[@]}"

log "All VOSK models downloaded and extracted successfully!"

# Update config.yaml if it exists
if [ -f "../config/config.yaml" ]; then
    log "Updating config/config.yaml with model paths..."
    sed -i "s|model_path:.*|model_path: \"$(pwd)/$CZECH_MODEL_DIR\"|g" ../config/config.yaml
    log "Config updated!"
fi

echo ""
echo "Next steps:"
echo "1. Update config/config.yaml if needed"
echo "2. Set 'language' to 'cs' for Czech or 'en' for English in config"
echo "3. Run the installation script"
echo "4. Test the voice recognition system" 