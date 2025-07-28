#!/bin/bash
# Wrapper script to run proximity_led.py in virtual environment with sudo

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get the virtual environment paths
VENV_DIR="${SCRIPT_DIR}/venv"
VENV_PYTHON="${VENV_DIR}/bin/python3"
VENV_SITE_PACKAGES="${VENV_DIR}/lib/python3.11/site-packages"

# Activate virtual environment
source "${VENV_DIR}/bin/activate"

# Run with sudo using the virtual environment's Python
sudo PYTHONPATH="${VENV_SITE_PACKAGES}" "${VENV_PYTHON}" "${SCRIPT_DIR}/hardware/proximity_led.py" "$@" 