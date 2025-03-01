#!/bin/bash

# Enable strict error handling
set -e

cd "$(dirname "$0")" || exit 1

# Ensure dist directory exists
mkdir -p dist

# Create venv if it doesn't exist
if [ ! -d "dist/python310" ]; then
    cp -r vendor/python-3.10.11-embed-amd64 dist/python310

    dist/python310/python.exe vendor/get-pip.py
    echo "import site" >> dist/python310/python310._pth

    # Install dependencies
    dist/python310/python.exe -m pip install --upgrade pip
    dist/python310/python.exe -m pip install -r requirements.txt

    # 
    cp dist/python310/Lib/site-packages/openvr/libopenvr_api_64.dll dist/python310/libopenvr_api_64.dll
    
    echo "Successfully prepared python310"
else
    echo "python310 already exists"
fi

# Copy scripts
cp -r scripts/* dist/
cp -r steam_vr_wheel dist/python310/
echo "Copied all scripts"

# Copy vendor

## ETS 2
ETS2_DIR="dist/Euro Truck Simulator 2/bin/win_x64/plugins"
if [ ! -d "$ETS2_DIR" ]; then
    ETS2_PV="release_v_1_12_1" # plugin version
    mkdir -p "$ETS2_DIR"
    cp "vendor/github.com/RenCloud/scs-sdk-plugin/$ETS2_PV.zip" "$ETS2_DIR"
    unzip -d "$ETS2_DIR" "$ETS2_DIR/$ETS2_PV.zip"
    cp "$ETS2_DIR/$ETS2_PV/Win64/scs-telemetry.dll" "$ETS2_DIR"
    echo "Copied ETS2 plugin files"
fi