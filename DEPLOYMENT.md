# Spotiplay Deployment: Nginx & Systemd Setup Instructions

## Nginx Configuration
- File: `spotiplay_nginx.conf`
- Place at: `/etc/nginx/sites-available/spotiplay`
- Symlink into enabled sites:
  ```
  sudo ln -s /etc/nginx/sites-available/spotiplay /etc/nginx/sites-enabled/
  ```
- **Do not change** the `server_name` in the file unless you want to use a custom domain.

### HTTPS (SSL/TLS)
- Use [Let's Encrypt Certbot](https://certbot.eff.org/) for automatic free HTTPS setup.
- Example:
  ```
  sudo apt install certbot python3-certbot-nginx
  sudo certbot --nginx -d your.domain.com
  ```
- This will update your server block with `listen 443 ssl;` and SSL certificate paths.

- After config changes, reload Nginx:
  ```
  sudo systemctl reload nginx
  ```

## Systemd Service
- File: `spotiplay.service`
- Place at: `/etc/systemd/system/spotiplay.service`
- Ensure paths reference `/home/ubuntu/spotiplay` and correct user (default is `www-data`).
- Enable and start the service:
  ```
  sudo systemctl daemon-reload
  sudo systemctl enable spotiplay
  sudo systemctl start spotiplay
  sudo systemctl status spotiplay
  ```
- To restart after a code/config change:
  ```
  sudo systemctl restart spotiplay
  ```

## Automated Deployment with Git Hooks

### Setup
1. **Create a bare git repository for deployment:**
   ```
   mkdir -p /home/ubuntu/spotiplay.git
   cd /home/ubuntu/spotiplay.git
   git init --bare
   ```
2. **Set up the post-receive hook:**
   - Copy `post-receive.sample` to `/home/ubuntu/spotiplay.git/hooks/post-receive`:
     ```
     cp /home/ubuntu/spotiplay/post-receive.sample /home/ubuntu/spotiplay.git/hooks/post-receive
     chmod +x /home/ubuntu/spotiplay.git/hooks/post-receive
     ```
   - `post-receive` will update the working tree at `/home/ubuntu/spotiplay`, copy the systemd and nginx configs into place, reload services, and run `deploy.sh` after every push.
3. **Add the production server as a remote in your local repo:**
   ```
   git remote add production ubuntu@your.server.ip:/home/ubuntu/spotiplay.git
   git push production main  # or your branch
   ```

### What Happens on Push?
- The bare repo's `post-receive` hook checks out the latest code to `/home/ubuntu/spotiplay`, copies `spotiplay.service`/`spotiplay_nginx.conf` into their system locations, reloads/restarts systemd/nginx if needed, and runs `deploy.sh`.
- `deploy.sh` pulls dependencies and restarts the systemd service.

> **Note:** Ensure `/home/ubuntu/spotiplay/deploy.sh` is executable: `chmod +x deploy.sh`
> The post-receive hook must have passwordless sudo rights for copying configs and reloading services.

## Notes
- Your environment variables must be in `/home/ubuntu/spotiplay/.env`.
- The app runs on `localhost:5000` and is proxied by Nginx.
- Static files and favicon are served directly by Nginx for better performance.
- For further customization (multiple workers, logging), edit `spotiplay.service` and `deploy.sh` accordingly.

