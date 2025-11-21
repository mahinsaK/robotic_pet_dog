#!/bin/bash

echo "🤖 EASY ROBOT CONTROL STARTUP"
echo "============================="

cd /home/ubuntu/without_ros

# Activate virtual environment
source /home/ubuntu/.venv/bin/activate

# Kill any existing servers
pkill -f "python.*robot" 2>/dev/null || true
pkill -f "python.*8080" 2>/dev/null || true

# Wait a moment
sleep 2

echo "🚀 Starting Easy Robot Server (WebSocket on port 8765)..."
python easy_robot_server.py &
SERVER_PID=$!
sleep 1

echo "🌐 Starting Simple Web Server (HTTP on port 8080)..."
python -m http.server 8080 &
WEB_PID=$!
sleep 1

echo ""
echo "✅ EASY ROBOT SYSTEM READY!"
echo "=========================="
echo "🌐 Open in browser: http://localhost:8080/easy_robot_control.html"
echo "🌐 Or network access: http://10.236.10.48:8080/easy_robot_control.html"
echo ""
echo "🤖 WebSocket Server: ws://localhost:8765"
echo "🌐 Web Server: http://localhost:8080"
echo ""
echo "🛑 Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $SERVER_PID 2>/dev/null || true
    kill $WEB_PID 2>/dev/null || true
    pkill -f "python.*robot" 2>/dev/null || true
    pkill -f "python.*8080" 2>/dev/null || true
    echo "✅ Servers stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for servers
wait
