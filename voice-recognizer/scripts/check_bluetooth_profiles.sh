#!/bin/bash

# Bluetooth Profile Checker
# Checks available profiles and their quality for connected devices

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

check_bluetooth_devices() {
    log "Checking Bluetooth devices..."
    
    # Get paired devices
    devices_output=$(bluetoothctl devices)
    if [ -z "$devices_output" ]; then
        warn "No paired devices found"
        return 1
    fi
    
    echo "$devices_output"
    echo ""
}

check_connected_device() {
    log "Checking connected device..."
    
    # Get connected device
    connected_output=$(bluetoothctl info | grep -E "(Device|Name|Connected|Paired|Trusted|Blocked)")
    if [ -z "$connected_output" ]; then
        warn "No connected device found"
        return 1
    fi
    
    echo "$connected_output"
    echo ""
}

check_audio_profiles() {
    log "Checking available audio profiles..."
    
    # Get PulseAudio cards
    cards_output=$(pactl list cards short)
    if [ -z "$cards_output" ]; then
        warn "No PulseAudio cards found"
        return 1
    fi
    
    echo "Available audio cards:"
    echo "$cards_output"
    echo ""
    
    # Find Bluetooth cards
    bluetooth_cards=$(echo "$cards_output" | grep "bluez_card")
    if [ -n "$bluetooth_cards" ]; then
        log "Found Bluetooth audio cards:"
        echo "$bluetooth_cards"
        echo ""
        
        # Check profiles for each Bluetooth card
        echo "$bluetooth_cards" | while read -r card; do
            card_name=$(echo "$card" | awk '{print $2}')
            log "Checking profiles for card: $card_name"
            
            # Get profiles for this card
            profiles_output=$(pactl list cards | grep -A 50 "Name: $card_name" | grep -A 20 "Profiles:" | grep -E "(Profile:|Active Profile:)")
            if [ -n "$profiles_output" ]; then
                echo "Profiles for $card_name:"
                echo "$profiles_output"
                echo ""
            fi
        done
    else
        warn "No Bluetooth audio cards found"
    fi
}

check_audio_sources() {
    log "Checking audio sources..."
    
    # Get PulseAudio sources
    sources_output=$(pactl list sources short)
    if [ -z "$sources_output" ]; then
        warn "No PulseAudio sources found"
        return 1
    fi
    
    echo "Available audio sources:"
    echo "$sources_output"
    echo ""
    
    # Find Bluetooth sources
    bluetooth_sources=$(echo "$sources_output" | grep "bluez_input")
    if [ -n "$bluetooth_sources" ]; then
        log "Found Bluetooth audio sources:"
        echo "$bluetooth_sources"
        echo ""
        
        # Check properties for each Bluetooth source
        echo "$bluetooth_sources" | while read -r source; do
            source_name=$(echo "$source" | awk '{print $2}')
            log "Checking properties for source: $source_name"
            
            # Get properties for this source
            properties_output=$(pactl list sources | grep -A 50 "Name: $source_name" | grep -E "(Description:|Sample Specification:|Channel Map:|Active Port:|Formats:|Properties:)")
            if [ -n "$properties_output" ]; then
                echo "Properties for $source_name:"
                echo "$properties_output"
                echo ""
            fi
        done
    else
        warn "No Bluetooth audio sources found"
    fi
}

check_audio_sinks() {
    log "Checking audio sinks..."
    
    # Get PulseAudio sinks
    sinks_output=$(pactl list sinks short)
    if [ -z "$sinks_output" ]; then
        warn "No PulseAudio sinks found"
        return 1
    fi
    
    echo "Available audio sinks:"
    echo "$sinks_output"
    echo ""
    
    # Find Bluetooth sinks
    bluetooth_sinks=$(echo "$sinks_output" | grep "bluez_sink")
    if [ -n "$bluetooth_sinks" ]; then
        log "Found Bluetooth audio sinks:"
        echo "$bluetooth_sinks"
        echo ""
        
        # Check properties for each Bluetooth sink
        echo "$bluetooth_sinks" | while read -r sink; do
            sink_name=$(echo "$sink" | awk '{print $2}')
            log "Checking properties for sink: $sink_name"
            
            # Get properties for this sink
            properties_output=$(pactl list sinks | grep -A 50 "Name: $sink_name" | grep -E "(Description:|Sample Specification:|Channel Map:|Active Port:|Formats:|Properties:)")
            if [ -n "$properties_output" ]; then
                echo "Properties for $sink_name:"
                echo "$properties_output"
                echo ""
            fi
        done
    else
        warn "No Bluetooth audio sinks found"
    fi
}

