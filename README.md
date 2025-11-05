Optional lightweight Flask or FastAPI service that accepts incoming detections and forwards to mobile app.
E.g. POST /alert { label,score,timestamp, image_url }.
Not strictly required when using Telegram.
