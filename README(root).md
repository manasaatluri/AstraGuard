# AstraGuard-AI

Edge AI wildlife intrusion detection system for farms — Raspberry Pi + Edge Impulse model.

## Quick Start

1. Put `ei_model.tflite` in `models/`.
2. Edit `models/labels.txt` to match model classes.
3. Install dependencies:
   ```bash
   sudo apt update && sudo apt install -y python3-pip
   python3 -m pip install --user -r requirements.txt
