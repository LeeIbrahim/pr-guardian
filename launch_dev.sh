#!/bin/bash
# launch_dev.sh

GUI_PORT=8501
UV="/home/forky/.local/bin/uv"

cleanup() {
    echo -e "\n Shutting down Dev Services..."
    [ -n "$GUI_PID" ] && kill $GUI_PID 2>/dev/null
    exit
}
trap cleanup INT TERM

echo "🧹 Clearing GUI port..."
sudo fuser -k $GUI_PORT/tcp 2>/dev/null

echo "💻 Launching GUI with MKCERT SSL..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# We MUST add the SSL flags here to stop the 'Record Too Long' error
$UV run streamlit run gui.py \
    --server.port $GUI_PORT \
    --server.sslCertFile ./cert.pem \
    --server.sslKeyFile ./key.pem &
GUI_PID=$!

echo -e "\n✅ GUI is running at https://localhost:8501"
echo "👉 Now start the VS Code Debugger for the Backend (Port 8000)"

wait $GUI_PID