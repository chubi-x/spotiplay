#!/bin/bash
# Spotiplay Docker deploy script for production (run by GitHub Actions or manually)
# Builds and runs Spotiplay in a Docker container and also (optionally) updates nginx config
set -e

APP_NAME=spotiplay
IMAGE_NAME=spotiplay:latest
CONTAINER_NAME=spotiplay_app
DIR=/home/ubuntu/spotiplay
SYSTEMD_SERVICE_FILE=spotiplay.service
NGINX_CONF_FILE=spotiplay_nginx.conf
SYSTEMD_DEST=/etc/systemd/system/$SYSTEMD_SERVICE_FILE
NGINX_DEST=/etc/nginx/sites-available/spotiplay
NGINX_SYMLINK=/etc/nginx/sites-enabled/spotiplay

cd "$DIR"

# Build Docker image
echo "[deploy.sh] Building Docker image..."
docker build -t $IMAGE_NAME .

# Stop and remove old container if it exists
if [ $(docker ps -aq -f name=^/$CONTAINER_NAME$) ]; then
	echo "[deploy.sh] Stopping old container..."
	docker stop $CONTAINER_NAME || true
	echo "[deploy.sh] Removing old container..."
	docker rm $CONTAINER_NAME || true
fi

# Run new container
echo "[deploy.sh] Running new container..."
docker run -d --name $CONTAINER_NAME --restart unless-stopped \
	-p 127.0.0.1:5000:5000 \
	--env-file .env \
	$IMAGE_NAME

# (Optional) Nginx config for SSL/static proxy
if [ -f "$DIR/$NGINX_CONF_FILE" ]; then
	echo "[deploy.sh] Installing nginx config..."
	sudo cp "$DIR/$NGINX_CONF_FILE" "$NGINX_DEST"
	if [ ! -e "$NGINX_SYMLINK" ]; then
		sudo ln -s "$NGINX_DEST" "$NGINX_SYMLINK"
	fi
	sudo nginx -t && sudo systemctl reload nginx
fi

echo "[deploy.sh] Deployment complete."
