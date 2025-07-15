#!/usr/bin/env python3
"""
Find and download a working Czech VOSK model
"""

import os
import sys
import requests
import subprocess
from pathlib import Path

def check_available_models():
    """Check what models are available on the VOSK website"""
    print("🔍 Checking available VOSK models...")
    
    try:
        # Try to get the models page
        response = requests.get("https://alphacephei.com/vosk/models", timeout=10)
        if response.status_code == 200:
            content = response.text
            # Look for Czech models
            if "cs" in content.lower():
                print("✅ Found Czech models on the website")
                return True
            else:
                print("❌ No Czech models found on the website")
                return False
    except Exception as e:
        print(f"❌ Error checking website: {e}")
        return False

def try_alternative_sources():
    """Try alternative sources for Czech models"""
    print("🔍 Trying alternative sources...")
    
    # Alternative URLs to try
    alternative_urls = [
        "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4-sphere.tar.gz",
        "https://alphacephei.com/vosk/models/vosk-model-small-cs-0.4.tar.gz",
        "https://alphacephei.com/vosk/models/vosk-model-cs-0.4.tar.gz",
        "https://alphacephei.com/vosk/models/vosk-model-cs-0.3.tar.gz",
        # Try different naming patterns
        "https://alphacephei.com/vosk/models/vosk-model-cs-small-0.4.tar.gz",
        "https://alphacephei.com/vosk/models/vosk-model-czech-0.4.tar.gz",
    ]
    
    for url in alternative_urls:
        print(f"🔗 Trying: {url}")
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ URL accessible: {url}")
                return url
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    return None

def download_from_url(url, filename):
    """Download model from URL"""
    print(f"📥 Downloading from: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def extract_model(filename):
    """Extract the downloaded model"""
    print(f"📦 Extracting: {filename}")
    
    try:
        # Extract the tar.gz file
        result = subprocess.run(['tar', '-xzf', filename], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Extraction successful")
            return True
        else:
            print(f"❌ Extraction failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return False

def setup_model():
    """Set up the model in the correct location"""
    print("🔧 Setting up model...")
    
    # Find the extracted directory
    extracted_dirs = [d for d in os.listdir('.') if d.startswith('vosk-model') and os.path.isdir(d)]
    
    if not extracted_dirs:
        print("❌ No extracted model directory found")
        return False
    
    model_dir = extracted_dirs[0]
    print(f"📁 Found model directory: {model_dir}")
    
    # Create target directory
    target_dir = "./vosk-model-cs"
    os.makedirs(target_dir, exist_ok=True)
    
    # Move files to target directory
    try:
        for item in os.listdir(model_dir):
            src = os.path.join(model_dir, item)
            dst = os.path.join(target_dir, item)
            if os.path.isfile(src):
                os.rename(src, dst)
            elif os.path.isdir(src):
                # Move directory contents
                for subitem in os.listdir(src):
                    sub_src = os.path.join(src, subitem)
                    sub_dst = os.path.join(target_dir, subitem)
                    os.rename(sub_src, sub_dst)
                os.rmdir(src)
        
        # Remove empty source directory
        os.rmdir(model_dir)
        
        print("✅ Model setup complete")
        return True
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

def main():
    """Main function"""
    print("🎯 VOSK Czech Model Finder")
    print("=" * 40)
    
    # Check if model already exists
    if os.path.exists("./vosk-model-cs") and len(os.listdir("./vosk-model-cs")) > 1:
        print("✅ VOSK model already exists")
        return True
    
    # Try to find a working URL
    working_url = try_alternative_sources()
    
    if not working_url:
        print("❌ No working URLs found")
        print("\n💡 Manual download options:")
        print("1. Visit: https://alphacephei.com/vosk/models")
        print("2. Look for Czech (cs) models")
        print("3. Download manually and extract to ./vosk-model-cs/")
        return False
    
    # Download the model
    filename = "vosk-model-cs.tar.gz"
    if not download_from_url(working_url, filename):
        return False
    
    # Extract the model
    if not extract_model(filename):
        return False
    
    # Set up the model
    if not setup_model():
        return False
    
    # Clean up
    if os.path.exists(filename):
        os.remove(filename)
    
    print("🎉 VOSK Czech model is ready!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 