#!/usr/bin/env python3
"""
Robust WebSocket Robot Server with Enhanced Compatibility
Uses more lenient WebSocket handling for mobile devices
"""

import asyncio
import websockets
import json
import sys
import subprocess
from datetime import datetime

class RobustRobotServer:
    def __init__(self):
        self.clients = set()
        self.robot_status = "idle"
        self.current_mode = "standing"
        self.hardware_ready = False
        
        print("🤖 Robust Robot Server initialized")
        print("🌐 Enhanced mobile compatibility enabled")
    
    async def register_client(self, websocket):
        """Register new WebSocket client with enhanced compatibility"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        print(f"📱 Client connected from {client_ip}. Total: {len(self.clients)}")
        
        # Send welcome message
        try:
            await self.send_to_client(websocket, {
                "type": "status",
                "message": "🤖 Connected to Robust Robot Server",
                "server_mode": "robust_compatibility",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"⚠️ Error sending welcome message: {e}")
    
    async def unregister_client(self, websocket):
        """Unregister WebSocket client"""
        self.clients.discard(websocket)
        print(f"📱 Client disconnected. Total: {len(self.clients)}")
    
    async def send_to_client(self, websocket, data):
        """Send data to specific client with error handling"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            self.clients.discard(websocket)
        except Exception as e:
            print(f"⚠️ Send error: {e}")
    
    async def handle_client_message(self, websocket, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            command_type = data.get('type', '')
            
            response = {"type": "response", "timestamp": datetime.now().isoformat()}
            
            if command_type == 'robot_command':
                command = data.get('command', '').lower()
                response.update({
                    "success": True,
                    "message": f"🤖 Executing command: {command}",
                    "command": command
                })
                
            elif command_type == 'joystick':
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                response.update({
                    "success": True,
                    "message": f"🕹️ Joystick input: x={x:.2f}, y={y:.2f}",
                    "joystick": {"x": x, "y": y}
                })
                
            elif command_type == 'status_request':
                response.update({
                    "success": True,
                    "message": "📊 Status retrieved",
                    "status": {
                        "robot_status": self.robot_status,
                        "current_mode": self.current_mode,
                        "hardware_ready": self.hardware_ready,
                        "server_mode": "robust_compatibility",
                        "client_count": len(self.clients)
                    }
                })
                
            else:
                response.update({
                    "success": False,
                    "message": f"❓ Unknown message type: {command_type}"
                })
            
            await self.send_to_client(websocket, response)
            
        except json.JSONDecodeError:
            await self.send_to_client(websocket, {
                "type": "response",
                "success": False,
                "message": "❌ Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            await self.send_to_client(websocket, {
                "type": "response",
                "success": False,
                "message": f"❌ Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def websocket_handler(self, websocket, path=None):
        """Enhanced WebSocket connection handler with better error handling"""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        print(f"🔌 New connection from {client_ip}")
        
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"📱 Connection closed: {client_ip}")
        except Exception as e:
            print(f"❌ WebSocket error from {client_ip}: {e}")
        finally:
            await self.unregister_client(websocket)

async def main():
    robot_server = RobustRobotServer()
    
    # Get IP address
    try:
        ip_addr = subprocess.check_output(['hostname', '-I']).decode().strip()
    except:
        ip_addr = "localhost"
    
    print("🚀 Starting Robust Robot WebSocket Server...")
    print(f"🌐 Local access: ws://localhost:8765")
    print(f"🌐 Network access: ws://{ip_addr}:8765")
    print("📱 Enhanced mobile device compatibility")
    print("🤖 Available commands: stand, sit, walk, forward, backward, right, left, stop, distance, sensors")
    print("🕹️ Joystick control supported")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        # Create server with enhanced compatibility settings
        start_server = websockets.serve(
            robot_server.websocket_handler, 
            "0.0.0.0", 
            8765,
            ping_interval=20,  # Ping every 20 seconds
            ping_timeout=10,   # Timeout after 10 seconds
            close_timeout=10   # Close timeout
        )
        await start_server
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
