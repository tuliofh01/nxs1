#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TUNNEL_NAME="nxs1"

echo -e "${GREEN}=== Cloudflare Tunnel Manager ===${NC}"

# Pre-checks
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}Error: cloudflared is not installed. Run ./setup.sh first.${NC}"
    exit 1
fi

if [ ! -f ~/.cloudflared/cert.pem ]; then
    echo -e "${RED}Error: Not authenticated. Run ./setup.sh first.${NC}"
    exit 1
fi

# Tunnel Management
echo -e "\n${YELLOW}Checking tunnel configuration for '$TUNNEL_NAME'...${NC}"

if ! cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "Tunnel not found. Creating..."
    if cloudflared tunnel create "$TUNNEL_NAME"; then
        echo -e "${GREEN}Tunnel '$TUNNEL_NAME' created successfully.${NC}"
    else
        echo -e "${RED}Failed to create tunnel.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Tunnel '$TUNNEL_NAME' already exists.${NC}"
fi

# Running
echo -e "\n${GREEN}Starting Tunnel '$TUNNEL_NAME'...${NC}"
echo "This will block the terminal. Press Ctrl+C to stop."
echo "---------------------------------------------------"

# We run without a config file here for simplicity, assuming the user just wants
# to expose the tunnel. For production, a config.yml is recommended.
# If you have a specific target (e.g., SSH or HTTP), you might need to specify it.
# For now, we'll run it. Note: 'tunnel run' typically requires a config file or ingress rules
# defined in the dashboard if it's a remotely managed tunnel.
# If this is a locally managed tunnel, we need to know what to route.

# Attempting to run. If it fails due to missing config, we'll warn.
if ! cloudflared tunnel run "$TUNNEL_NAME"; then
    echo -e "\n${RED}Tunnel stopped or failed to start.${NC}"
    echo "Ensure you have a valid configuration or ingress rules set up."
    echo "If you are using a config file, make sure it is in ~/.cloudflared/config.yml or specify it with --config."
fi
