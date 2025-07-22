#!/bin/bash

# Language Switch Script for Voice Recognition
# Switches between Czech and English VOSK models

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
CONFIG_FILE="config/config.yaml"
CZECH_MODEL_DIR="./models/vosk-model-cs"
ENGLISH_MODEL_DIR="./models/vosk-model-en"

check_model_exists() {
    local model_dir=$1
    local language=$2
    
    if [ -d "$model_dir" ] && [ "$(ls -A "$model_dir" 2>/dev/null)" ]; then
        log "✓ ${language} model found at: $model_dir"
        return 0
    else
        warn "✗ ${language} model not found at: $model_dir"
        return 1
    fi
}

switch_to_language() {
    local language=$1
    local model_dir=$2
    
    log "Switching to ${language} language..."
    
    # Check if model exists
    if ! check_model_exists "$model_dir" "$language"; then
        error "${language} model not found. Please run the download script first."
        return 1
    fi
    
    # Update config file
    if [ -f "$CONFIG_FILE" ]; then
        # Update language setting
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS version
            sed -i '' "s/language:.*/language: \"$language\"/g" "$CONFIG_FILE"
            sed -i '' "s/model_path:.*/model_path: \"\"/g" "$CONFIG_FILE"
        else
            # Linux version
            sed -i "s/language:.*/language: \"$language\"/g" "$CONFIG_FILE"
            sed -i "s/model_path:.*/model_path: \"\"/g" "$CONFIG_FILE"
        fi
        
        log "✓ Configuration updated to use ${language} language"
        log "✓ Model path set to auto-detect: $model_dir"
    else
        error "Configuration file not found: $CONFIG_FILE"
        return 1
    fi
}

show_current_language() {
    if [ -f "$CONFIG_FILE" ]; then
        current_lang=$(grep "language:" "$CONFIG_FILE" | head -1 | sed 's/.*language: *"\([^"]*\)".*/\1/')
        log "Current language setting: $current_lang"
        
        if [ "$current_lang" = "cs" ]; then
            check_model_exists "$CZECH_MODEL_DIR" "Czech"
        elif [ "$current_lang" = "en" ]; then
            check_model_exists "$ENGLISH_MODEL_DIR" "English"
        else
            warn "Unknown language setting: $current_lang"
        fi
    else
        error "Configuration file not found: $CONFIG_FILE"
    fi
}

download_missing_models() {
    log "Checking for missing models..."
    
    local need_download=false
    
    if ! check_model_exists "$CZECH_MODEL_DIR" "Czech"; then
        warn "Czech model missing"
        need_download=true
    fi
    
    if ! check_model_exists "$ENGLISH_MODEL_DIR" "English"; then
        warn "English model missing"
        need_download=true
    fi
    
    if [ "$need_download" = true ]; then
        log "Downloading missing models..."
        bash scripts/download_vosk_model.sh
    else
        log "✓ All models are available"
    fi
}

main() {
    echo "🌍 Voice Recognition Language Switcher"
    echo "====================================="
    
    case "${1:-}" in
        "cs"|"czech")
            switch_to_language "cs" "$CZECH_MODEL_DIR"
            ;;
        "en"|"english")
            switch_to_language "en" "$ENGLISH_MODEL_DIR"
            ;;
        "status"|"current")
            show_current_language
            ;;
        "download")
            download_missing_models
            ;;
        "help"|"-h"|"--help"|"")
            echo ""
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  cs, czech     Switch to Czech language"
            echo "  en, english   Switch to English language"
            echo "  status        Show current language setting"
            echo "  download      Download missing models"
            echo "  help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 cs         # Switch to Czech"
            echo "  $0 en         # Switch to English"
            echo "  $0 status     # Show current setting"
            echo "  $0 download   # Download missing models"
            echo ""
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
    
    echo ""
    echo "Next steps:"
    echo "1. Restart the voice recognizer to apply changes"
    echo "2. Test with the new language"
    echo "3. Update passwords.txt for the new language"
}

main "$@" 