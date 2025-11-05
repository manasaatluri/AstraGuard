# src/utils.py
import os
import time
from datetime import datetime

def timestamp():
    return datetime.utcnow().isoformat()

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def safe_write_text(path, text):
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(text)

