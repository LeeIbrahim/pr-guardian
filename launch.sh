#!/bin/bash
# launch.sh

BACKEND_PORT=8000
FRONTEND_PORT=8501
UV="/home/forky/.local/bin/uv"

cleanup() {
    echo -e "\n🛑 Shutting down..."
    sudo caddy stop 2>/dev/null
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    exit
}
trap cleanup INT TERM

echo "🧹 Clearing ports..."
sudo fuser -k 11435/tcp 8000/tcp 8501/tcp 2>/dev/null

echo "🛡️ Starting Caddy Proxy..."
sudo caddy start --config ./Caddyfile
sleep 2

# Starting local llms
echo "🦙 Checking Local Models (Ollama)..."
ollama serve > /dev/null 2>&1 & # Starts Ollama in background if not running
sleep 2
ollama run deepseek-r1:1.5b "" # Pre-loads the model into VRAM
ollama run llama3.2 ""

echo "🚀 Launching Backend..."
# Pointing directly to main:app in the root directory
$UV run uvicorn backend.main:app \
    --host 127.0.0.1 --port $BACKEND_PORT \
    --ssl-keyfile ./key.pem --ssl-certfile ./cert.pem &
BACKEND_PID=$!

echo "💻 Launching GUI..."
$UV run streamlit run gui.py \
    --server.port $FRONTEND_PORT \
    --server.sslCertFile ./cert.pem \
    --server.sslKeyFile ./key.pem &
FRONTEND_PID=$!

wait