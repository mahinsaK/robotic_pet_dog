#!/usr/bin/env python3
"""
Simple HTTP Server for Robot Control Web Interface
Serves the robot_control.html file and makes it accessible from mobile devices
"""

import http.server
import socketserver
import os
import socket

# Configuration
HTTP_PORT = 8080
WEBSOCKET_PORT = 8765

def get_local_ip():
    """Get the local IP address of the Raspberry Pi"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "localhost"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[HTTP] {self.address_string()} - {format % args}")

def main():
    # Change to the directory containing robot_control.html
    web_dir = "/home/ubuntu/without_ros"
    os.chdir(web_dir)
    
    # Get local IP address
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("🌐 ROBOT CONTROL WEB SERVER")
    print("=" * 60)
    print(f"📱 Access from your phone:")
    print(f"   http://{local_ip}:{HTTP_PORT}/robot_control.html")
    print(f"   http://10.236.10.48:{HTTP_PORT}/robot_control.html")
    print()
    print(f"🔌 WebSocket server should be running on:")
    print(f"   ws://10.236.10.48:{WEBSOCKET_PORT}")
    print()
    print("📋 Setup checklist:")
    print("   ✓ Make sure your phone is on the same WiFi network")
    print("   ✓ Start the WebSocket server: python3 working_robot_server.py")
    print("   ✓ Open the URL above in your phone's browser")
    print()
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Create and start the HTTP server
    try:
        with socketserver.TCPServer(("", HTTP_PORT), CustomHTTPRequestHandler) as httpd:
            print(f"[HTTP] Server started on port {HTTP_PORT}")
            print(f"[HTTP] Serving files from: {web_dir}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[HTTP] Server stopped by user")
    except Exception as e:
        print(f"[HTTP] Server error: {e}")

if __name__ == "__main__":
    main()
