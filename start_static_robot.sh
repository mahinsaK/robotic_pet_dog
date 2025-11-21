#!/bin/bash

# Static IP Robot Control Startup Script
# Launches both WebSocket and HTTP servers for static IP robot control

echo "🤖 STATIC IP ROBOT CONTROL STARTUP"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "static_ip_robot_control.html" ]; then
    print_error "static_ip_robot_control.html not found!"
    print_info "Please run this script from the /home/ubuntu/without_ros directory"
    exit 1
fi

# Function to cleanup processes on exit
cleanup() {
    echo ""
    print_warning "Shutting down servers..."
    
    # Kill background processes
    if [ ! -z "$WEBSOCKET_PID" ]; then
        kill $WEBSOCKET_PID 2>/dev/null
    fi
    if [ ! -z "$HTTP_PID" ]; then
        kill $HTTP_PID 2>/dev/null
    fi
    
    # Wait a moment for clean shutdown
    sleep 2
    
    print_success "Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_info "Checking Python environment..."

# Activate virtual environment if available
if [ -f "/home/ubuntu/.venv/bin/activate" ]; then
    source /home/ubuntu/.venv/bin/activate
    print_success "Virtual environment activated"
else
    print_warning "Virtual environment not found, using system Python"
fi

# Check for required packages
python3 -c "import websockets" 2>/dev/null
if [ $? -ne 0 ]; then
    print_warning "Installing websockets package..."
    pip3 install websockets
    if [ $? -eq 0 ]; then
        print_success "websockets installed"
    else
        print_error "Failed to install websockets"
        exit 1
    fi
else
    print_success "websockets package available"
fi

print_info "Starting Static IP Robot Control System..."
echo ""

# Start WebSocket server in background
print_info "🔌 Starting Robot WebSocket Server (port 8765)..."
python3 static_robot_server.py &
WEBSOCKET_PID=$!

# Wait a moment for WebSocket server to start
sleep 2

# Check if WebSocket server started successfully
if ! kill -0 $WEBSOCKET_PID 2>/dev/null; then
    print_error "Failed to start WebSocket server"
    exit 1
fi

print_success "WebSocket server started (PID: $WEBSOCKET_PID)"

# Start HTTP server in background  
print_info "🌐 Starting HTTP Web Server (port 8080)..."
python3 static_web_server.py &
HTTP_PID=$!

# Wait a moment for HTTP server to start
sleep 2

# Check if HTTP server started successfully
if ! kill -0 $HTTP_PID 2>/dev/null; then
    print_error "Failed to start HTTP server"
    print_error "Cleaning up WebSocket server..."
    kill $WEBSOCKET_PID 2>/dev/null
    exit 1
fi

print_success "HTTP server started (PID: $HTTP_PID)"
echo ""

# Display access information
echo "🎉 STATIC IP ROBOT CONTROL SYSTEM READY!"
echo "========================================"
echo ""
echo "📱 ACCESS URLS:"
echo "   http://localhost:8080/static_ip_robot_control.html"
echo "   http://10.236.10.48:8080/static_ip_robot_control.html"
echo "   http://10.21.12.48:8080/static_ip_robot_control.html"
echo ""
echo "🔗 WEBSOCKET SERVERS:"
echo "   ws://localhost:8765 (local)"
echo "   ws://10.236.10.48:8765 (network)"
echo "   ws://10.21.12.48:8765 (network)"
echo ""
echo "✨ FEATURES:"
echo "   ✅ Multiple connection options"
echo "   ✅ Direct and relay server support"
echo "   ✅ Auto IP address detection"
echo "   ✅ Real-time status monitoring"
echo "   ✅ Keyboard shortcuts"
echo "   ✅ Emergency stop"
echo ""
echo "🎮 KEYBOARD SHORTCUTS:"
echo "   W - Walk    S - Sit      A - Left"
echo "   D - Right   X - Stand    Q - Emergency Stop"
echo "   Space - Distance sensor"
echo ""
echo "📋 INSTRUCTIONS:"
echo "   1. Open the URL above in your web browser"
echo "   2. Select connection type (Direct/Relay/Custom)"
echo "   3. Click 'Connect to Robot'"
echo "   4. Use the control buttons or keyboard shortcuts"
echo ""
echo "🛑 Press Ctrl+C to stop all servers"
echo "========================================"

# Keep script running and wait for signals
wait
