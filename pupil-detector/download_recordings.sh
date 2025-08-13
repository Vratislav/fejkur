#!/bin/bash

# Advanced script to download pupil measurement recordings from Raspberry Pi

# Configuration
PI_HOST="fejkur@fejkur.local"
RECORDINGS_DIR="/home/fejkur/recordings"
LOCAL_DIR="./recordings"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    echo -e "${BLUE}📖 Usage:${NC}"
    echo -e "${YELLOW}  $0 [OPTION]${NC}"
    echo ""
    echo -e "${BLUE}Options:${NC}"
    echo -e "${YELLOW}  latest${NC}     - Download the latest recording (default)"
    echo -e "${YELLOW}  list${NC}       - List all available recordings"
    echo -e "${YELLOW}  all${NC}        - Download all recordings"
    echo -e "${YELLOW}  recent N${NC}    - Download the N most recent recordings"
    echo -e "${YELLOW}  specific FILE${NC} - Download a specific recording file"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo -e "${YELLOW}  $0${NC}                    # Download latest"
    echo -e "${YELLOW}  $0 latest${NC}             # Download latest"
    echo -e "${YELLOW}  $0 list${NC}               # List all recordings"
    echo -e "${YELLOW}  $0 all${NC}                # Download all recordings"
    echo -e "${YELLOW}  $0 recent 3${NC}           # Download 3 most recent"
    echo -e "${YELLOW}  $0 specific pupil_measurement_20250731_012757.mp4${NC}"
}

# Function to download a single file
download_file() {
    local remote_file="$1"
    local local_file="$2"
    
    echo -e "${YELLOW}⬇️  Downloading: $(basename "$remote_file")${NC}"
    
    if scp "$PI_HOST:$remote_file" "$local_file" 2>/dev/null; then
        local size=$(ls -lh "$local_file" | awk '{print $5}')
        echo -e "${GREEN}✅ Downloaded: $(basename "$local_file") ($size)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to download: $(basename "$remote_file")${NC}"
        return 1
    fi
}

# Function to get file info
get_file_info() {
    local file="$1"
    local size=$(ssh "$PI_HOST" "ls -lh $file 2>/dev/null | awk '{print \$5}'")
    local date=$(ssh "$PI_HOST" "ls -l $file 2>/dev/null | awk '{print \$6, \$7, \$8}'")
    echo "$size|$date"
}

