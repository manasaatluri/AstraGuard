#!/bin/bash
# run_on_boot.sh - simple wrapper to start the app at boot
# place this in /home/pi/AstraGuard-AI/startup/run_on_boot.sh and make executable

# Activate virtualenv if used
# source /home/pi/venv/bin/activate

# Change to project dir
cd /home/pi/AstraGuard-AI/src
# Keep log
/usr/bin/python3 main.py >> /home/pi/AstraGuard-AI/logs/astraguard.log 2>&1 &
