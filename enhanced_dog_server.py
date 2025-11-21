#!/usr/bin/env python3
"""
Enhanced Dog Control Server - More intuitive responses for robot dog control
"""

import asyncio
import websockets
import json
import subprocess
from datetime import datetime

class DogControlServer:
    def __init__(self):
        self.clients = set()
        self.dog_state = "sitting"  # sitting, standing, walking, turning
        self.last_command = "none"
        print("🐕 Robot Dog Control Server - Port 9000")
        print("🎮 Ready for mobile dog control commands!")
    
    async def register_client(self, websocket):
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        print(f"📱 Dog owner connected from {client_ip}")
        
        await websocket.send(json.dumps({
            "type": "status",
            "message": "🐕 Connected to Robot Dog! Ready for commands.",
            "dog_state": self.dog_state,
            "timestamp": datetime.now().isoformat()
        }))
    
    async def unregister_client(self, websocket):
        self.clients.discard(websocket)
        print(f"📱 Dog owner disconnected")
    
    async def handle_message(self, websocket, message):
        try:
            data = json.loads(message)
            command_type = data.get('type', '')
            
            response = {"type": "response", "timestamp": datetime.now().isoformat()}
            
            if command_type == 'robot_command':
                command = data.get('command', '').lower()
                
                if command == 'stand':
                    self.dog_state = "standing"
                    self.last_command = "stand"
                    response.update({
                        "success": True,
                        "message": "🐕 Good dog! Standing up...",
                        "action": "stand",
                        "dog_state": self.dog_state
                    })
                    
                elif command == 'sit':
                    self.dog_state = "sitting" 
                    self.last_command = "sit"
                    response.update({
                        "success": True,
                        "message": "🐕 Sit! Good boy/girl! 🍖",
                        "action": "sit",
                        "dog_state": self.dog_state
                    })
                    
                elif command in ['forward', 'walk']:
                    self.dog_state = "walking"
                    self.last_command = "walk"
                    response.update({
                        "success": True,
                        "message": "🐕 Walkies time! Walking forward 🦴",
                        "action": "forward",
                        "dog_state": self.dog_state
                    })
                    
                elif command == 'backward':
                    self.dog_state = "walking"
                    self.last_command = "backward"
                    response.update({
                        "success": True,
                        "message": "🐕 Backing up carefully... 🐾",
                        "action": "backward",
                        "dog_state": self.dog_state
                    })
                    
                elif command == 'left':
                    self.dog_state = "turning"
                    self.last_command = "left"
                    response.update({
                        "success": True,
                        "message": "🐕 Turning left! Following your lead 🎾",
                        "action": "left",
                        "dog_state": self.dog_state
                    })
                    
                elif command == 'right':
                    self.dog_state = "turning"
                    self.last_command = "right"
                    response.update({
                        "success": True,
                        "message": "🐕 Turning right! Where are we going? 🏃‍♂️",
                        "action": "right",
                        "dog_state": self.dog_state
                    })
                    
                elif command == 'stop':
                    self.dog_state = "standing"
                    self.last_command = "stop"
                    response.update({
                        "success": True,
                        "message": "🐕 STOP! Good dog, staying put! 🛑",
                        "action": "stop",
                        "dog_state": self.dog_state
                    })
                    
                elif command == 'distance':
                    import random
                    distance = round(random.uniform(5.0, 50.0), 1)
                    
                    if distance < 10:
                        alert = "⚠️ Something close ahead!"
                    elif distance < 20:
                        alert = "👀 Obstacle detected nearby"
                    else:
                        alert = "✅ Path looks clear"
                        
                    response.update({
                        "success": True,
                        "message": f"🐕 Sniffing around... {alert}",
                        "distance": distance,
                        "alert": alert
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
                    
                    # Dog-like status based on sensor data
                    if abs(sensor_data["mpu"]["gyro"]["x"]) > 5:
                        status = "🐕 I'm tilting! Need to balance!"
                    elif sensor_data["distance"] < 10:
                        status = "🐕 Sniffing something close by..."
                    else:
                        status = "🐕 Feeling good and ready to play!"
                    
                    response.update({
                        "success": True,
                        "message": status,
                        "sensors": sensor_data,
                        "dog_state": self.dog_state
                    })
                    
                else:
                    response.update({
                        "success": False,
                        "message": f"🐕 Woof? I don't understand '{command}'. Try: stand, sit, forward, etc."
                    })
                    
            elif command_type == 'joystick':
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                
                # Determine dog movement based on joystick
                if abs(x) < 0.1 and abs(y) < 0.1:
                    self.dog_state = "standing"
                    action = "stopped"
                    message = "🐕 Standing still like a good dog!"
                elif y > 0.3:
                    self.dog_state = "walking"
                    action = "forward"
                    message = f"🐕 Running forward! Speed: {y:.1f} 🏃‍♂️💨"
                elif y < -0.3:
                    self.dog_state = "walking"
                    action = "backward" 
                    message = f"🐕 Backing up cautiously... Speed: {abs(y):.1f} 🐾"
                elif x > 0.3:
                    self.dog_state = "turning"
                    action = "right"
                    message = f"🐕 Spinning right! Chasing my tail? Speed: {x:.1f} 🌀"
                elif x < -0.3:
                    self.dog_state = "turning"
                    action = "left"
                    message = f"🐕 Turning left! Following the scent... Speed: {abs(x):.1f} 👃"
                else:
                    self.dog_state = "adjusting"
                    action = "adjusting"
                    message = f"🐕 Making small adjustments... (x:{x:.1f}, y:{y:.1f})"
                    
                response.update({
                    "success": True,
                    "message": message,
                    "joystick": {"x": x, "y": y, "action": action},
                    "dog_state": self.dog_state
                })
                
            elif command_type == 'status_request':
                response.update({
                    "success": True,
                    "message": f"🐕 Dog Status: {self.dog_state.title()} | Last: {self.last_command}",
                    "status": {
                        "dog_state": self.dog_state,
                        "last_command": self.last_command,
                        "robot_status": "active",
                        "current_mode": "dog_control",
                        "hardware_ready": True,
                        "server_mode": "enhanced_dog_control",
                        "client_count": len(self.clients),
                        "server_ip": "10.236.10.48:9000"
                    }
                })
                
            else:
                response.update({
                    "success": False,
                    "message": f"🐕 Woof? Unknown command type: {command_type}"
                })
            
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "response",
                "success": False,
                "message": f"🐕 Oops! Something went wrong: {str(e)}",
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
    server = DogControlServer()
    ip_addr = subprocess.check_output(['hostname', '-I']).decode().strip()
    
    print("🚀 Starting Enhanced Dog Control Server on Port 9000...")
    print(f"🌐 Mobile Access: http://{ip_addr}:8080/enhanced_mobile_robot_control.html")
    print(f"🌐 WebSocket: ws://{ip_addr}:9000")
    print("🐕 Ready to control your robot dog!")
    print("📱 Use your mobile device to give commands")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    start_server = websockets.serve(server.websocket_handler, "0.0.0.0", 9000)
    await start_server
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
