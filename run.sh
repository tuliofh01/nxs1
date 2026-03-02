#!/bin/bash
set -e

# Configuration
TUNNEL_NAME="nxs1" # Replace with actual tunnel name if different, or parse from config.yml if available
SSH_SERVICE="sshd"
CLOUDFLARED_SERVICE="cloudflared"

echo "Checking SSH daemon status..."
if ! systemctl is-active --quiet "$SSH_SERVICE"; then
    echo "Starting SSH daemon..."
    sudo systemctl start "$SSH_SERVICE"
else
    echo "SSH daemon is running."
fi

echo "Checking Cloudflare Tunnel status..."
if ! systemctl is-active --quiet "$CLOUDFLARED_SERVICE"; then
    echo "Starting Cloudflare Tunnel..."
    sudo systemctl start "$CLOUDFLARED_SERVICE"
else
    echo "Cloudflare Tunnel is running."
fi

# Function to monitor logs
monitor_logs() {
    echo "Monitoring logs... (Ctrl+C to stop monitoring)"
    sudo journalctl -u "$CLOUDFLARED_SERVICE" -f
}

# Function to stop/pause
stop_connection() {
    read -p "Stop SSH daemon? (y/n): " STOP_SSH
    if [[ "$STOP_SSH" == "y" ]]; then
        sudo systemctl stop "$SSH_SERVICE"
        echo "SSH daemon stopped."
    fi

    read -p "Stop Cloudflare Tunnel? (y/n): " STOP_CF
    if [[ "$STOP_CF" == "y" ]]; then
        sudo systemctl stop "$CLOUDFLARED_SERVICE"
        echo "Cloudflare Tunnel stopped."
    fi
}

# Main loop
while true; do
    echo "-----------------------------------"
    echo "Status:"
    echo "SSH Daemon: $(systemctl is-active "$SSH_SERVICE")"
    echo "Cloudflare Tunnel: $(systemctl is-active "$CLOUDFLARED_SERVICE")"
    echo "-----------------------------------"
    echo "Options:"
    echo "1. Monitor Logs"
    echo "2. Stop/Pause Connection"
    echo "3. Restart Services"
    echo "4. Exit"
    
    read -p "Select option: " OPTION
    
    case "$OPTION" in
        1)
            monitor_logs
            ;;
        2)
            stop_connection
            ;;
        3)
            sudo systemctl restart "$SSH_SERVICE"
            sudo systemctl restart "$CLOUDFLARED_SERVICE"
            echo "Services restarted."
            ;;
        4)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option."
            ;;
    esac
done
