#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Build and Deploy Pipeline ===${NC}"

# 1. Compile Assets
echo -e "\n${YELLOW}[1/3] Compiling assets...${NC}"
# This runs build.js which handles esbuild (TS) and sass (SCSS)
if npm run build; then
    echo -e "${GREEN}Assets compiled successfully.${NC}"
else
    echo -e "${RED}Asset compilation failed.${NC}"
    exit 1
fi

# 2. Type Check
echo -e "\n${YELLOW}[2/3] Running type checks...${NC}"
if npm run check; then
    echo -e "${GREEN}Type checks passed.${NC}"
else
    echo -e "${RED}Type checks failed.${NC}"
    exit 1
fi

# 3. Deploy
echo -e "\n${YELLOW}[3/3] Deploying to Cloudflare Workers...${NC}"
if npm run deploy; then
    echo -e "${GREEN}Deployment successful.${NC}"
else
    echo -e "${RED}Deployment failed.${NC}"
    exit 1
fi

# 4. Verify
echo -e "\n${YELLOW}Verifying deployment...${NC}"
# Extract worker name from wrangler.json if possible, defaulting to known name
WORKER_URL="https://nxs1.tuliofh01.workers.dev"

if command -v curl &> /dev/null; then
    HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" $WORKER_URL)
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo -e "${GREEN}Worker is accessible at $WORKER_URL (Status: 200 OK)${NC}"
    else
        echo -e "${RED}Worker returned status: $HTTP_STATUS${NC}"
    fi
else
    echo "curl not found, skipping HTTP verification."
fi

echo -e "\n${GREEN}Pipeline Complete!${NC}"
