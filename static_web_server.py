#!/usr/bin/env python3
"""
Simple HTTP server for static IP robot control
"""

import http.server
import socketserver
import os
import sys
import signal
from pathlib import Path

class RobotHTTPServer:
    def __init__(self, port=8080):
        self.port = port
        self.httpd = None
        
    def start(self):
        """Start the HTTP server"""
        # Change to the directory containing the HTML files
        web_dir = Path(__file__).parent
        os.chdir(web_dir)
        
        handler = http.server.SimpleHTTPRequestHandler
        
        try:
            self.httpd = socketserver.TCPServer(("", self.port), handler)
            
            print("=" * 60)
            print("🌐 STATIC IP ROBOT CONTROL WEB SERVER")
            print("=" * 60)
            print(f"📱 Access the robot control interface at:")
            print(f"   http://localhost:{self.port}/static_ip_robot_control.html")
            print(f"   http://10.236.10.48:{self.port}/static_ip_robot_control.html")
            print(f"   http://10.21.12.48:{self.port}/static_ip_robot_control.html")
            print("")
            print("🔧 Features:")
            print("   ✅ Multiple connection options (direct/relay/custom)")
            print("   ✅ Auto IP detection")
            print("   ✅ Connection status monitoring")
            print("   ✅ Keyboard shortcuts (W/A/S/D/X/Q/Space)")
            print("   ✅ Emergency stop functionality")
            print("")
            print("🛑 Press Ctrl+C to stop the server")
            print("=" * 60)
            
            # Setup signal handler
            signal.signal(signal.SIGINT, self.signal_handler)
            
            print(f"[HTTP] Server started on port {self.port}")
            self.httpd.serve_forever()
            
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"❌ Port {self.port} is already in use!")
                print("💡 Try stopping other servers or use a different port")
                sys.exit(1)
            else:
                raise
        except Exception as e:
            print(f"❌ Server error: {e}")
            sys.exit(1)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Shutting down web server...")
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        print("✅ Web server stopped")
        sys.exit(0)

if __name__ == "__main__":
    server = RobotHTTPServer()
    server.start()
