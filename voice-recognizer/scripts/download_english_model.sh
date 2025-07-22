#!/bin/bash

echo "🔍 Downloading English VOSK Model for Testing"
echo "=============================================="

# Create model directory
mkdir -p vosk-model-en

echo "📥 Downloading English model for testing..."

# Try to download English model (usually more reliable)
ENGLISH_URLS=(
    "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.tar.gz"
    "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.tar.gz"
    "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15-sphere.tar.gz"
)

for url in "${ENGLISH_URLS[@]}"; do
    echo "🔗 Trying: $url"
    if curl -I "$url" >/dev/null 2>&1; then
        echo "✅ URL accessible, downloading..."
        curl -L -o vosk-model-en.tar.gz "$url"
        if [ $? -eq 0 ]; then
            echo "✅ Download successful!"
            break
        fi
    else
        echo "❌ URL not accessible"
    fi
done

# Extract if download was successful
if [ -f "vosk-model-en.tar.gz" ]; then
    echo "📦 Extracting model..."
    tar -xzf vosk-model-en.tar.gz
    
    # Find the extracted directory and move contents
    for dir in vosk-model-*; do
        if [ -d "$dir" ] && [ "$dir" != "vosk-model-en" ] && [ "$dir" != "vosk-model-cs" ]; then
            echo "📁 Found extracted directory: $dir"
            mv "$dir"/* vosk-model-en/ 2>/dev/null
            rmdir "$dir" 2>/dev/null
            break
        fi
    done
    
    # Clean up
    rm -f vosk-model-en.tar.gz
    
    echo "✅ Model extraction complete!"
    
    # Check if we have the required files
    required_files=("am" "conf" "graph" "ivector" "rnnlm" "final.mdl")
    missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -e "vosk-model-en/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        echo "✅ All required files present!"
        echo ""
        echo "💡 For Czech model, try these alternatives:"
        echo "1. Visit: https://alphacephei.com/vosk/models"
        echo "2. Look for Czech (cs) models"
        echo "3. Download manually and extract to ./vosk-model-cs/"
        echo ""
        echo "Alternative sources for Czech models:"
        echo "- GitHub: https://github.com/alphacep/vosk-api"
        echo "- Hugging Face: Search for 'vosk czech'"
        echo "- Try different model names: vosk-model-cs, vosk-model-czech, etc."
    else
        echo "❌ Missing files: ${missing_files[*]}"
    fi
else
    echo "❌ Failed to download English model"
fi 