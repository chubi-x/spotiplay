# EC2 Setup for GitHub Actions Deployment

1. **Ensure SSH Access:**
   - Create an SSH key pair for GitHub Actions (do NOT use your personal key) on your local machine:
     ```
     ssh-keygen -t ed25519 -C "github-actions@spotiplay"
     ```
   - Add the public key (id_ed25519.pub) to `/home/ubuntu/.ssh/authorized_keys` on your EC2 instance.

2. **Ensure the repository is cloned at `/home/ubuntu/spotiplay`:**
   - If not already present:
     ```
     git clone <your-repo-url> /home/ubuntu/spotiplay
     cd /home/ubuntu/spotiplay
     ```

3. **Ensure correct permissions for scripts:**
   ```
   chmod +x /home/ubuntu/spotiplay/deploy.sh
   ```

4. **Systemd/NGINX setup only needs to be done once (unless the config changes):**
   - Place the systemd and nginx config files as documented previously.
   - Enable and start the service:
     ```
     sudo systemctl daemon-reload
     sudo systemctl enable spotiplay
     sudo systemctl start spotiplay
     sudo systemctl status spotiplay
     sudo systemctl reload nginx
     ```

5. **Your deploy.sh script should handle:**
   - Pulling latest code (redundant but safe)
   - Installing dependencies
   - Restarting the systemd service

6. **Security:**
   - Make sure only the GitHub Actions SSH key is allowed to deploy (limit to GitHub Actions IPs if possible).
   - Do not allow password authentication for SSH.

7. **Verify:**
   - Manually SSH into EC2 and run `deploy.sh` to ensure it works before relying on Actions.

