# src/camera_stream.py
import cv2 # type: ignore
import time
try:
    from picamera import PiCamera # type: ignore
    from picamera.array import PiRGBArray # type: ignore
    PICAMERA_AVAILABLE = True
except Exception:
    PICAMERA_AVAILABLE = False

class CameraStream:
    def __init__(self, src=0, width=640, height=480, use_picamera=False):
        self.width = width
        self.height = height
        self.use_picamera = use_picamera and PICAMERA_AVAILABLE
        self.vcap = None
        self.picam = None
        self.picam_raw = None

        if self.use_picamera:
            self.picam = PiCamera()
            self.picam.resolution = (width, height)
            self.picam.framerate = 24
            self.picam_raw = PiRGBArray(self.picam, size=(width, height))
            time.sleep(0.2)
            print("CameraStream: Using PiCamera")
        else:
            self.vcap = cv2.VideoCapture(src)
            self.vcap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            if not self.vcap.isOpened():
                raise RuntimeError(f"Unable to open camera (src={src}).")
            print("CameraStream: OpenCV camera opened.")

    def read(self):
        if self.use_picamera and self.picam is not None:
            self.picam.capture(self.picam_raw, format="bgr", use_video_port=True)
            frame = self.picam_raw.array
            self.picam_raw.truncate(0)
            return True, frame
        else:
            return self.vcap.read()

    def release(self):
        if self.picam:
            self.picam.close()
        if self.vcap:
            self.vcap.release()
