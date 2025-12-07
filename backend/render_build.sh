#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Dependencies..."
pip install -r requirements.txt

echo "Fixing OpenCV for Render Environment..."
# Uninstall opencv-contrib-python which forces libGL dependency
pip uninstall -y opencv-contrib-python
# Ensure headless version is present
pip install opencv-python-headless

echo "Build Completed Successfully."
