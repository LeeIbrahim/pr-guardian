#!/bin/bash

# Configuration
REQUIRED_MODELS=("llama3.1" "llama3.2")
BACKEND_PORT=8000
FRONTEND_PORT=8501

cleanup() {
    echo -e "\n🛑 Stopping PR Guardian..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT

echo "🚀 Starting PR Guardian Suite..."

# 1. Start Ollama if not running
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null; then
    echo "Starting Ollama server..."
    ollama serve &
    sleep 5
fi

# 2. Check for required local models
for model in "${REQUIRED_MODELS[@]}"; do
    if ! ollama list | grep -q "$model"; then
        echo "📥 Model $model not found. Pulling..."
        ollama pull "$model"
    fi
done

# 3. Launch Backend
echo "Starting Backend (FastAPI) on port $BACKEND_PORT..."
PYTHONPATH=src uv run uvicorn pr_guardian.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

# 4. Launch Frontend
echo "Starting Frontend (Streamlit) on port $FRONTEND_PORT..."
uv run streamlit run gui.py --server.port $FRONTEND_PORT &
FRONTEND_PID=$!

wait