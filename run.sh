#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
WORKER_URL="https://nxs1.tuliofh01.workers.dev"

echo -e "${GREEN}=== Cloudflare Quick Tunnel Manager ===${NC}"
echo "This script starts a free Cloudflare Tunnel (TryCloudflare) and updates your Worker."

# Check for cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}Error: cloudflared is not installed. Run ./setup.sh first.${NC}"
    exit 1
fi

# Ask for port/service
read -p "Enter local port/service to expose (default: ssh://localhost:22): " SERVICE_URL
SERVICE_URL=${SERVICE_URL:-ssh://localhost:22}

echo -e "\n${YELLOW}Starting tunnel for $SERVICE_URL...${NC}"
echo "This may take a moment to initialize..."

# Start cloudflared in the background and capture output
LOG_FILE=$(mktemp)
cloudflared tunnel --url "$SERVICE_URL" > "$LOG_FILE" 2>&1 &
PID=$!

# Wait for URL to appear in logs
echo "Waiting for tunnel URL..."
TUNNEL_URL=""
MAX_RETRIES=30
COUNT=0

while [ -z "$TUNNEL_URL" ] && [ $COUNT -lt $MAX_RETRIES ]; do
    sleep 1
    TUNNEL_URL=$(grep -o 'https://.*\.trycloudflare\.com' "$LOG_FILE" | head -n 1)
    COUNT=$((COUNT+1))
done

if [ -z "$TUNNEL_URL" ]; then
    echo -e "${RED}Failed to obtain tunnel URL. Check logs:${NC}"
    cat "$LOG_FILE"
    kill $PID
    rm "$LOG_FILE"
    exit 1
fi

echo -e "${GREEN}Tunnel Active at: $TUNNEL_URL${NC}"

# Update Worker
echo -e "\n${YELLOW}Updating Worker at $WORKER_URL...${NC}"

# Read secret if exists
SECRET=""
if [ -f .env ]; then
    source .env
fi

# Post data to worker
if [ -n "$TUNNEL_SECRET" ]; then
    RESPONSE=$(curl -s -X POST "$WORKER_URL/api/tunnel" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TUNNEL_SECRET" \
        -d "{\"tunnelUrl\": \"$TUNNEL_URL\"}")
else
    # If no secret, try without auth (if worker allows it in dev mode)
    RESPONSE=$(curl -s -X POST "$WORKER_URL/api/tunnel" \
        -H "Content-Type: application/json" \
        -d "{\"tunnelUrl\": \"$TUNNEL_URL\"}")
fi

echo "Worker Response: $RESPONSE"

echo -e "\n${GREEN}Setup Complete!${NC}"
echo "Your local service ($SERVICE_URL) is now linked to your Worker."
echo "Visit $WORKER_URL to see the connection details."
echo -e "${YELLOW}Press Ctrl+C to stop the tunnel.${NC}"

# Keep script running to maintain the background process
wait $PID
