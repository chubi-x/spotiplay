#!/bin/bash
# Spotiplay deploy script for production (run as git push hook, cron, or manually)
# Edit USER, DIR, and SERVICE as needed

set -e

USER=ubuntu
DIR=/home/ubuntu/spotiplay
SERVICE=spotiplay
VENV="$DIR/venv"

cd "$DIR"
echo "[deploy.sh] Pulling latest changes..."
git pull --ff-only

if [ ! -d "$VENV" ]; then
    echo "[deploy.sh] Creating venv..."
    python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"

if [ -f requirements-prod.txt ]; then
    echo "[deploy.sh] Installing prod requirements..."
    pip install --upgrade pip
    pip install -r requirements-prod.txt
else
    echo "[deploy.sh] Installing requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

echo "[deploy.sh] Restarting systemd service..."
sudo systemctl restart "$SERVICE"
echo "[deploy.sh] Deployment complete."

