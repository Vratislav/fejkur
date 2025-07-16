#!/bin/bash

# Sync Voice Recognition Project to Raspberry Pi
# Usage: ./sync_to_pi.sh [pi-ip-address]

# Configuration
PI_USER="sluchatko"
PI_HOST="${1:-sluchatko.local}"
PI_PATH="/home/sluchatko/voice-recognizer"
LOCAL_PATH="."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Syncing voice recognition project to Raspberry Pi...${NC}"
echo "Host: $PI_USER@$PI_HOST"
echo "Path: $PI_PATH"
echo ""

# Check if rsync is available
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}Error: rsync is not installed. Please install it first.${NC}"
    exit 1
fi

# Test connection
echo -e "${YELLOW}Testing connection to Raspberry Pi...${NC}"
if ! ssh -o ConnectTimeout=5 "$PI_USER@$PI_HOST" "echo 'Connection successful'" &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Raspberry Pi at $PI_HOST${NC}"
    echo "Please check:"
    echo "1. Pi is powered on and connected to network"
    echo "2. SSH is enabled on Pi"
    echo "3. Hostname/IP address is correct"
    echo ""
    echo "Try: ssh $PI_USER@$PI_HOST"
    exit 1
fi

echo -e "${GREEN}Connection successful!${NC}"

# Create directory on Pi if it doesn't exist
echo -e "${YELLOW}Creating directory on Pi...${NC}"
ssh "$PI_USER@$PI_HOST" "mkdir -p $PI_PATH"

# Sync files
echo -e "${YELLOW}Syncing files...${NC}"
rsync -avz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='models/vosk-model-cs' \
    --exclude='sounds/*.mp3' \
    --exclude='sounds/*.wav' \
    --delete \
    "$LOCAL_PATH/" "$PI_USER@$PI_HOST:$PI_PATH/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Sync completed successfully!${NC}"
    
    # Optional: Restart service on Pi (if installed)
    echo -e "${YELLOW}Restarting voice-recognizer service...${NC}"
    if ssh "$PI_USER@$PI_HOST" "sudo systemctl is-active voice-recognizer" &> /dev/null; then
        ssh "$PI_USER@$PI_HOST" "sudo systemctl restart voice-recognizer"
        echo -e "${GREEN}Service restarted!${NC}"
    else
        echo -e "${YELLOW}Service not installed yet. Run install.sh on Pi first.${NC}"
    fi
    echo ""
    echo "To check service status:"
    echo "ssh $PI_USER@$PI_HOST 'sudo systemctl status voice-recognizer'"
    echo ""
    echo "To view logs:"
    echo "ssh $PI_USER@$PI_HOST 'sudo journalctl -u voice-recognizer -f'"
else
    echo -e "${RED}Sync failed!${NC}"
    exit 1
fi 