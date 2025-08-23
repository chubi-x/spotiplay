#!/bin/bash
# Spotiplay deploy script for production (run by GitHub Actions or manually)
# Edits nginx/systemd config, installs dependencies, restarts services

set -e

USER=ubuntu
DIR=/home/ubuntu/spotiplay
SERVICE=spotiplay
VENV="$DIR/venv"
SYSTEMD_SERVICE_FILE=spotiplay.service
NGINX_CONF_FILE=spotiplay_nginx.conf
SYSTEMD_DEST=/etc/systemd/system/$SYSTEMD_SERVICE_FILE
NGINX_DEST=/etc/nginx/sites-available/spotiplay
NGINX_SYMLINK=/etc/nginx/sites-enabled/spotiplay

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

echo "[deploy.sh] Installing systemd service file..."
sudo cp "$DIR/$SYSTEMD_SERVICE_FILE" "$SYSTEMD_DEST"
sudo systemctl daemon-reload

echo "[deploy.sh] Installing nginx config..."
sudo cp "$DIR/$NGINX_CONF_FILE" "$NGINX_DEST"
if [ ! -e "$NGINX_SYMLINK" ]; then
    sudo ln -s "$NGINX_DEST" "$NGINX_SYMLINK"
fi
sudo nginx -t && sudo systemctl reload nginx

echo "[deploy.sh] Restarting systemd service..."
sudo systemctl restart "$SERVICE"
echo "[deploy.sh] Deployment complete."

