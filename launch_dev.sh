#!/bin/bash
# launch_dev.sh

# TODO: load port from .env or config file
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
# TODO: load the UV path from .env or config file
UV="${UV:-/home/forky/.local/bin/uv}"

cleanup() {
    echo -e "\n🛑 Shutting down Dev Services..."
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    exit
}
trap cleanup INT TERM

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

# Launching Vite Frontend
echo "💻 Launching Vite Frontend..."
cd frontend && npm run start &
FRONTEND_PID=$!

echo -e "\n✅ Services Ready."
echo "👉 Now start the VS Code Debugger for the Backend (Port 8000)"

wait $FRONTEND_PID