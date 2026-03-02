# Deployment Guide

## Prerequisites
- Node.js & npm
- Cloudflare Account
- `wrangler` CLI installed and authenticated (`npx wrangler login`)

## Deploying the Worker

1.  **Install Dependencies:**
    ```bash
    npm install
    ```

2.  **Build & Deploy:**
    Run the deployment script:
    ```bash
    ./deploy.sh
    ```
    This will:
    - Compile TypeScript to JavaScript.
    - Compile SCSS to CSS.
    - Upload the worker and assets to Cloudflare.

## Arch Linux SSH Tunnel Setup

To route your SSH connection through Cloudflare Tunnel:

1.  **Install cloudflared:**
    ```bash
    sudo pacman -S cloudflared
    ```

2.  **Authenticate:**
    ```bash
    cloudflared tunnel login
    ```

3.  **Create a Tunnel:**
    ```bash
    cloudflared tunnel create <tunnel-name>
    ```

4.  **Configure Ingress (config.yml):**
    Create `~/.cloudflared/config.yml`:
    ```yaml
    tunnel: <tunnel-uuid>
    credentials-file: /home/<user>/.cloudflared/<tunnel-uuid>.json

    ingress:
      - hostname: ssh.yourdomain.com
        service: ssh://localhost:22
      - service: http_status:404
    ```

5.  **Route DNS:**
    ```bash
    cloudflared tunnel route dns <tunnel-name> ssh.yourdomain.com
    ```

6.  **Run as Service:**
    ```bash
    cloudflared service install
    systemctl start cloudflared
    systemctl enable cloudflared
    ```

7.  **Connect Client:**
    On your client machine, add to `~/.ssh/config`:
    ```ssh
    Host my-server
        HostName ssh.yourdomain.com
        ProxyCommand cloudflared access ssh --hostname %h
    ```
