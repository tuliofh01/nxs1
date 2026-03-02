#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Cloudflare Tunneling Setup ===${NC}"

# 1. Check for cloudflared
echo -e "\n${YELLOW}[1/3] Checking cloudflared installation...${NC}"
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}cloudflared is not installed.${NC}"
    
    # Detect OS
    if [ -f /etc/arch-release ]; then
        echo "Detected Arch Linux."
        echo "Please run: sudo pacman -S cloudflared"
    elif [ -f /etc/debian_version ]; then
        echo "Detected Debian/Ubuntu."
        echo "Please follow Cloudflare's instructions to install the .deb package."
    else
        echo "OS not automatically detected. Please install cloudflared manually."
    fi
    
    echo -e "${YELLOW}Please install cloudflared and run this script again.${NC}"
    exit 1
else
    echo -e "${GREEN}cloudflared is installed.$(cloudflared --version | head -n 1)${NC}"
fi

# 2. Check for cloudflared authentication
echo -e "\n${YELLOW}[2/3] Checking cloudflared authentication...${NC}"
if [ ! -f ~/.cloudflared/cert.pem ]; then
    echo -e "${YELLOW}cloudflared is not authenticated.${NC}"
    echo "Opening login page in your browser..."
    cloudflared tunnel login
else
    echo -e "${GREEN}cloudflared is authenticated.${NC}"
fi

# 3. SSH Configuration
echo -e "\n${YELLOW}[3/3] Setting up SSH access...${NC}"
SSH_GROUP="ssh-users"

if ! getent group "$SSH_GROUP" >/dev/null; then
    echo "Creating SSH group: $SSH_GROUP"
    sudo groupadd "$SSH_GROUP"
else
    echo "SSH group exists: $SSH_GROUP"
fi

echo "Current users in $SSH_GROUP:"
getent group "$SSH_GROUP" | cut -d: -f4

read -p "Do you want to add a user to the '$SSH_GROUP' group? (y/n): " ADD_USER
if [[ "$ADD_USER" == "y" ]]; then
    read -p "Enter username to add: " USER_NAME
    if id "$USER_NAME" >/dev/null 2>&1; then
        echo "User $USER_NAME exists. Adding to group..."
        sudo usermod -aG "$SSH_GROUP" "$USER_NAME"
        echo -e "${GREEN}User $USER_NAME added to $SSH_GROUP.${NC}"
    else
        read -p "User $USER_NAME does not exist. Create new user? (y/n): " CREATE_USER
        if [[ "$CREATE_USER" == "y" ]]; then
            sudo useradd -m -G "$SSH_GROUP" "$USER_NAME"
            echo -e "${GREEN}User $USER_NAME created and added to $SSH_GROUP.${NC}"
            
            echo "Please set a password for the new user:"
            sudo passwd "$USER_NAME"
        else
            echo "Skipping user creation."
        fi
    fi
fi

echo -e "\n${GREEN}=== Setup Complete ===${NC}"
echo "You can now run './run.sh' to start the tunnel."
