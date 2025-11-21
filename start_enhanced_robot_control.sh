#!/bin/bash
"""
Enhanced Robot Control System Startup Script
Starts the WebSocket server and opens the control interface
"""

echo "🤖 Starting Enhanced Robot Control System..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "/home/ubuntu/.venv" ]; then
    print_error "Virtual environment not found at /home/ubuntu/.venv"
    exit 1
fi

# Check if enhanced server exists
if [ ! -f "/home/ubuntu/without_ros/enhanced_robot_websocket_server.py" ]; then
    print_error "Enhanced robot server not found!"
    exit 1
fi

# Make the enhanced server executable
chmod +x /home/ubuntu/without_ros/enhanced_robot_websocket_server.py

print_status "Starting Enhanced Robot WebSocket Server..."

# Start the enhanced server in background
/home/ubuntu/.venv/bin/python /home/ubuntu/without_ros/enhanced_robot_websocket_server.py &
SERVER_PID=$!

print_success "Enhanced Robot WebSocket Server started with PID: $SERVER_PID"

# Wait a moment for server to start
sleep 2

# Get local IP address for mobile access
LOCAL_IP=$(hostname -I | cut -d' ' -f1)

print_status "Starting HTTP server for mobile interface..."

# Start HTTP server for mobile interface
cd /home/ubuntu/without_ros
python3 -m http.server 8080 &
HTTP_PID=$!

print_success "HTTP server started with PID: $HTTP_PID"

echo ""
print_success "🎉 Enhanced Robot Control System is running!"
echo "========================================"
echo ""
print_status "📱 Access URLs:"
echo "   Local:    http://localhost:8080/enhanced_mobile_robot_control.html"
echo "   Mobile:   http://$LOCAL_IP:8080/enhanced_mobile_robot_control.html"
echo ""
print_status "🤖 WebSocket Server:"
echo "   Local:    ws://localhost:8765"
echo "   Mobile:   ws://$LOCAL_IP:8765"
echo ""
print_status "📋 Features Available:"
echo "   • 🕹️  Joystick control (drag to move)"
echo "   • 🎮 Button controls (stand, sit, walk, etc.)"
echo "   • 📊 Live sensor data (distance, gyro, accelerometer)"
echo "   • ⚡ Real-time robot status updates"
echo "   • 🛑 Emergency stop functionality"
echo ""
print_status "⌨️  Keyboard Controls (when connected):"
echo "   • W/S: Forward/Backward"
echo "   • A/D: Left/Right turns"
echo "   • Q/E: Stand/Sit"
echo "   • Space: Emergency Stop"
echo ""
print_warning "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "Shutting down Enhanced Robot Control System..."
    
    if kill -0 $SERVER_PID 2>/dev/null; then
        print_status "Stopping WebSocket server (PID: $SERVER_PID)..."
        kill $SERVER_PID
    fi
    
    if kill -0 $HTTP_PID 2>/dev/null; then
        print_status "Stopping HTTP server (PID: $HTTP_PID)..."
        kill $HTTP_PID
    fi
    
    print_success "Enhanced Robot Control System stopped."
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop the script
while true; do
    sleep 1
    
    # Check if servers are still running
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        print_error "WebSocket server stopped unexpectedly!"
        break
    fi
    
    if ! kill -0 $HTTP_PID 2>/dev/null; then
        print_error "HTTP server stopped unexpectedly!"
        break
    fi
done

cleanup
