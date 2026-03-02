#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
WORKER_URL="https://nxs1.tuliofh01.workers.dev"
DEFAULT_SERVICE="ssh://localhost:22"

# Usage function
usage() {
    echo "Usage: $0 [service]"
    echo ""
    echo "Examples:"
    echo "  $0              # Expose SSH (default)"
    echo "  $0 8080        # Expose HTTP on port 8080"
    echo "  $0 3000        # Expose HTTP on port 3000"
    echo "  $0 ssh://localhost:22  # Expose custom SSH port"
    exit 1
}

echo -e "${GREEN}=== Cloudflare Quick Tunnel ===${NC}"

# Check for cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}cloudflared is not installed.${NC}"
    echo "Please run ./setup.sh first or install cloudflared."
    exit 1
fi

# Determine service to expose
SERVICE_URL="$DEFAULT_SERVICE"
if [ -n "$1" ]; then
    if [[ "$1" == ssh://* ]]; then
        SERVICE_URL="$1"
    elif [[ "$1" =~ ^[0-9]+$ ]]; then
        SERVICE_URL="http://localhost:$1"
    else
        SERVICE_URL="$1"
    fi
fi

echo "Exposing: $SERVICE_URL"
echo "Starting tunnel..."

# Start cloudflared in the background and capture output
LOG_FILE=$(mktemp)
cloudflared tunnel --url "$SERVICE_URL" > "$LOG_FILE" 2>&1 &
PID=$!

# Cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping tunnel...${NC}"
    kill $PID 2>/dev/null || true
    rm -f "$LOG_FILE"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for URL to appear in logs
echo "Waiting for tunnel URL..."
TUNNEL_URL=""
MAX_RETRIES=30
COUNT=0

while [ -z "$TUNNEL_URL" ] && [ $COUNT -lt $MAX_RETRIES ]; do
    sleep 1
    TUNNEL_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' "$LOG_FILE" | head -n 1)
    COUNT=$((COUNT+1))
    echo -n "."
done
echo ""

if [ -z "$TUNNEL_URL" ]; then
    echo -e "${RED}Failed to obtain tunnel URL. Check logs:${NC}"
    cat "$LOG_FILE"
    exit 1
fi

echo -e "${GREEN}Tunnel Active at: $TUNNEL_URL${NC}"

# Update Worker
echo "Updating dashboard..."
source .env 2>/dev/null || true

if [ -n "$TUNNEL_SECRET" ]; then
    curl -s -X POST "$WORKER_URL/api/tunnel" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TUNNEL_SECRET" \
        -d "{\"tunnelUrl\": \"$TUNNEL_URL\"}" > /dev/null
else
    curl -s -X POST "$WORKER_URL/api/tunnel" \
        -H "Content-Type: application/json" \
        -d "{\"tunnelUrl\": \"$TUNNEL_URL\"}" > /dev/null
fi

echo -e "${GREEN}Done!${NC}"
echo "Dashboard: $WORKER_URL"
echo "SSH Command: ssh user@${TUNNEL_URL#https://}"
echo ""
echo "Press Ctrl+C to stop."

# Keep running
wait $PID
