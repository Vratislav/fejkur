#!/bin/bash

echo "🔊 Bluetooth Profile Checker (macOS)"
echo "===================================="
echo

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking Bluetooth status..."

# Get Bluetooth controller info
echo "📱 Bluetooth Controller:"
system_profiler SPBluetoothDataType 2>/dev/null | grep -A 5 "Bluetooth Controller" | head -10

echo
echo "🔗 Connected Devices:"
system_profiler SPBluetoothDataType 2>/dev/null | grep -A 10 "Connected:" | head -15

echo
echo "🎧 Audio Devices:"
echo "Input devices:"
system_profiler SPAudioDataType 2>/dev/null | grep -A 3 -B 1 "Input" | grep -E "(Input|UGREEN)" | head -10

echo
echo "Output devices:"
system_profiler SPAudioDataType 2>/dev/null | grep -A 3 -B 1 "Output" | grep -E "(Output|UGREEN)" | head -10

echo
echo "🎵 Current Audio Settings:"
echo "Default input:"
osascript -e 'tell application "System Events" to get name of current input device' 2>/dev/null || echo "Could not get default input"

echo "Default output:"
osascript -e 'tell application "System Events" to get name of current output device' 2>/dev/null || echo "Could not get default output"

echo
echo "📊 Audio Device Details:"
# Get detailed audio device info
system_profiler SPAudioDataType 2>/dev/null | grep -A 20 "UGREEN" | head -20

echo
echo "💡 macOS Bluetooth Profile Notes:"
echo "- macOS automatically manages Bluetooth profiles"
echo "- Headset devices typically use HFP (Hands-Free Profile) for voice calls"
echo "- A2DP (Advanced Audio Distribution Profile) is used for music"
echo "- Profile switching happens automatically based on usage"
echo "- Manual profile control is limited on macOS"
echo
echo "🔧 To improve voice quality:"
echo "1. Ensure the device is set as default input for voice recognition"
echo "2. Check that the device supports HFP (Hands-Free Profile)"
echo "3. Consider using a dedicated USB microphone for better quality"
echo "4. The current setup should work well for voice recognition" 