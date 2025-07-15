#!/bin/bash

# Wrapper script to run VOSK test with virtual environment

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the test
python3 test_vosk.py 