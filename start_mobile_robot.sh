#!/bin/bash

# Mobile Robot Control System Startup Script

echo "🤖 Starting Mobile Robot Control System..."
echo "="×50

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    pkill -f "robot_mobile_backend.py" 2>/dev/null
    pkill -f "http.server" 2>/dev/null
    pkill -f "python.*8080" 2>/dev/null
    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "robot_mobile_backend.py" 2>/dev/null
pkill -f "http.server" 2>/dev/null
pkill -f "python.*8080" 2>/dev/null
sleep 2

# Get local IP for display
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

echo "🌐 Network Configuration:"
echo "   Local IP: $LOCAL_IP"
echo ""

# Start HTTP server for serving the web interface
echo "🌐 Starting HTTP server for web interface..."
cd /home/ubuntu/without_ros
nohup python3 -m http.server 8080 > /dev/null 2>&1 &
HTTP_PID=$!
sleep 2

# Check if HTTP server started successfully
if ps -p $HTTP_PID > /dev/null; then
    echo "✅ HTTP server started (PID: $HTTP_PID)"
    echo "   📱 Web interface: http://localhost:8080/robot_mobile_control.html"
    echo "   🌐 Remote access: http://$LOCAL_IP:8080/robot_mobile_control.html"
else
    echo "❌ Failed to start HTTP server"
    exit 1
fi

echo ""

# Start WebSocket server for robot control
echo "🤖 Starting Robot WebSocket server..."
if [ -f "/home/ubuntu/.venv/bin/activate" ]; then
    echo "🐍 Activating Python virtual environment..."
    source /home/ubuntu/.venv/bin/activate
fi

# Start the robot backend server
python3 robot_mobile_backend.py &
ROBOT_PID=$!

echo ""
echo "🚀 Mobile Robot Control System is running!"
echo "="×50
echo "📱 Open your mobile browser and navigate to:"
echo "   http://$LOCAL_IP:8080/robot_mobile_control.html"
echo ""
echo "🔗 In the web interface:"
echo "   1. Set WebSocket URL to: ws://$LOCAL_IP:8765"
echo "   2. Click 'Connect'"
echo "   3. Click 'Connect'"
echo "   3. Start controlling your robot!"
echo ""
echo "💡 Available commands:"
echo "   • Stand/Sit - Basic poses"
echo "   • Arrow keys - Walk/turn directions"
echo "   • Distance - Check obstacle sensor"
echo "   • Stop - Emergency stop"
echo "   • Gestures: Open Hand (walk), Fist (stop), Thumbs Up (backward), Peace (sit)"
echo ""
echo "⚠️ Press Ctrl+C to stop all services"
echo "="×50

# Wait for robot server to finish or be interrupted
wait $ROBOT_PID

# Cleanup on exit
cleanup