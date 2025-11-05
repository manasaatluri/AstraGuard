# src/main.py
import os
import time
import csv
from datetime import datetime
import yaml # type: ignore

# local imports
from camera_stream import CameraStream
from inference import TFLiteModel, TemporalSmoother
from motion_sensor import MotionSensor
from alert_system import Buzzer, TelegramNotifier, save_snapshot

# ---------------- CONFIG ----------------
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE, "models")
LOG_DIR = os.path.join(BASE, "data", "logs")
SNAPSHOT_DIR = os.path.join(BASE, "snapshots")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

CONFIG = {
    'MODEL_PATH': os.path.join(MODELS_DIR, "ei_model.tflite"),
    'LABELS_PATH': os.path.join(MODELS_DIR, "labels.txt"),
    'INPUT_SIZE': (224,224),
    'USE_FLOAT': False,
    'CAMERA_SRC': 0,
    'CAMERA_WIDTH': 640,
    'CAMERA_HEIGHT': 480,
    'USE_PICAMERA': False,
    'PIR_PIN': 17,
    'BUZZER_PIN': 27,
    'CONFIDENCE_THRESHOLD': 0.6,
    'SMOOTHER_WINDOW': 5,
    'SMOOTHER_HITS': 3,
    'ALERT_COOLDOWN': 40,
    'TELEGRAM_BOT_TOKEN': None,
    'TELEGRAM_CHAT_ID': None,
    'LOG_CSV': os.path.join(LOG_DIR, "detection_log.csv"),
}

# allow config.yaml override at repo root
CFG_PATH = os.path.join(os.path.dirname(BASE), "config.yaml")
if os.path.exists(CFG_PATH):
    with open(CFG_PATH,"r") as f:
        user_cfg = yaml.safe_load(f)
    if isinstance(user_cfg, dict):
        CONFIG.update(user_cfg)

# ---------------- INIT ----------------
print("AstraGuard AI starting. Config:")
for k,v in CONFIG.items():
    if k.startswith("TELEGRAM"): v = "REDACTED" if v else v
    print(f"  {k}: {v}")

# model
model = TFLiteModel(CONFIG['MODEL_PATH'], labels_path=CONFIG['LABELS_PATH'], input_size=CONFIG['INPUT_SIZE'], use_float=CONFIG['USE_FLOAT'])
smoother = TemporalSmoother(window_size=CONFIG['SMOOTHER_WINDOW'], required_hits=CONFIG['SMOOTHER_HITS'])

# camera
cam = CameraStream(src=CONFIG['CAMERA_SRC'], width=CONFIG['CAMERA_WIDTH'], height=CONFIG['CAMERA_HEIGHT'], use_picamera=CONFIG['USE_PICAMERA'])

# sensors / actuators
motion = MotionSensor(pin=CONFIG['PIR_PIN'])
buzzer = Buzzer(pin=CONFIG['BUZZER_PIN'])
notifier = TelegramNotifier(bot_token=CONFIG['TELEGRAM_BOT_TOKEN'], chat_id=CONFIG['TELEGRAM_CHAT_ID'])

last_alert_time = 0.0

def log_csv(timestamp, label, score, img_path):
    exists = os.path.exists(CONFIG['LOG_CSV'])
    with open(CONFIG['LOG_CSV'], 'a', newline='') as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(['timestamp','label','score','image'])
        w.writerow([timestamp, label, f"{score:.4f}", img_path])

def main_loop():
    global last_alert_time
    print("Entering main loop. Ctrl-C to stop.")
    try:
        while True:
            has_motion = motion.motion()
            if not has_motion:
                time.sleep(0.2)
                continue

            # collect frames
            frames = []
            for _ in range(CONFIG['SMOOTHER_WINDOW']):
                ok, frm = cam.read()
                if not ok:
                    break
                frames.append(frm)
                time.sleep(0.12)

            if not frames:
                time.sleep(0.5)
                continue

            best_label = None
            best_score = 0.0
            # inference loop
            for f in frames:
                r = model.infer(f)
                lbl = None
                score = 0.0
                if r['type'] == 'classification' or r['type'] == 'detection':
                    lbl = r.get('label')
                    score = r.get('score', 0.0)
                # add only if above confidence threshold
                if score >= CONFIG['CONFIDENCE_THRESHOLD']:
                    smoother.add(lbl)
                else:
                    smoother.add(None)
                if score > best_score:
                    best_score = score
                    best_label = lbl

            if smoother.triggered():
                now = time.time()
                if now - last_alert_time < CONFIG['ALERT_COOLDOWN']:
                    print("Alert suppressed by cooldown.")
                    smoother.reset()
                else:
                    ts = datetime.utcnow().isoformat()
                    snap = frames[-1]
                    img_path = save_snapshot(snap, prefix="alert")
                    print(f"[ALERT] {best_label} {best_score:.2f} -> {img_path}")
                    # act
                    buzzer.buzz(0.5)
                    log_csv(ts, best_label or "unknown", best_score or 0.0, img_path)
                    if notifier.base:
                        try:
                            notifier.send_photo(img_path, caption=f"AstraGuard: {best_label} ({best_score:.2f}) @ {ts}")
                        except Exception as e:
                            print("Notifier failed:", e)
                    last_alert_time = now
                    smoother.reset()
            else:
                print("No sustained detection (smoother)")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        print("Cleaning up camera.")
        cam.release()

if __name__ == "__main__":
    main_loop()
