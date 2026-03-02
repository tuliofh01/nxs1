#!/bin/bash
set -e

echo "Building Frontend..."
npm run build

echo "Deploying Worker..."
npm run deploy

echo "Checking Cloudflare Tunnel Status..."
if command -v cloudflared &> /dev/null; then
    cloudflared tunnel info || echo "Tunnel not running or not configured."
else
    echo "cloudflared not installed."
fi

echo "Deployment Complete!"
