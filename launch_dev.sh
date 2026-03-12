#!/bin/bash
# launch_dev.sh

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

FRONTEND_PORT="${FRONTEND_PORT:-5173}"
# Using the local secure address for consistent OAuth origins
SECURE_URL="https://localhost:5173"

cleanup() {
    echo -e "\n🛑 Shutting down Dev Services..."
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    [ -n "$CADDY_PID" ] && kill $CADDY_PID 2>/dev/null
    exit
}
trap cleanup INT TERM

# Start Ollama
ollama serve > /dev/null 2>&1 & 

until curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "⏳ Waiting for Ollama service..."
  sleep 2
done

# Pre-load models into VRAM
ollama run deepseek-r1:1.5b "" 
ollama run llama3.2 ""

# Launching Vite Frontend (Internal Port)
echo "💻 Launching Vite Frontend on http://localhost:3000..."
cd frontend && npm run dev -- --port 3000 &
FRONTEND_PID=$!

# Launching Caddy as an HTTPS Proxy
# This uses 'caddy reverse-proxy' to wrap the HTTP Vite server in HTTPS
echo "🛡️ Starting Caddy HTTPS Proxy at $SECURE_URL..."
caddy reverse-proxy --from localhost:5173 --to localhost:3000 > /dev/null 2>&1 &
CADDY_PID=$!

echo -e "\n✅ Services Ready."
echo "👉 Frontend (Secure): $SECURE_URL"
echo "👉 Start the Backend Debugger (Port 8000) with SSL enabled"

wait $FRONTEND_PID