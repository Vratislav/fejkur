#!/bin/bash

echo "🔍 Manual VOSK Czech Model Download"
echo "===================================="

# Create model directory
mkdir -p vosk-model-cs

# Try different approaches
echo "📥 Attempting to download Czech model..."

# Method 1: Try wget with different URLs
echo "🔗 Method 1: Direct download attempts..."

# Try different known Czech model URLs
URLS=(
    "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4-sphere.tar.gz"
    "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4.tar.gz"
    "https://alphacephei.com/vosk/models/vosk-model-cs-0.4.tar.gz"
    "https://alphacephei.com/vosk/models/vosk-model-cs-0.3.tar.gz"
)

for url in "${URLS[@]}"; do
    echo "🔗 Trying: $url"
    if wget --spider "$url" 2>/dev/null; then
        echo "✅ URL accessible, downloading..."
        wget -O vosk-model-cs.tar.gz "$url"
        if [ $? -eq 0 ]; then
            echo "✅ Download successful!"
            break
        fi
    else
        echo "❌ URL not accessible"
    fi
done

# Method 2: Try curl
if [ ! -f "vosk-model-cs.tar.gz" ]; then
    echo "🔗 Method 2: Using curl..."
    for url in "${URLS[@]}"; do
        echo "🔗 Trying: $url"
        if curl -I "$url" >/dev/null 2>&1; then
            echo "✅ URL accessible, downloading..."
            curl -L -o vosk-model-cs.tar.gz "$url"
            if [ $? -eq 0 ]; then
                echo "✅ Download successful!"
                break
            fi
        else
            echo "❌ URL not accessible"
        fi
    done
fi

# Extract if download was successful
if [ -f "vosk-model-cs.tar.gz" ]; then
    echo "📦 Extracting model..."
    tar -xzf vosk-model-cs.tar.gz
    
    # Find the extracted directory and move contents
    for dir in vosk-model-*; do
        if [ -d "$dir" ] && [ "$dir" != "vosk-model-cs" ]; then
            echo "📁 Found extracted directory: $dir"
            mv "$dir"/* vosk-model-cs/ 2>/dev/null
            rmdir "$dir" 2>/dev/null
            break
        fi
    done
    
    # Clean up
    rm -f vosk-model-cs.tar.gz
    
    echo "✅ Model extraction complete!"
    
    # Check if we have the required files
    required_files=("am" "conf" "graph" "ivector" "rnnlm" "final.mdl")
    missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -e "vosk-model-cs/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        echo "✅ All required files present!"
    else
        echo "❌ Missing files: ${missing_files[*]}"
    fi
else
    echo "❌ Failed to download model"
    echo ""
    echo "💡 Manual download instructions:"
    echo "1. Visit: https://alphacephei.com/vosk/models"
    echo "2. Look for Czech (cs) models"
    echo "3. Download the model file"
    echo "4. Extract it to ./vosk-model-cs/"
    echo ""
    echo "Alternative sources:"
    echo "- GitHub: https://github.com/alphacep/vosk-api"
    echo "- Hugging Face: Search for 'vosk czech'"
fi 