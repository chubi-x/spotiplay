# Spotiplay Deployment

## 1. GitHub Actions Automated Deployment to EC2

Deployment is handled by a GitHub Actions workflow. On every push to the `main` branch:
- The workflow uses SSH to log in to your EC2 instance.
- It pulls the latest code to `/home/ubuntu/spotiplay`.
- It ensures `deploy.sh` is executable and runs it to install dependencies and restart the service.

### Setup Steps
**A. On EC2:**
- Make sure the repository is cloned at `/home/ubuntu/spotiplay`.
- Add the public key (from the GitHub Actions deploy key) to `/home/ubuntu/.ssh/authorized_keys`.
- Ensure `deploy.sh` is present and executable (`chmod +x deploy.sh`).
- Systemd and Nginx should be set up as described previously.

**B. In GitHub:**
- Add these repository secrets:
    - `EC2_SSH_PRIVATE_KEY`: The private key for the deployment user.
    - `EC2_HOST`: The public DNS or IP address of your EC2.
    - `EC2_USER`: The SSH user (typically `ubuntu`).

**C. Review Workflow File:**
- See `.github/workflows/deploy-to-ec2.yml`.

### What Happens on Push?
- GitHub Actions SSH's to EC2 and runs:
    - `git pull --ff-only`
    - `chmod +x deploy.sh`
    - `./deploy.sh`
