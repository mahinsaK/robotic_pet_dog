#!/bin/bash

# Enhanced Robot Dog Mobile Control - FIXED VERSION
echo "🐕 Enhanced Robot Dog Mobile Control System"
echo "🔥 NOW WITH PROPER STOP AND BACKWARD FUNCTIONS!"
echo "=============================================="

# Get the IP address
IP_ADDR=$(hostname -I | tr -d ' ')

# Kill any existing servers
echo "🧹 Cleaning up existing servers..."
pkill -f "real_robot_dog_server.py" 2>/dev/null || true
pkill -f "python.*http.server.*8080" 2>/dev/null || true
sleep 2

# Change to correct directory
cd /home/ubuntu/without_ros

# Start the enhanced dog control server
echo "🐕 Starting Enhanced Robot Dog Control Server..."
python3 real_robot_dog_server.py &
DOG_SERVER_PID=$!
sleep 3

# Start the HTTP server for mobile interface
echo "📱 Starting Mobile Interface Server..."
python3 -m http.server 8080 &
HTTP_SERVER_PID=$!
sleep 2

echo ""
echo "🎉 Enhanced Robot Dog Control System Ready!"
echo "=============================================="
echo "📱 Open this on your mobile device:"
echo "   http://$IP_ADDR:8080/enhanced_mobile_robot_control.html"
echo ""
echo "🔗 WebSocket Server: ws://$IP_ADDR:9000"
echo "🐕 Enhanced Dog Server PID: $DOG_SERVER_PID"
echo "📱 Mobile Server PID: $HTTP_SERVER_PID"
echo ""
echo "🔥 NEW FEATURES ADDED:"
echo "✅ Emergency Stop - Now properly stops robot movement!"
echo "✅ Backward Walking - Real backward movement!"
echo "✅ Enhanced Robot Script - Uses enhanced_p12-6.py"
echo ""
echo "🎮 HOW TO CONTROL YOUR DOG:"
echo "1. Open the URL above on your mobile browser"
echo "2. Make sure Server URL shows: ws://$IP_ADDR:9000"
echo "3. Click 'Connect'"
echo "4. Try these commands:"
echo "   🏠 Stand - Robot stands up"
echo "   🪑 Sit - Robot sits down"
echo "   ⬆️ Forward - Robot walks forward"
echo "   ⬇️ Backward - Robot walks backward (NEW!)"
echo "   🛑 Emergency Stop - Immediate stop (FIXED!)"
echo "   📏 Distance - Check sensor"
echo "   🕹️ Joystick - Smooth movement control"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=============================================="

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping Enhanced Robot Dog Control System..."
    kill $DOG_SERVER_PID 2>/dev/null || true
    kill $HTTP_SERVER_PID 2>/dev/null || true
    echo "🐕 Enhanced robot dog is now sleeping. Goodbye!"
    exit 0
}

# Set up signal handler
trap cleanup SIGINT SIGTERM

# Keep script running
while true; do
    sleep 1
done