profile_quality_info() {
    log "Bluetooth Profile Quality Information:"
    echo ""
    echo "Common Bluetooth Audio Profiles:"
    echo "================================="
    echo ""
    echo "1. HSP (Headset Profile) - headset-head-unit"
    echo "   - Mono audio (1 channel)"
    echo "   - Low quality (8kHz, 64kbps)"
    echo "   - Good for voice calls"
    echo "   - Limited bandwidth"
    echo ""
    echo "2. HFP (Hands-Free Profile) - handsfree-hf"
    echo "   - Mono audio (1 channel)"
    echo "   - Better quality than HSP (8kHz-16kHz)"
    echo "   - Good for voice calls"
    echo "   - More features than HSP"
    echo ""
    echo "3. A2DP (Advanced Audio Distribution Profile) - a2dp-sink"
    echo "   - Stereo audio (2 channels)"
    echo "   - High quality (44.1kHz, 328kbps)"
    echo "   - Best for music and high-quality audio"
    echo "   - Limited to one-way audio (sink only)"
    echo ""
    echo "4. AVRCP (Audio/Video Remote Control Profile)"
    echo "   - Control profile (play/pause/volume)"
    echo "   - Works with A2DP"
    echo "   - No audio transmission"
    echo ""
    echo "5. HFP + A2DP (Dual Profile)"
    echo "   - Best of both worlds"
    echo "   - HFP for voice calls (bidirectional)"
    echo "   - A2DP for music (high quality, one-way)"
    echo "   - Automatic switching between profiles"
    echo ""
}

test_profile_switching() {
    log "Testing profile switching..."
    
    # Find Bluetooth card
    bluetooth_card=$(pactl list cards short | grep "bluez_card" | head -1 | awk '{print $2}')
    if [ -z "$bluetooth_card" ]; then
        warn "No Bluetooth card found"
        return 1
    fi
    
    log "Found Bluetooth card: $bluetooth_card"
    
    # Get available profiles
    profiles=$(pactl list cards | grep -A 50 "Name: $bluetooth_card" | grep -A 20 "Profiles:" | grep "Profile:" | awk '{print $2}')
    if [ -z "$profiles" ]; then
        warn "No profiles found for $bluetooth_card"
        return 1
    fi
    
    echo "Available profiles for $bluetooth_card:"
    echo "$profiles"
    echo ""
    
    # Test switching to each profile
    echo "$profiles" | while read -r profile; do
        if [ -n "$profile" ]; then
            log "Testing profile: $profile"
            
            # Switch to profile
            if pactl set-card-profile "$bluetooth_card" "$profile" 2>/dev/null; then
                echo "  ✓ Successfully switched to $profile"
                
                # Wait a moment for profile to activate
                sleep 2
                
                # Check if profile is active
                active_profile=$(pactl list cards | grep -A 50 "Name: $bluetooth_card" | grep "Active Profile:" | awk '{print $3}')
                if [ "$active_profile" = "$profile" ]; then
                    echo "  ✓ Profile $profile is now active"
                else
                    echo "  ⚠ Profile $profile is not active (current: $active_profile)"
                fi
            else
                echo "  ✗ Failed to switch to $profile"
            fi
            echo ""
        fi
    done
}

main() {
    echo "🔊 Bluetooth Profile Checker"
    echo "============================"
    echo ""
    
    # Check if bluetoothctl is available
    if ! command -v bluetoothctl &> /dev/null; then
        error "bluetoothctl not found"
        exit 1
    fi
    
    # Check if pactl is available
    if ! command -v pactl &> /dev/null; then
        error "pactl not found (PulseAudio not available)"
        exit 1
    fi
    
    # Run checks
    check_bluetooth_devices
    check_connected_device
    check_audio_profiles
    check_audio_sources
    check_audio_sinks
    profile_quality_info
    
    echo ""
    log "Profile switching test (this will temporarily change your audio setup):"
    read -p "Do you want to test profile switching? (y/N): " -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        test_profile_switching
    else
        log "Skipping profile switching test"
    fi
    
    echo ""
    log "Recommendations:"
    echo "1. For voice recognition: Use 'headset-head-unit' (HSP) - current setting"
    echo "2. For better voice quality: Try 'handsfree-hf' (HFP) if available"
    echo "3. For music: Use 'a2dp-sink' (A2DP) - but no microphone"
    echo "4. For best of both: Use dual profile setup (HFP + A2DP)"
    echo ""
    log "To change profile in the voice recognizer, edit the bluetooth_manager.py file"
}

main "$@" 