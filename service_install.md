Systemd service installation (recommended):

1. Create service file:
   sudo nano /etc/systemd/system/astraguard.service

Contents:
[Unit]
Description=AstraGuard AI service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/AstraGuard-AI/src
ExecStart=/usr/bin/python3 /home/pi/AstraGuard-AI/src/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

2. Enable and start:
   sudo systemctl daemon-reload
   sudo systemctl enable astraguard.service
   sudo systemctl start astraguard.service
   sudo journalctl -u astraguard.service -f
