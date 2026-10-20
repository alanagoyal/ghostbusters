#!/bin/bash
# Run from the normal checkout owner's account using sudo.
set -euo pipefail
if [[ ${EUID} -ne 0 || -z ${SUDO_USER:-} || ${SUDO_USER} == root ]]; then
    echo "Run as your normal account: sudo ./setup-service.sh" >&2
    exit 1
fi
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Keep generated systemd paths unambiguous (including its % specifiers).
if [[ "$project_dir" == *[[:space:]%\"\\]* ]]; then
    echo "Move the checkout to a path without whitespace, %, quotes or backslashes." >&2
    exit 1
fi
python_bin="$project_dir/.venv/bin/python"
if [[ ! -x "$python_bin" || ! -f "$project_dir/.env" ]]; then
    echo "Run uv sync and configure .env in the checkout first." >&2
    exit 1
fi
cat > /etc/systemd/system/costume-detector.service <<SERVICE
[Unit]
Description=Halloween Costume Detector
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$project_dir
Environment=PYTHONUNBUFFERED=1
ExecStart=$python_bin -m backend.scripts.main
Restart=on-failure
RestartSec=10
TimeoutStopSec=20
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload
systemctl enable costume-detector.service
echo "Installed. Start: sudo systemctl start costume-detector"
echo "Logs: sudo journalctl -u costume-detector -f"
