#!/usr/bin/env python3
"""
Setup script for pupil detector installation.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"✗ Python {version.major}.{version.minor} is not supported. Please use Python 3.7 or higher.")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling Python dependencies...")
    
    # Upgrade pip first
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def test_installation():
    """Test the installation."""
    print("\nTesting installation...")
    return run_command("python test_installation.py", "Running installation tests")

def main():
    """Main setup function."""
    print("Setting up Pupil Detector...")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n✗ Installation failed. Please check the errors above.")
        return False
    
    # Test installation
    if not test_installation():
        print("\n✗ Installation test failed. Please check the errors above.")
        return False
    
    print("\n" + "="*50)
    print("✓ Setup completed successfully!")
    print("\nYou can now run the pupil detector:")
    print("  python pupil_detector.py --debug")
    print("\nFor help:")
    print("  python pupil_detector.py --help")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 