# Main script logic
case "${1:-latest}" in
    "latest")
        echo -e "${BLUE}🔍 Finding latest recording...${NC}"
        
        # Create local directory
        mkdir -p "$LOCAL_DIR"
        
        # Find latest file
        LATEST_FILE=$(ssh "$PI_HOST" "ls -t $RECORDINGS_DIR/pupil_measurement_*.mp4 2>/dev/null | head -1")
        
        if [ -z "$LATEST_FILE" ]; then
            echo -e "${RED}❌ No recordings found${NC}"
            exit 1
        fi
        
        FILENAME=$(basename "$LATEST_FILE")
        LOCAL_FILE="$LOCAL_DIR/$FILENAME"
        
        # Get file info
        FILE_INFO=$(get_file_info "$LATEST_FILE")
        FILE_SIZE=$(echo "$FILE_INFO" | cut -d'|' -f1)
        FILE_DATE=$(echo "$FILE_INFO" | cut -d'|' -f2-)
        
        echo -e "${GREEN}✅ Found: $FILENAME${NC}"
        echo -e "${BLUE}📏 Size: $FILE_SIZE${NC}"
        echo -e "${BLUE}📅 Date: $FILE_DATE${NC}"
        
        # Download
        if download_file "$LATEST_FILE" "$LOCAL_FILE"; then
            echo -e "${GREEN}🎉 Latest recording ready!${NC}"
        fi
        ;;
        
    "list")
        echo -e "${BLUE}📋 Available recordings on Raspberry Pi:${NC}"
        echo ""
        
        # Get all recordings with details
        ssh "$PI_HOST" "ls -lh $RECORDINGS_DIR/pupil_measurement_*.mp4 2>/dev/null" | while read line; do
            if [[ $line == *"pupil_measurement_"* ]]; then
                filename=$(echo "$line" | awk '{print $9}')
                size=$(echo "$line" | awk '{print $5}')
                date=$(echo "$line" | awk '{print $6, $7, $8}')
                echo -e "${GREEN}📹 $filename${NC}"
                echo -e "${BLUE}   📏 Size: $size | 📅 Date: $date${NC}"
                echo ""
            fi
        done
        
        # Count total files
        TOTAL=$(ssh "$PI_HOST" "ls $RECORDINGS_DIR/pupil_measurement_*.mp4 2>/dev/null | wc -l")
        echo -e "${PURPLE}📊 Total recordings: $TOTAL${NC}"
        ;;
        
    "all")
        echo -e "${BLUE}📥 Downloading all recordings...${NC}"
        
        mkdir -p "$LOCAL_DIR"
        
        # Get list of all files
        FILES=$(ssh "$PI_HOST" "ls $RECORDINGS_DIR/pupil_measurement_*.mp4 2>/dev/null")
        
        if [ -z "$FILES" ]; then
            echo -e "${RED}❌ No recordings found${NC}"
            exit 1
        fi
        
        COUNT=0
        SUCCESS=0
        
        for file in $FILES; do
            COUNT=$((COUNT + 1))
            filename=$(basename "$file")
            local_file="$LOCAL_DIR/$filename"
            
            if download_file "$file" "$local_file"; then
                SUCCESS=$((SUCCESS + 1))
            fi
        done
        
        echo -e "${GREEN}🎉 Downloaded $SUCCESS/$COUNT recordings successfully!${NC}"
        ;;
        
    "recent")
        if [ -z "$2" ] || ! [[ "$2" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}❌ Please specify number of recent recordings to download${NC}"
            echo -e "${YELLOW}Example: $0 recent 5${NC}"
            exit 1
        fi
        
        N="$2"
        echo -e "${BLUE}📥 Downloading $N most recent recordings...${NC}"
        
        mkdir -p "$LOCAL_DIR"
        
        # Get N most recent files
        FILES=$(ssh "$PI_HOST" "ls -t $RECORDINGS_DIR/pupil_measurement_*.mp4 2>/dev/null | head -$N")
        
        if [ -z "$FILES" ]; then
            echo -e "${RED}❌ No recordings found${NC}"
            exit 1
        fi
        
        COUNT=0
        SUCCESS=0
        
        for file in $FILES; do
            COUNT=$((COUNT + 1))
            filename=$(basename "$file")
            local_file="$LOCAL_DIR/$filename"
            
            echo -e "${BLUE}📥 [$COUNT/$N] Downloading: $filename${NC}"
            
            if download_file "$file" "$local_file"; then
                SUCCESS=$((SUCCESS + 1))
            fi
        done
        
        echo -e "${GREEN}🎉 Downloaded $SUCCESS/$COUNT recent recordings!${NC}"
        ;;
        
    "specific")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify filename to download${NC}"
            echo -e "${YELLOW}Example: $0 specific pupil_measurement_20250731_012757.mp4${NC}"
            exit 1
        fi
        
        FILENAME="$2"
        REMOTE_FILE="$RECORDINGS_DIR/$FILENAME"
        LOCAL_FILE="$LOCAL_DIR/$FILENAME"
        
        echo -e "${BLUE}📥 Downloading specific file: $FILENAME${NC}"
        
        # Check if file exists
        if ! ssh "$PI_HOST" "test -f $REMOTE_FILE" 2>/dev/null; then
            echo -e "${RED}❌ File not found: $FILENAME${NC}"
            echo -e "${YELLOW}💡 Use '$0 list' to see available files${NC}"
            exit 1
        fi
        
        mkdir -p "$LOCAL_DIR"
        
        if download_file "$REMOTE_FILE" "$LOCAL_FILE"; then
            echo -e "${GREEN}🎉 Specific recording downloaded!${NC}"
        fi
        ;;
        
    "help"|"-h"|"--help")
        show_usage
        ;;
        
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        show_usage
        exit 1
        ;;
esac 