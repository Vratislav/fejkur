#!/usr/bin/env python3
"""
Test script to verify installation of all dependencies.
Run this before using the main pupil detector.
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    try:
        if package_name:
            module = importlib.import_module(module_name, package_name)
        else:
            module = importlib.import_module(module_name)
        print(f"✓ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        return False

def test_opencv():
    """Test OpenCV installation and camera access."""
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
        
        # Test camera access
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✓ Camera access successful")
            cap.release()
            return True
        else:
            print("✗ Camera access failed")
            return False
    except Exception as e:
        print(f"✗ OpenCV test failed: {e}")
        return False

def test_pypupilext():
    """Test PyPupilEXT installation."""
    try:
        import pypupilext
        print("✓ PyPupilEXT imported successfully")
        
        # Test creating a detector
        detector = pypupilext.PuRe()
        print("✓ PyPupilEXT detector initialized successfully")
        return True
    except Exception as e:
        print(f"✗ PyPupilEXT test failed: {e}")
        return False

def main():
    """Run all installation tests."""
    print("Testing pupil detector installation...\n")
    
    tests = [
        ("numpy", test_import("numpy")),
        ("opencv-python", test_opencv()),
        ("PyPupilEXT", test_pypupilext()),
    ]
    
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print("="*50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! You can now run pupil_detector.py")
        print("\nTry running:")
        print("  python pupil_detector.py --debug")
    else:
        print("✗ Some tests failed. Please check the installation.")
        print("\nCommon solutions:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Check camera permissions on macOS")
        print("3. Ensure PyPupilEXT repository is accessible")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 