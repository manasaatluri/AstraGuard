# src/inference.py
import time
import numpy as np
from PIL import Image # type: ignore
import os

try:
    from tflite_runtime.interpreter import Interpreter # type: ignore
except Exception:
    try:
        from tensorflow.lite.python.interpreter import Interpreter # type: ignore
    except Exception:
        raise RuntimeError("tflite runtime not available. Install tflite-runtime or tensorflow.")

class TFLiteModel:
    def __init__(self, model_path, labels_path=None, input_size=(224,224), use_float=False):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        self.interpreter = Interpreter(model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_size = tuple(input_size)
        self.use_float = use_float
        self.labels = []
        if labels_path and os.path.exists(labels_path):
            with open(labels_path, "r") as f:
                self.labels = [l.strip() for l in f.readlines() if l.strip()]

    def _preprocess(self, frame):
        img = Image.fromarray(frame[..., ::-1])  # BGR to RGB
        img = img.resize(self.input_size)
        arr = np.asarray(img)
        dtype = self.input_details[0]['dtype']
        if dtype == np.float32 or self.use_float:
            arr = arr.astype(np.float32) / 255.0
        else:
            arr = arr.astype(np.uint8)
        return np.expand_dims(arr, axis=0)

    def infer(self, frame):
        tensor = self._preprocess(frame)
        self.interpreter.set_tensor(self.input_details[0]['index'], tensor)
        t0 = time.time()
        self.interpreter.invoke()
        latency_ms = (time.time() - t0) * 1000.0
        outputs = [self.interpreter.get_tensor(o['index']) for o in self.output_details]

        # If single 2D array -> classifier
        if len(outputs) == 1 and outputs[0].ndim == 2:
            scores = outputs[0][0]
            best = int(np.argmax(scores))
            best_score = float(scores[best])
            label = self.labels[best] if best < len(self.labels) else str(best)
            return {'type':'classification', 'label':label, 'index':best, 'score':best_score, 'latency_ms':latency_ms}

        # Try heuristic for detection-style outputs
        scores, classes, boxes = None, None, None
        for out in outputs:
            if out.ndim == 2 and out.shape[1] == 4:
                # boxes candidate [1, N, 4] or [N,4]
                boxes = out[0] if out.shape[0] == 1 else out
            elif out.ndim == 2 or out.ndim == 1:
                flat = out.flatten()
                # scores likely floats 0-1
                if flat.size > 0 and np.all(flat >= 0.0) and np.all(flat <= 1.0):
                    if scores is None or flat.size > scores.size:
                        scores = flat
                else:
                    # possible classes
                    if np.all(np.equal(np.mod(flat,1),0)):
                        classes = flat.astype(int)

        if scores is not None:
            top_idx = int(np.argmax(scores))
            top_score = float(scores[top_idx])
            top_cls = int(classes[top_idx]) if classes is not None and top_idx < len(classes) else None
            top_label = self.labels[top_cls] if top_cls is not None and top_cls < len(self.labels) else (str(top_cls) if top_cls is not None else None)
            box = boxes[top_idx].tolist() if boxes is not None and top_idx < len(boxes) else None
            return {'type':'detection','label':top_label,'index':top_cls,'score':top_score,'box':box,'latency_ms':latency_ms}

        # fallback: raw
        return {'type':'raw','raw':outputs,'latency_ms':latency_ms}


class TemporalSmoother:
    def __init__(self, window_size=5, required_hits=3, target_label=None):
        self.window_size = int(window_size)
        self.required_hits = int(required_hits)
        self.target_label = target_label
        self.buffer = []

    def add(self, label):
        self.buffer.append(label)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

    def triggered(self):
        if not self.buffer:
            return False
        if self.target_label is None:
            hits = sum(1 for l in self.buffer if l is not None and l != 'none' and l != 'background')
        else:
            hits = sum(1 for l in self.buffer if l == self.target_label)
        return hits >= self.required_hits

    def reset(self):
        self.buffer = []
