#!/bin/bash
set -e

echo "Running build pipeline..."

# 1. Compile & Check
echo "Compiling frontend assets..."
npm run build

echo "Running type check..."
npm run check

# 2. Deploy
echo "Deploying worker to Cloudflare..."
npm run deploy

# 3. Verify Deployment
echo "Verifying deployment..."
# Check HTTP status of the worker (adjust URL as needed, assuming nxs1.tuliofh01.workers.dev based on wrangler.json name)
# Note: wrangler.json name is 'nxs1', so default worker URL is nxs1.<subdomain>.workers.dev
WORKER_URL="https://nxs1.tuliofh01.workers.dev"

if command -v curl &> /dev/null; then
    HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" $WORKER_URL)
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "Worker is up and running at $WORKER_URL (Status: $HTTP_STATUS)"
    else
        echo "Worker deployment might have issues. Status: $HTTP_STATUS"
    fi
else
    echo "curl not found, skipping HTTP check."
fi

# 4. Check Tunnel Status
echo "Checking Cloudflare Tunnel status..."
if command -v cloudflared &> /dev/null; then
    cloudflared tunnel list || echo "No tunnels found or not logged in."
else
    echo "cloudflared not installed."
fi

echo "Build and deployment complete."
