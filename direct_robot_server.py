#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
import os
from datetime import datetime

# Add the path to import p12-6 functions
sys.path.append('/home/ubuntu/without_ros')

# Try to import robot functions directly
try:
    # Import the functions from p12-6.py
    import importlib.util
    spec = importlib.util.spec_from_file_location("robot", "/home/ubuntu/without_ros/p12-6.py")
    robot_module = importlib.util.module_from_spec(spec)
    
    # We'll import specific functions we need
    robot_functions_available = True
except Exception as e:
    print(f"Could not import robot functions: {e}")
    robot_functions_available = False

class DirectRobotServer:
    def __init__(self):
        self.clients = set()
        self.robot_initialized = False
        
    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"Client connected. Total: {len(self.clients)}")
        
    async def unregister(self, websocket):
        self.clients.discard(websocket)
        print(f"Client disconnected. Total: {len(self.clients)}")
        
    def init_robot(self):
        """Initialize robot hardware if not already done"""
        if not self.robot_initialized:
            try:
                # Import and execute the initialization code from p12-6.py
                exec(open('/home/ubuntu/without_ros/p12-6.py').read(), globals())
                self.robot_initialized = True
                return True
            except Exception as e:
                print(f"Robot initialization failed: {e}")
                return False
        return True
    
    async def execute_robot_command(self, command):
        """Execute robot command and return result"""
        try:
            if not self.robot_initialized:
                if not self.init_robot():
                    return {"success": False, "message": "Robot initialization failed"}
            
            if command == 'stand':
                # Execute stand command
                set_pose(standing_angles)
                return {"success": True, "message": "Robot standing"}
                
            elif command == 'sit':
                # Execute sit command  
                set_pose(sitting_angles)
                return {"success": True, "message": "Robot sitting"}
                
            elif command == 'walk':
                # Execute walk command
                walk_trot(cycles=20, enable_obstacle_avoidance=True)
                return {"success": True, "message": "Robot walking completed"}
                
            elif command == 'right':
                # Execute turn right
                turn_right(cycles=15)
                return {"success": True, "message": "Right turn completed"}
                
            elif command == 'left':
                # Execute turn left
                turn_left(cycles=15)
                return {"success": True, "message": "Left turn completed"}
                
            elif command == 'distance':
                # Check distance
                distance = get_distance()
                if distance == -1:
                    return {"success": False, "message": "Sensor timeout"}
                else:
                    status = "🚨 OBSTACLE!" if distance <= 30 else "✅ Clear"
                    return {"success": True, "message": f"Distance: {distance:.2f} cm | {status}"}
            else:
                return {"success": False, "message": f"Unknown command: {command}"}
                
        except Exception as e:
            return {"success": False, "message": f"Command failed: {str(e)}"}

# Global server instance
server = DirectRobotServer()

async def handler(websocket, path):
    await server.register(websocket)
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "status",
            "message": "Connected to Direct Robot Server",
            "timestamp": datetime.now().isoformat()
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                command_type = data.get('type')
                command = data.get('command', '').lower()
                
                response = {
                    "type": "response",
                    "timestamp": datetime.now().isoformat()
                }
                
                if command_type == 'robot_command':
                    valid_commands = ['stand', 'sit', 'walk', 'right', 'left', 'distance']
                    
                    if command in valid_commands:
                        # Execute command directly
                        result = await server.execute_robot_command(command)
                        response.update(result)
                    else:
                        response["message"] = f"Invalid command. Valid: {', '.join(valid_commands)}"
                        response["success"] = False
                        
                elif command_type == 'status':
                    response["message"] = f"Robot status: {'initialized' if server.robot_initialized else 'not initialized'}"
                    response["success"] = True
                else:
                    response["message"] = "Unknown command type"
                    response["success"] = False
                
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        await server.unregister(websocket)

async def main():
    print("Starting Direct Robot WebSocket Server...")
    print("WebSocket server: ws://localhost:8765")
    print("Valid commands: stand, sit, walk, right, left, distance")
    print("Note: Robot hardware will be initialized on first command")
    
    start_server = websockets.serve(handler, "0.0.0.0", 8765)
    
    try:
        await start_server
        print("Server started successfully!")
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
