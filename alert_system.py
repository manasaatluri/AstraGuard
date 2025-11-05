# src/alert_system.py
import os
import time
import requests # type: ignore
from .utils import ensure_dir # type: ignore
try:
    from gpiozero import OutputDevice # type: ignore
except Exception:
    OutputDevice = None

SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "snapshots")
ensure_dir = lambda p: os.makedirs(p, exist_ok=True)
ensure_dir(SNAPSHOT_DIR)

class Buzzer:
    def __init__(self, pin=27):
        self.pin = pin
        self.available = OutputDevice is not None
        if self.available:
            try:
                self.dev = OutputDevice(pin)
            except Exception:
                self.dev = None
                self.available = False
        else:
            self.dev = None

    def buzz(self, duration=0.5):
        if self.available and self.dev:
            self.dev.on()
            time.sleep(duration)
            self.dev.off()
        else:
            print("[Buzzer] simulated beep for", duration, "s")

class TelegramNotifier:
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base = None
        if bot_token and chat_id:
            self.base = f"https://api.telegram.org/bot{bot_token}"

    def send_text(self, text):
        if not self.base:
            print("[Telegram] would send:", text)
            return None
        try:
            url = self.base + "/sendMessage"
            r = requests.post(url, data={'chat_id': self.chat_id, 'text': text}, timeout=10)
            return r
        except Exception as e:
            print("Telegram send error:", e)
            return None

    def send_photo(self, image_path, caption="AstraGuard Alert"):
        if not self.base:
            print("[Telegram] would send photo:", image_path, caption)
            return None
        try:
            url = self.base + "/sendPhoto"
            with open(image_path, 'rb') as f:
                files = {'photo': f}
                data = {'chat_id': self.chat_id, 'caption': caption}
                r = requests.post(url, files=files, data=data, timeout=30)
                return r
        except Exception as e:
            print("Telegram photo send error:", e)
            return None

def save_snapshot(frame, prefix="snap"):
    import cv2, time, os # type: ignore
    SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "snapshots")
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    ts = int(time.time())
    p = os.path.join(SNAPSHOT_DIR, f"{prefix}_{ts}.jpg")
    cv2.imwrite(p, frame)
    return p

