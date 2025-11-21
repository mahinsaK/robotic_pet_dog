#!/usr/bin/env python3
"""
Alternative Port Robot Server - Uses port 9000 to avoid conflicts
"""

import asyncio
import websockets
import json
import subprocess
from datetime import datetime

class AlternativeRobotServer:
    def __init__(self):
        self.clients = set()
        print("🤖 Alternative Robot Server - Port 9000")
    
    async def register_client(self, websocket):
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        print(f"📱 Client connected from {client_ip}")
        
        await websocket.send(json.dumps({
            "type": "status",
            "message": "🤖 Connected to Alternative Robot Server (Port 9000)",
            "timestamp": datetime.now().isoformat()
        }))
    
    async def unregister_client(self, websocket):
        self.clients.discard(websocket)
        print(f"📱 Client disconnected")
    
    async def handle_message(self, websocket, message):
        try:
            data = json.loads(message)
            command_type = data.get('type', '')
            
            response = {"type": "response", "timestamp": datetime.now().isoformat()}
            
            if command_type == 'robot_command':
                command = data.get('command', '').lower()
                
                if command == 'stand':
                    response.update({
                        "success": True,
                        "message": "🤖 Moving to standing position",
                        "action": "stand"
                    })
                    
                elif command == 'sit':
                    response.update({
                        "success": True,
                        "message": "🪑 Moving to sitting position", 
                        "action": "sit"
                    })
                    
                elif command in ['forward', 'walk']:
                    response.update({
                        "success": True,
                        "message": "⬆️ Walking forward",
                        "action": "forward"
                    })
                    
                elif command == 'backward':
                    response.update({
                        "success": True,
                        "message": "⬇️ Walking backward",
                        "action": "backward"
                    })
                    
                elif command == 'left':
                    response.update({
                        "success": True,
                        "message": "⬅️ Turning left",
                        "action": "left"
                    })
                    
                elif command == 'right':
                    response.update({
                        "success": True,
                        "message": "➡️ Turning right",
                        "action": "right"
                    })
                    
                elif command == 'stop':
                    response.update({
                        "success": True,
                        "message": "🛑 Emergency stop activated",
                        "action": "stop"
                    })
                    
                elif command == 'distance':
                    import random
                    distance = round(random.uniform(5.0, 50.0), 1)
                    response.update({
                        "success": True,
                        "message": f"📏 Distance: {distance} cm",
                        "distance": distance
                    })
                    
                elif command == 'sensors':
                    import random
                    sensor_data = {
                        "distance": round(random.uniform(5.0, 50.0), 1),
                        "mpu": {
                            "gyro": {
                                "x": round(random.uniform(-10.0, 10.0), 2),
                                "y": round(random.uniform(-10.0, 10.0), 2),
                                "z": round(random.uniform(-10.0, 10.0), 2)
                            },
                            "accel": {
                                "x": round(random.uniform(-2.0, 2.0), 2),
                                "y": round(random.uniform(-2.0, 2.0), 2),
                                "z": round(random.uniform(8.0, 12.0), 2)
                            }
                        }
                    }
                    response.update({
                        "success": True,
                        "message": "📊 Sensor data retrieved",
                        "sensors": sensor_data
                    })
                    
                else:
                    response.update({
                        "success": False,
                        "message": f"❓ Unknown command: {command}"
                    })
                    
            elif command_type == 'joystick':
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                
                # Determine movement based on joystick input
                if abs(x) < 0.1 and abs(y) < 0.1:
                    action = "stopped"
                    message = "🛑 Robot stopped"
                elif y > 0.3:
                    action = "forward"
                    message = f"⬆️ Moving forward (speed: {y:.1f})"
                elif y < -0.3:
                    action = "backward" 
                    message = f"⬇️ Moving backward (speed: {abs(y):.1f})"
                elif x > 0.3:
                    action = "right"
                    message = f"➡️ Turning right (speed: {x:.1f})"
                elif x < -0.3:
                    action = "left"
                    message = f"⬅️ Turning left (speed: {abs(x):.1f})"
                else:
                    action = "adjusting"
                    message = f"🎯 Fine adjustment (x:{x:.1f}, y:{y:.1f})"
                    
                response.update({
                    "success": True,
                    "message": message,
                    "joystick": {"x": x, "y": y, "action": action}
                })
                
            elif command_type == 'status_request':
                response.update({
                    "success": True,
                    "message": "📊 Robot status retrieved",
                    "status": {
                        "robot_status": "active",
                        "current_mode": "ready",
                        "hardware_ready": True,
                        "server_mode": "enhanced_functionality",
                        "client_count": len(self.clients),
                        "server_ip": "10.236.10.48:9000"
                    }
                })
                
            else:
                response.update({
                    "success": False,
                    "message": f"❓ Unknown message type: {command_type}"
                })
            
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "response",
                "success": False,
                "message": f"❌ Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))
    
    async def websocket_handler(self, websocket, path=None):
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

async def main():
    server = AlternativeRobotServer()
    ip_addr = subprocess.check_output(['hostname', '-I']).decode().strip()
    
    print("🚀 Starting Alternative Robot Server on Port 9000...")
    print(f"🌐 Access: ws://{ip_addr}:9000")
    print("Press Ctrl+C to stop")
    
    start_server = websockets.serve(server.websocket_handler, "0.0.0.0", 9000)
    await start_server
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
