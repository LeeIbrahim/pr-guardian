#!/bin/bash

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' 

echo -e "${BLUE}🛡️ PR Guardian Secure Install${NC}"

# 1. SSL Setup Logic
if [ -f "key.pem" ] && [ -f "cert.pem" ]; then
    echo -e "${GREEN}✅ Existing certificates found.${NC}"
else
    read -p "Do you have existing SSL certificates to use? (y/n): " has_certs
    if [ "$has_certs" == "y" ]; then
        read -p "Enter path to key.pem: " key_path
        read -p "Enter path to cert.pem: " cert_path
        cp "$key_path" ./key.pem
        cp "$cert_path" ./cert.pem
    else
        echo -e "${YELLOW}Generating self-signed certs for guardian.local...${NC}"
        openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes -subj "/CN=guardian.local"
    fi
fi

# 2. Local DNS Setup (Fixes [Errno -2])
if ! grep -q "guardian.local" /etc/hosts; then
    echo -e "${YELLOW}Adding guardian.local to /etc/hosts (Sudo required)...${NC}"
    echo "127.0.0.1 guardian.local" | sudo tee -a /etc/hosts
fi

# 3. Caddy Installation
if ! command -v caddy &> /dev/null; then
    echo "Installing Caddy..."
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt update && sudo apt install caddy -y
fi

# 4. uv Sync
uv sync
echo -e "${GREEN}✅ Installation Complete.${NC}"