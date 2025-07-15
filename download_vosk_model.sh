#!/bin/bash

# Manual VOSK Czech Model Download Script
# This script tries multiple URLs to download the Czech VOSK model

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
MODEL_DIR="./vosk-model-cs"
DOWNLOAD_DIR="./downloads"

# Available Czech model URLs (from https://alphacephei.com/vosk/models/)
MODEL_URLS=(
    "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4-sphere.tar.gz"
    "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4.tar.gz"
    "https://alphacephei.com/vosk/models/vosk-model-cs-0.4.tar.gz"
    "https://alphacephei.com/vosk/models/vosk-model-cs-0.3.tar.gz"
)

# Create download directory
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

log "Starting VOSK Czech model download..."

# Try each URL
download_success=false
for url in "${MODEL_URLS[@]}"; do
    log "Trying URL: $url"
    
    # Extract filename from URL
    filename=$(basename "$url")
    
    # Try to download
    if wget --timeout=30 --tries=3 -O "$filename" "$url" 2>/dev/null; then
        log "Successfully downloaded: $filename"
        download_success=true
        break
    else
        warn "Failed to download from: $url"
    fi
done

if [ "$download_success" = false ]; then
    error "Failed to download VOSK model from all URLs"
    echo ""
    echo "Manual download options:"
    echo "1. Visit: https://alphacephei.com/vosk/models/"
    echo "2. Look for Czech models (cs)"
    echo "3. Download and extract to: $MODEL_DIR"
    echo ""
    echo "Alternative models you can try:"
    echo "- vosk-model-small-cs-0.4-sphere.tar.gz"
    echo "- vosk-model-small-cs-0.4.tar.gz"
    echo "- vosk-model-cs-0.4.tar.gz"
    echo "- vosk-model-cs-0.3.tar.gz"
    exit 1
fi

# Extract the model
log "Extracting model..."
tar -xzf "$filename"

# Find the extracted directory
extracted_dir=$(find . -maxdepth 1 -type d -name "vosk-model*" | head -1)

if [ -z "$extracted_dir" ]; then
    error "Could not find extracted model directory"
    exit 1
fi

# Move to final location
log "Moving model to: $MODEL_DIR"
mkdir -p "$MODEL_DIR"
mv "$extracted_dir"/* "$MODEL_DIR/"
rmdir "$extracted_dir"

# Clean up
rm -f "$filename"

log "VOSK Czech model downloaded and extracted successfully!"
log "Model location: $MODEL_DIR"

# Update config.yaml if it exists
if [ -f "../config.yaml" ]; then
    log "Updating config.yaml with model path..."
    sed -i "s|model_path:.*|model_path: \"$(pwd)/$MODEL_DIR\"|g" ../config.yaml
    log "Config updated!"
fi

echo ""
echo "Next steps:"
echo "1. Update config.yaml if needed"
echo "2. Run the installation script"
echo "3. Test the voice recognition system" 