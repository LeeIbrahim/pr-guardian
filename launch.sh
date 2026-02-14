#!/bin/bash

# Flag to track if we started Ollama ourselves
OLLAMA_STARTED_BY_SCRIPT=false

# --- CONFIGURATION ---
# Define the models you want to ensure are downloaded
REQUIRED_MODELS=("llama3")
# ---------------------

cleanup() {
    echo ""
    echo "🛑 Stopping PR Guardian Suite..."
    # Kill the background process groups
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    
    if [ "$OLLAMA_STARTED_BY_SCRIPT" = true ]; then
        echo "Stopping Ollama..."
        pkill ollama
    else
        echo "Ollama was already running; leaving it active."
    fi
    exit
}

trap cleanup SIGINT

echo "🚀 Starting PR Guardian Suite..."

echo "Cleaning up old sessions..."
fuser -k 8000/tcp 8501/tcp 2>/dev/null

# 1. Start or Verify Ollama
if curl -s http://127.0.0.1:11434/api/tags > /dev/null; then
    echo "ℹ️ Ollama is already running."
else
    if command -v ollama &> /dev/null; then
        echo "Starting Ollama (Local LLM Server)..."
        ollama serve &
        OLLAMA_STARTED_BY_SCRIPT=true
        sleep 5
    else
        echo "⚠️ Warning: Ollama not found. Local models will not work."
    fi
fi

# 2. Verify Models are Downloaded (Fixes the 404 Error)
if command -v ollama &> /dev/null; then
    for model in "${REQUIRED_MODELS[@]}"; do
        if ollama list | grep -q "$model"; then
            echo "Model '$model' is already installed."
        else
            echo "Model '$model' not found. Pulling now..."
            ollama pull "$model"
        fi
    done
fi

# 3. Start Backend (FastAPI)
echo "Starting Backend (FastAPI)..."
PYTHONPATH=src uv run uvicorn pr_guardian.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Waiting for Backend to initialize..."
until curl -s http://127.0.0.1:8000/ > /dev/null; do
  sleep 1
done

# 4. Start Frontend (Streamlit)
echo "Starting Frontend (Streamlit)..."
uv run streamlit run gui.py --server.port 8501 &
FRONTEND_PID=$!

echo "✅ All services are running!"
echo "Frontend UI: http://127.0.0.1:8501"

wait