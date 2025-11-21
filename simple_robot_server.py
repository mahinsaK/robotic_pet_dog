#!/usr/bin/env python3
import asyncio
import websockets
import json
import subprocess
import threading
import time
from datetime import datetime

class SimpleRobotServer:
    def __init__(self):
        self.robot_process = None
        self.clients = set()
        
    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"Client connected. Total: {len(self.clients)}")
        
    async def unregister(self, websocket):
        self.clients.discard(websocket)
        print(f"Client disconnected. Total: {len(self.clients)}")
        
    async def broadcast(self, message):
        if self.clients:
            disconnected = []
            for client in self.clients:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.append(client)
            
            # Remove disconnected clients
            for client in disconnected:
                self.clients.discard(client)
    
    def start_robot(self):
        if self.robot_process is None or self.robot_process.poll() is not None:
            try:
                # Don't start the subprocess automatically - just return True
                # We'll simulate the robot being "ready"
                print("Robot marked as ready (no subprocess started)")
                return True
            except Exception as e:
                print(f"Failed to start robot: {e}")
                return False
        return True
    
    def send_command(self, command):
        # Instead of subprocess, we'll execute commands by calling the p12-6.py script directly
        try:
            import subprocess
            result = subprocess.run([
                'python3', '/home/ubuntu/without_ros/p12-6.py'
            ], input=f"{command}\nq\n", text=True, capture_output=True, timeout=30)
            
            print(f"Sent command: {command}")
            print(f"Robot output: {result.stdout}")
            if result.stderr:
                print(f"Robot errors: {result.stderr}")
            return True
        except subprocess.TimeoutExpired:
            print(f"Command {command} timed out")
            return False
        except Exception as e:
            print(f"Send failed: {e}")
            return False
    
    def stop_robot(self):
        if self.robot_process and self.robot_process.poll() is None:
            try:
                self.robot_process.stdin.write('q\n')
                self.robot_process.stdin.flush()
                time.sleep(1)
                if self.robot_process.poll() is None:
                    self.robot_process.terminate()
                print("Robot stopped")
                return True
            except Exception as e:
                print(f"Stop failed: {e}")
                return False
        return True

# Global server instance
server = SimpleRobotServer()

async def handler(websocket, path):
    await server.register(websocket)
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "status",
            "message": "Connected to Robot Server",
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
                    valid_commands = ['stand', 'sit', 'walk', 'right', 'left', 'distance', 'q']
                    
                    if command in valid_commands:
                        if command == 'q':
                            # Just acknowledge the stop command
                            response["message"] = "Robot stop acknowledged"
                        else:
                            # Send command directly (no need to start subprocess)
                            if server.send_command(command):
                                response["message"] = f"Command '{command}' executed successfully"
                                response["success"] = True
                            else:
                                response["message"] = f"Failed to execute '{command}'"
                                response["success"] = False
                    else:
                        response["message"] = f"Invalid command. Valid: {', '.join(valid_commands)}"
                        response["success"] = False
                        
                elif command_type == 'status':
                    response["message"] = "Robot status: ready"
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
    finally:
        await server.unregister(websocket)

async def main():
    print("Starting Simple Robot WebSocket Server...")
    print("WebSocket server: ws://localhost:8765")
    print("Valid commands: stand, sit, walk, right, left, distance, q")
    
    start_server = websockets.serve(handler, "0.0.0.0", 8765)
    
    try:
        await start_server
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop_robot()

if __name__ == "__main__":
    asyncio.run(main())
