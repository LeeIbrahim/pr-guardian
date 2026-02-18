#!/bin/bash
# stop_models.sh

echo "🛑 Initiating Local Model Shutdown..."

# 1. Stop the Caddy Proxy
echo "🛡️ Stopping Caddy Proxy..."
sudo caddy stop 2>/dev/null

# 2. Unload specific models from Ollama memory
# This frees up VRAM immediately
echo "🧠 Unloading local models from VRAM..."
curl -X POST http://localhost:11434/api/generate -d '{"model": "llama3.2", "keep_alive": 0}' > /dev/null 2>&1
curl -X POST http://localhost:11434/api/generate -d '{"model": "deepseek-r1:1.5b", "keep_alive": 0}' > /dev/null 2>&1

# 3. Kill any lingering backend or frontend processes
echo "🧹 Cleaning up lingering PR Guardian processes..."
sudo fuser -k 8000/tcp 8501/tcp 2>/dev/null

# 4. Optional: Stop the Ollama service entirely
# Only uncomment if you want to turn off the model engine completely
# sudo systemctl stop ollama

echo "✅ All services and models have been shut down."