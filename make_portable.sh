#!/bin/bash

(
cd "$(dirname "$0")" || exit 1

# Ensure dist directory exists
mkdir -p dist

# Create venv if it doesn't exist
if [ ! -d "dist/python310" ]; then
    cp -r vendor/python-3.10.11-embed-amd64 dist/python310 &&

    dist/python310/python.exe vendor/get-pip.py &&
    echo "import site" >> dist/python310/python310._pth &&

    # Install dependencies
    dist/python310/python.exe -m pip install --upgrade pip &&
    dist/python310/python.exe -m pip install -r requirements.txt &&

    # 
    cp dist/python310/Lib/site-packages/openvr/libopenvr_api_64.dll dist/python310/libopenvr_api_64.dll &&
    
    echo "Successfully prepared python310"
else
  echo "Virtual environment already exists at dist/venv"
fi

# Copy scripts
cp -r scripts/* dist/
cp -r steam_vr_wheel dist/python310/

)
