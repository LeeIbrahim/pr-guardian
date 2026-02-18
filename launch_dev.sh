#!/bin/bash
# launch_dev.sh

GUI_PORT=8501
PROXY_PORT=11435
UV="/home/forky/.local/bin/uv"

cleanup() {
    echo -e "\n🛑 Shutting down Dev Services..."
    sudo caddy stop 2>/dev/null
    [ -n "$GUI_PID" ] && kill $GUI_PID 2>/dev/null
    exit
}
trap cleanup INT TERM

echo "🧹 Clearing GUI and Proxy ports (leaving 8000 for Debugger)..."
# We specifically avoid killing 8000 so your VS Code session isn't interrupted
sudo fuser -k $GUI_PORT/tcp $PROXY_PORT/tcp 2>/dev/null

echo "🛡️ Starting Caddy Proxy (Ollama Discovery)..."
sudo caddy start --config ./Caddyfile
sleep 1

echo "💻 Launching GUI in Dev Mode..."
# Setting PYTHONPATH so streamlit can find your src modules
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

$UV run streamlit run gui.py --server.port $GUI_PORT &
GUI_PID=$!

echo -e "\n✅ Dev Environment Ready!"
echo "1. GUI: https://localhost:$GUI_PORT"
echo "2. Proxy: https://guardian.local:$PROXY_PORT"
echo "3. 👉 Now start the 'Python: Debug Backend' configuration in VS Code."

# Keep script running to maintain the GUI process
wait $GUI_PID