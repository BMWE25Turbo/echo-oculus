#!/bin/bash

echo "Installing Echo Oculus..."

# Create project folder
mkdir -p ~/echo-oculus
cd ~/echo-oculus

# Download main files from GitHub repo (adjust YOUR_USERNAME and repo name)
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/main.py
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/config.yaml
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/utils.py
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/requirements.txt
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/modules/data_collector.py
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/modules/waze_scanner.py
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/modules/hot_zone_analytics.py
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/modules/manual_tagger.py
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/echo-oculus/main/modules/logger.py

# Install dependencies
pip install -r requirements.txt

# Start the system
python3 main.py
