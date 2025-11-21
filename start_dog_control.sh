#!/bin/bash

# Robot Dog Mobile Control - Complete Setup Script
echo "🐕 Robot Dog Mobile Control System"
echo "=================================="

# Get the IP address
IP_ADDR=$(hostname -I | tr -d ' ')

# Kill any existing servers
echo "🧹 Cleaning up existing servers..."
pkill -f "enhanced_dog_server.py" 2>/dev/null || true
pkill -f "python.*http.server.*8080" 2>/dev/null || true
sleep 2

# Change to correct directory
cd /home/ubuntu/without_ros

# Start the dog control server
echo "🐕 Starting Robot Dog Control Server..."
python3 enhanced_dog_server.py &
DOG_SERVER_PID=$!
sleep 3

# Start the HTTP server for mobile interface
echo "📱 Starting Mobile Interface Server..."
python3 -m http.server 8080 &
HTTP_SERVER_PID=$!
sleep 2

echo ""
echo "🎉 Robot Dog Control System Ready!"
echo "=================================="
echo "📱 Open this on your mobile device:"
echo "   http://$IP_ADDR:8080/enhanced_mobile_robot_control.html"
echo ""
echo "🔗 WebSocket Server: ws://$IP_ADDR:9000"
echo "🐕 Dog Control Server PID: $DOG_SERVER_PID"
echo "📱 Mobile Server PID: $HTTP_SERVER_PID"
echo ""
echo "🎮 HOW TO CONTROL YOUR DOG:"
echo "1. Open the URL above on your mobile browser"
echo "2. Make sure Server URL shows: ws://$IP_ADDR:9000"
echo "3. Click 'Connect'"
echo "4. Use buttons: Stand, Sit, Forward, etc."
echo "5. Try the joystick for smooth movement"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=================================="

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping Robot Dog Control System..."
    kill $DOG_SERVER_PID 2>/dev/null || true
    kill $HTTP_SERVER_PID 2>/dev/null || true
    echo "🐕 Robot dog is now sleeping. Goodbye!"
    exit 0
}

# Set up signal handler
trap cleanup SIGINT SIGTERM

# Keep script running
while true; do
    sleep 1
done
