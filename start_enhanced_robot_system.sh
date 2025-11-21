#!/bin/bash

# Enhanced Robot Control System Startup Script
# This script starts both the WebSocket server and HTTP server for complete robot control

echo "=========================================="
echo "Enhanced Robot Control System Startup"
echo "=========================================="

# Change to the correct directory
cd /home/ubuntu/without_ros

# Kill any existing servers on the required ports
echo "Cleaning up existing servers..."
sudo pkill -f "enhanced_robot_websocket_server.py" 2>/dev/null || true
sudo pkill -f "python.*http.server.*8080" 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

# Start the WebSocket server in the background
echo "Starting Enhanced Robot WebSocket Server on port 8765..."
python3 enhanced_robot_websocket_server.py &
WEBSOCKET_PID=$!

# Wait a moment for WebSocket server to start
sleep 3

# Start the HTTP server for the mobile interface
echo "Starting HTTP Server for mobile interface on port 8080..."
python3 -m http.server 8080 &
HTTP_PID=$!

# Wait a moment for HTTP server to start
sleep 2

echo ""
echo "=========================================="
echo "System Started Successfully!"
echo "=========================================="
echo "WebSocket Server: ws://localhost:8765 (PID: $WEBSOCKET_PID)"
echo "HTTP Server: http://localhost:8080 (PID: $HTTP_PID)"
echo ""
echo "Mobile Interface: http://localhost:8080/enhanced_mobile_robot_control.html"
echo ""
echo "Available Robot Commands:"
echo "- stand, sit, walk, forward, backward, right, left, stop"
echo "- distance (ultrasonic sensor)"
echo "- sensors (gyro/accelerometer data)"
echo "- Joystick control supported"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=========================================="

# Function to cleanup when script is terminated
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $WEBSOCKET_PID 2>/dev/null || true
    kill $HTTP_PID 2>/dev/null || true
    echo "System shutdown complete."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep the script running
while true; do
    sleep 1
done
