#!/usr/bin/env python3
"""
Real Robot Dog Mobile Control Server
Integrates mobile interface with actual robot hardware control
"""

import asyncio
import websockets
import json
import subprocess
import threading
import queue
import time
from datetime import datetime

class RealRobotDogServer:
    def __init__(self):
        self.robot_process = None
        self.command_queue = queue.Queue()
        self.clients = set()
        self.robot_status = "stopped"
        self.loop = None
        self.dog_state = "sitting"
        self.last_command = "none"
        
        print("🐕 REAL Robot Dog Control Server - Port 9000")
        print("🔥 This server controls ACTUAL robot hardware!")
        
    async def register_client(self, websocket):
        """Register new WebSocket client"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        print(f"📱 Dog owner connected from {client_ip}")
        
        await websocket.send(json.dumps({
            "type": "status", 
            "message": "🐕 Connected to REAL Robot Dog! Hardware control ready.",
            "dog_state": self.dog_state,
            "robot_status": self.robot_status,
            "timestamp": datetime.now().isoformat()
        }))
    
    async def unregister_client(self, websocket):
        """Unregister WebSocket client"""
        self.clients.discard(websocket)
        print(f"📱 Dog owner disconnected")
    
    def start_robot_process(self):
        """Start the real robot control process"""
        if self.robot_process is None or self.robot_process.poll() is not None:
            try:
                # Start the actual robot control process (enhanced_p12-6.py)
                python_path = '/home/ubuntu/.venv/bin/python'
                robot_script = '/home/ubuntu/without_ros/enhanced_p12-6.py'
                
                self.robot_process = subprocess.Popen(
                    [python_path, robot_script],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd='/home/ubuntu/without_ros'
                )
                self.robot_status = "running"
                
                # Start thread to read robot output
                threading.Thread(target=self.read_robot_output, daemon=True).start()
                
                print("🤖 Real robot process started successfully")
                return True
            except Exception as e:
                print(f"❌ Failed to start robot process: {e}")
                self.robot_status = "error"
                return False
        return True
    
    def read_robot_output(self):
        """Read output from robot process and broadcast to clients"""
        if self.robot_process:
            try:
                for line in iter(self.robot_process.stdout.readline, ''):
                    if line:
                        try:
                            if self.loop and not self.loop.is_closed():
                                asyncio.run_coroutine_threadsafe(
                                    self.broadcast_to_all({
                                        "type": "robot_output",
                                        "message": f"🤖 {line.strip()}",
                                        "timestamp": datetime.now().isoformat()
                                    }), self.loop
                                )
                        except Exception as e:
                            print(f"Robot output: {line.strip()}")
            except Exception as e:
                print(f"Error reading robot output: {e}")
    
    def send_robot_command(self, command):
        """Send command to real robot process"""
        if self.robot_process and self.robot_process.poll() is None:
            try:
                self.robot_process.stdin.write(command + '\n')
                self.robot_process.stdin.flush()
                print(f"🤖 Sent to real robot: {command}")
                return True
            except Exception as e:
                print(f"❌ Failed to send command: {e}")
                return False
        else:
            print("❌ Robot process is not running")
            return False
    
    async def broadcast_to_all(self, data):
        """Send data to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[self.send_to_client(client, data) for client in self.clients],
                return_exceptions=True
            )
    
    async def send_to_client(self, websocket, data):
        """Send data to specific client"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def handle_message(self, websocket, message):
        """Handle incoming messages from mobile interface"""
        try:
            data = json.loads(message)
            command_type = data.get('type', '')
            
            response = {"type": "response", "timestamp": datetime.now().isoformat()}
            
            if command_type == 'robot_command':
                command = data.get('command', '').lower()
                
                # Map mobile commands to robot commands
                robot_command_map = {
                    'stand': 'stand',
                    'sit': 'sit', 
                    'forward': 'walk',
                    'walk': 'walk',
                    'backward': 'backward',  # Now supported!
                    'left': 'left',
                    'right': 'right',
                    'stop': 'stop',  # Now uses emergency stop instead of quit
                    'distance': 'distance'
                }
                
                if command in robot_command_map:
                    # Start robot if not running
                    if self.robot_status != "running":
                        if not self.start_robot_process():
                            response.update({
                                "success": False,
                                "message": "❌ Failed to start robot hardware"
                            })
                            await websocket.send(json.dumps(response))
                            return
                        await asyncio.sleep(2)  # Wait for robot to initialize
                    
                    # Send actual command to robot
                    robot_cmd = robot_command_map[command]
                    
                    if command == 'stand':
                        self.dog_state = "standing"
                        self.last_command = "stand"
                        if self.send_robot_command(robot_cmd):
                            response.update({
                                "success": True,
                                "message": "🐕 REAL DOG: Standing up!",
                                "action": "stand",
                                "dog_state": self.dog_state
                            })
                        else:
                            response.update({
                                "success": False,
                                "message": "❌ Failed to send stand command to robot"
                            })
                            
                    elif command == 'sit':
                        self.dog_state = "sitting"
                        self.last_command = "sit"
                        if self.send_robot_command(robot_cmd):
                            response.update({
                                "success": True,
                                "message": "🐕 REAL DOG: Sitting down! Good dog!",
                                "action": "sit",
                                "dog_state": self.dog_state
                            })
                        else:
                            response.update({
                                "success": False,
                                "message": "❌ Failed to send sit command to robot"
                            })
                            
                    elif command in ['forward', 'walk']:
                        self.dog_state = "walking"
                        self.last_command = "walk"
                        if self.send_robot_command(robot_cmd):
                            response.update({
                                "success": True,
                                "message": "🐕 REAL DOG: Walking forward! 🦴",
                                "action": "forward",
                                "dog_state": self.dog_state
                            })
                        else:
                            response.update({
                                "success": False,
                                "message": "❌ Failed to send walk command to robot"
                            })
                            
                    elif command == 'backward':
                        self.dog_state = "walking"
                        self.last_command = "backward"
                        if self.send_robot_command(robot_cmd):
                            response.update({
                                "success": True,
                                "message": "🐕 REAL DOG: Walking backward! 🐾",
                                "action": "backward",
                                "dog_state": self.dog_state
                            })
                        else:
                            response.update({
                                "success": False,
                                "message": "❌ Failed to send backward command to robot"
                            })
                            
                    elif command == 'left':
                        self.dog_state = "turning"
                        self.last_command = "left"
                        if self.send_robot_command(robot_cmd):
                            response.update({
                                "success": True,
                                "message": "🐕 REAL DOG: Turning left!",
                                "action": "left",
                                "dog_state": self.dog_state
                            })
                        else:
                            response.update({
                                "success": False,
                                "message": "❌ Failed to send left command to robot"
                            })
                            
                    elif command == 'right':
                        self.dog_state = "turning"
                        self.last_command = "right"
                        if self.send_robot_command(robot_cmd):
                            response.update({
                                "success": True,
                                "message": "🐕 REAL DOG: Turning right!",
                                "action": "right", 
                                "dog_state": self.dog_state
                            })
                        else:
                            response.update({
                                "success": False,
                                "message": "❌ Failed to send right command to robot"
                            })
                            
                    elif command == 'distance':
                        if self.send_robot_command(robot_cmd):
                            response.update({
                                "success": True,
                                "message": "🐕 REAL DOG: Checking distance sensor...",
                                "action": "distance"
                            })
                        else:
                            response.update({
                                "success": False,
                                "message": "❌ Failed to get distance reading"
                            })
                            
                    elif command == 'stop':
                        self.dog_state = "stopped"
                        self.last_command = "stop"
                        if self.send_robot_command(robot_cmd):
                            response.update({
                                "success": True,
                                "message": "🐕 REAL DOG: Emergency stop! Stopping all movement!",
                                "action": "stop",
                                "dog_state": self.dog_state
                            })
                        else:
                            response.update({
                                "success": False,
                                "message": "❌ Failed to send stop command"
                            })
                
                elif command == 'sensors':
                    # For sensors, we'll return robot status instead of hardware sensors
                    response.update({
                        "success": True,
                        "message": f"🐕 REAL DOG Status: {self.dog_state} | Robot: {self.robot_status}",
                        "sensors": {
                            "dog_state": self.dog_state,
                            "robot_status": self.robot_status,
                            "last_command": self.last_command,
                            "hardware_connected": self.robot_process is not None
                        }
                    })
                    
                else:
                    response.update({
                        "success": False,
                        "message": f"🐕 Unknown command: {command}"
                    })
                    
            elif command_type == 'joystick':
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                
                # Convert joystick to robot commands
                if abs(x) < 0.1 and abs(y) < 0.1:
                    # Center - no movement needed for real robot
                    response.update({
                        "success": True,
                        "message": "🐕 REAL DOG: Standing still",
                        "joystick": {"x": x, "y": y, "action": "stopped"}
                    })
                elif y > 0.5:  # Strong forward
                    if self.send_robot_command('walk'):
                        response.update({
                            "success": True,
                            "message": f"🐕 REAL DOG: Walking forward! (intensity: {y:.1f})",
                            "joystick": {"x": x, "y": y, "action": "forward"}
                        })
                elif x > 0.5:  # Strong right
                    if self.send_robot_command('right'):
                        response.update({
                            "success": True,
                            "message": f"🐕 REAL DOG: Turning right! (intensity: {x:.1f})",
                            "joystick": {"x": x, "y": y, "action": "right"}
                        })
                elif x < -0.5:  # Strong left
                    if self.send_robot_command('left'):
                        response.update({
                            "success": True,
                            "message": f"🐕 REAL DOG: Turning left! (intensity: {abs(x):.1f})",
                            "joystick": {"x": x, "y": y, "action": "left"}
                        })
                else:
                    response.update({
                        "success": True,
                        "message": f"🐕 Small joystick movement - no action taken",
                        "joystick": {"x": x, "y": y, "action": "minor"}
                    })
                    
            elif command_type == 'status_request':
                response.update({
                    "success": True,
                    "message": f"🐕 REAL Robot Dog Status",
                    "status": {
                        "dog_state": self.dog_state,
                        "robot_status": self.robot_status,
                        "last_command": self.last_command,
                        "hardware_connected": self.robot_process is not None,
                        "server_mode": "REAL_HARDWARE_CONTROL",
                        "client_count": len(self.clients)
                    }
                })
                
            else:
                response.update({
                    "success": False,
                    "message": f"🐕 Unknown message type: {command_type}"
                })
            
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "response",
                "success": False,
                "message": f"🐕 Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))
    
    async def websocket_handler(self, websocket, path=None):
        """Main WebSocket connection handler"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

async def main():
    server = RealRobotDogServer()
    ip_addr = subprocess.check_output(['hostname', '-I']).decode().strip()
    
    print("🚀 Starting REAL Robot Dog Control Server on Port 9000...")
    print(f"🌐 Mobile Access: http://{ip_addr}:8080/enhanced_mobile_robot_control.html")
    print(f"🌐 WebSocket: ws://{ip_addr}:9000")
    print("🔥 THIS SERVER CONTROLS REAL HARDWARE!")
    print("🐕 Ready to control your physical robot dog!")
    print("📱 Use your mobile device to give commands")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Store event loop reference
    server.loop = asyncio.get_running_loop()
    
    start_server = websockets.serve(server.websocket_handler, "0.0.0.0", 9000)
    await start_server
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
