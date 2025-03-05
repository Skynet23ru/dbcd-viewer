#!/bin/bash

echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Building executable..."
pyinstaller --name="DBCD Viewer" \
            --windowed \
            --icon=DBCD/icons/app_icon.icns \
            --add-data="README.md:." \
            --noconsole \
            --clean \
            main.py

echo "Build complete!"
echo "Application bundle can be found in dist/DBCD Viewer.app/" 