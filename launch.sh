#!/bin/bash
# launch.sh

BACKEND_PORT=8000
FRONTEND_PORT=5173
UV="/home/forky/.local/bin/uv"

cleanup() {
    echo -e "\n🛑 Shutting down..."
    sudo caddy stop 2>/dev/null
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    exit
}
trap cleanup INT TERM

# Clearing ports for Ollama, Backend, and Vite
echo "🧹 Clearing ports..."
sudo fuser -k 11435/tcp 8000/tcp 5173/tcp 2>/dev/null

# Starting Caddy Proxy
echo "🛡️ Starting Caddy Proxy..."
sudo caddy start --config ./Caddyfile
sleep 2

# Starting local llms
echo "🦙 Checking Local Models (Ollama)..."
# Starts Ollama in background if not running
ollama serve > /dev/null 2>&1 & 

# Wait for Ollama service to be ready
until curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "⏳ Waiting for Ollama service..."
  sleep 1
done

# Pre-loads models into VRAM
ollama run deepseek-r1:1.5b "" 
ollama run llama3.2 ""

# Launching Backend
echo "🚀 Launching Backend..."
$UV run uvicorn backend.main:app \
    --host 127.0.0.1 --port $BACKEND_PORT \
    --ssl-keyfile ./key.pem --ssl-certfile ./cert.pem &
BACKEND_PID=$!

# Launching Vite Frontend
echo "💻 Launching Vite Frontend..."
# Navigates to frontend folder and runs the dev command from package.json
cd frontend && npm run start &
FRONTEND_PID=$!

wait