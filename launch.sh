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

if [ "$1" = "--test" ]; then
    echo "🧪 Running ALL PR Guardian Tests..."
    # Clear caches to prevent import mismatches
    find . -name "__pycache__" -exec rm -rf {} +
    rm -rf .pytest_cache
    
    sudo caddy start --config ./Caddyfile 2>/dev/null
    PYTHONPATH=src $UV run pytest tests/ -v
    
    TEST_EXIT_CODE=$?
    sudo caddy stop 2>/dev/null
    exit $TEST_EXIT_CODE
fi

echo "🧹 Clearing ports..."
sudo fuser -k 11435/tcp 8000/tcp 8501/tcp 2>/dev/null

echo "🛡️ Starting Caddy Proxy..."
sudo caddy start --config ./Caddyfile
sleep 2

echo "🚀 Launching Backend..."
PYTHONPATH=src $UV run uvicorn pr_guardian.main:app \
    --host 0.0.0.0 --port $BACKEND_PORT \
    --ssl-keyfile ./key.pem --ssl-certfile ./cert.pem &
BACKEND_PID=$!

echo "💻 Launching GUI..."
$UV run streamlit run gui.py \
    --server.port $FRONTEND_PORT \
    --server.sslCertFile ./cert.pem \
    --server.sslKeyFile ./key.pem &
FRONTEND_PID=$!

wait