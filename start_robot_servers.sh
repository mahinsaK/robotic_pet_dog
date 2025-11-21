#!/bin/bash

# Robot Control Server Launcher
# Starts both the WebSocket server and HTTP server for mobile access

echo "🤖 ROBOT CONTROL SERVER LAUNCHER"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "robot_control.html" ]; then
    echo "❌ robot_control.html not found. Please run this script from /home/ubuntu/without_ros"
    exit 1
fi

# Check if Python dependencies are available
echo "🔍 Checking dependencies..."

# Check for websockets
python3 -c "import websockets" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing websockets..."
    pip3 install websockets
fi

# Check for other required modules
python3 -c "import asyncio, json, subprocess, os" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ All dependencies available"
else
    echo "❌ Missing required Python modules"
    exit 1
fi

echo ""
echo "🚀 Starting Robot Control Servers..."
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $WEBSOCKET_PID 2>/dev/null
    kill $HTTP_PID 2>/dev/null
    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start WebSocket server in background
echo "🔌 Starting WebSocket server (port 8765)..."
python3 working_robot_server.py &
WEBSOCKET_PID=$!

# Wait a moment for WebSocket server to start
sleep 2

# Start HTTP server in background
echo "🌐 Starting HTTP server (port 8080)..."
python3 web_server.py &
HTTP_PID=$!

# Wait a moment for HTTP server to start
sleep 2

echo ""
echo "✅ Both servers are running!"
echo ""
echo "📱 PHONE ACCESS INSTRUCTIONS:"
echo "   1. Make sure your phone is on the same WiFi network as the Raspberry Pi"
echo "   2. Open your phone's web browser (Chrome, Safari, Firefox, etc.)"
echo "   3. Go to: http://10.236.10.48:8080/robot_control.html"
echo "   4. The website should load with robot controls"
echo "   5. Click 'Connect' to connect to the WebSocket server"
echo "   6. Use the control buttons to operate your robot!"
echo ""
echo "🖥️  You can also access from a computer:"
echo "   http://10.236.10.48:8080/robot_control.html"
echo ""
echo "🔧 Troubleshooting:"
echo "   - If page doesn't load: Check WiFi connection and IP address"
echo "   - If controls don't work: Make sure WebSocket connection is successful"
echo "   - If robot doesn't move: Check servo connections and power"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $WEBSOCKET_PID $HTTP_PID
