#!/usr/bin/env python3
"""
Check and download VOSK Czech model if needed
"""

import os
import sys
from pathlib import Path

def check_vosk_model():
    """Check if VOSK model exists and is valid"""
    model_path = "./vosk-model-cs"
    
    print("🔍 Checking VOSK model...")
    print(f"📁 Looking for model at: {os.path.abspath(model_path)}")
    
    if not os.path.exists(model_path):
        print("❌ VOSK model directory not found")
        return False
    
    # Check for required files
    required_files = ["am", "conf", "graph", "ivector", "rnnlm", "final.mdl"]
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(model_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ VOSK model found and appears valid")
    return True

def download_vosk_model():
    """Download VOSK model using the download script"""
    print("📥 Downloading VOSK model...")
    
    # Run the download script
    import subprocess
    result = subprocess.run(["./download_vosk_model.sh"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ VOSK model downloaded successfully")
        return True
    else:
        print("❌ Failed to download VOSK model")
        print("Error:", result.stderr)
        return False

def main():
    """Main function"""
    if check_vosk_model():
        print("🎉 VOSK model is ready!")
        return True
    else:
        print("\n📥 Model not found. Attempting to download...")
        if download_vosk_model():
            if check_vosk_model():
                print("🎉 VOSK model is now ready!")
                return True
        
        print("\n❌ Failed to set up VOSK model")
        print("Please run manually:")
        print("  ./download_vosk_model.sh")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 