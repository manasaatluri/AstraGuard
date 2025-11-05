# src/motion_sensor.py
try:
    from gpiozero import DigitalInputDevice # type: ignore
except Exception:
    DigitalInputDevice = None

class MotionSensor:
    def __init__(self, pin=17):
        self.pin = pin
        self.available = DigitalInputDevice is not None
        if self.available:
            try:
                self.dev = DigitalInputDevice(pin)
            except Exception:
                self.dev = None
                self.available = False
        else:
            self.dev = None

    def motion(self):
        if not self.available or not self.dev:
            # fallback: always True (poll camera)
            return True
        return bool(self.dev.value)

