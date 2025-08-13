#!/bin/bash

# Script to automatically download the latest pupil measurement recording from Raspberry Pi

# Configuration
PI_HOST="fejkur@fejkur.local"
RECORDINGS_DIR="/home/fejkur/recordings"
LOCAL_DIR="./recordings"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Searching for latest pupil measurement recording...${NC}"

# Create local recordings directory if it doesn't exist
mkdir -p "$LOCAL_DIR"

# Find the latest recording file
LATEST_FILE=$(ssh "$PI_HOST" "ls -t $RECORDINGS_DIR/pupil_measurement_*.mp4 2>/dev/null | head -1")

if [ -z "$LATEST_FILE" ]; then
    echo -e "${RED}❌ No pupil measurement recordings found on Raspberry Pi${NC}"
    echo -e "${YELLOW}💡 Make sure the pupil measurement system has been running and created recordings${NC}"
    exit 1
fi

# Extract filename and timestamp
FILENAME=$(basename "$LATEST_FILE")
TIMESTAMP=$(echo "$FILENAME" | sed 's/pupil_measurement_\(.*\)\.mp4/\1/')

echo -e "${GREEN}✅ Found latest recording: $FILENAME${NC}"
echo -e "${BLUE}📅 Timestamp: $TIMESTAMP${NC}"

# Get file size on Pi
FILE_SIZE=$(ssh "$PI_HOST" "ls -lh $LATEST_FILE | awk '{print \$5}'")
echo -e "${BLUE}📏 File size: $FILE_SIZE${NC}"

# Download the file
LOCAL_FILE="$LOCAL_DIR/$FILENAME"
echo -e "${YELLOW}⬇️  Downloading to: $LOCAL_FILE${NC}"

if scp "$PI_HOST:$LATEST_FILE" "$LOCAL_FILE"; then
    echo -e "${GREEN}✅ Download completed successfully!${NC}"
    
    # Get local file size
    LOCAL_SIZE=$(ls -lh "$LOCAL_FILE" | awk '{print $5}')
    echo -e "${BLUE}📏 Downloaded size: $LOCAL_SIZE${NC}"
    
    # Show file details
    echo -e "${BLUE}📁 File location: $(pwd)/$LOCAL_FILE${NC}"
    
    # Check if file is playable
    if command -v ffprobe >/dev/null 2>&1; then
        DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$LOCAL_FILE" 2>/dev/null)
        if [ ! -z "$DURATION" ]; then
            echo -e "${BLUE}⏱️  Duration: ${DURATION}s${NC}"
        fi
    fi
    
    echo -e "${GREEN}🎉 Latest recording ready for analysis!${NC}"
    
else
    echo -e "${RED}❌ Download failed${NC}"
    exit 1
fi

# Optional: List other available recordings
echo -e "${YELLOW}📋 Other available recordings on Pi:${NC}"
ssh "$PI_HOST" "ls -lh $RECORDINGS_DIR/pupil_measurement_*.mp4 | tail -5" 2>/dev/null || echo "No additional recordings found"

echo -e "${BLUE}💡 To download a specific recording, use:${NC}"
echo -e "${YELLOW}   scp $PI_HOST:$RECORDINGS_DIR/pupil_measurement_YYYYMMDD_HHMMSS.mp4 ./${NC}" 