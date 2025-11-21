#!/usr/bin/env python3
import asyncio
import websockets
import json
import subprocess
import os
from datetime import datetime

connected_clients = set()

async def register_client(websocket):
    connected_clients.add(websocket)
    print(f"Client connected. Total: {len(connected_clients)}")

async def unregister_client(websocket):
    connected_clients.discard(websocket)
    print(f"Client disconnected. Total: {len(connected_clients)}")

async def send_response(websocket, message, success=True):
    response = {
        "type": "response",
        "message": message,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    try:
        await websocket.send(json.dumps(response))
    except:
        pass

def execute_robot_command(command):
    """Execute robot command using subprocess.run with timeout"""
    try:
        # Create a script that imports and executes specific functions
        if command == 'stand':
            script_content = """
import sys
sys.path.append('/home/ubuntu/without_ros')
# Read the file and exclude the interactive main loop (from line 342 onwards)
with open('/home/ubuntu/without_ros/p12-6.py', 'r') as f:
    lines = f.readlines()
# Execute only the first 341 lines (functions and definitions)
exec(''.join(lines[:341]))
print("Moving to standing mode...")
set_pose(standing_angles)
print("Standing pose completed.")
"""
        elif command == 'sit':
            script_content = """
import sys
sys.path.append('/home/ubuntu/without_ros')
with open('/home/ubuntu/without_ros/p12-6.py', 'r') as f:
    lines = f.readlines()
exec(''.join(lines[:341]))
print("Moving to sitting mode...")
set_pose(sitting_angles)
print("Sitting pose completed.")
"""
        elif command == 'walk':
            script_content = """
import sys
sys.path.append('/home/ubuntu/without_ros')
with open('/home/ubuntu/without_ros/p12-6.py', 'r') as f:
    lines = f.readlines()
exec(''.join(lines[:341]))
print("Starting walk mode...")
walk_trot(cycles=20)
print("Walk completed.")
"""
        elif command == 'right':
            script_content = """
import sys
sys.path.append('/home/ubuntu/without_ros')
with open('/home/ubuntu/without_ros/p12-6.py', 'r') as f:
    lines = f.readlines()
exec(''.join(lines[:341]))
print("Turning right...")
turn_right(cycles=15)
print("Right turn completed.")
"""
        elif command == 'left':
            script_content = """
import sys
sys.path.append('/home/ubuntu/without_ros')
with open('/home/ubuntu/without_ros/p12-6.py', 'r') as f:
    lines = f.readlines()
exec(''.join(lines[:341]))
print("Turning left...")
turn_left(cycles=15)
print("Left turn completed.")
"""
        elif command == 'distance':
            script_content = """
import sys
sys.path.append('/home/ubuntu/without_ros')
with open('/home/ubuntu/without_ros/p12-6.py', 'r') as f:
    lines = f.readlines()
exec(''.join(lines[:341]))
print("Measuring distance...")
distance = get_distance()
if distance == -1:
    print("Sensor timeout - check ultrasonic sensor connections")
else:
    status = "🚨 OBSTACLE!" if distance <= 30 else "✅ Clear"
    print(f"Distance: {distance:.2f} cm | {status}")
"""
        else:
            return False, f"Unknown command: {command}"
        
        # Write temporary script
        with open('/tmp/robot_cmd.py', 'w') as f:
            f.write(script_content)
        
        # Run the command with a short timeout using the virtual environment Python
        result = subprocess.run([
            '/home/ubuntu/.venv/bin/python', '/tmp/robot_cmd.py'
        ], 
        text=True, 
        capture_output=True, 
        timeout=20,
        cwd='/home/ubuntu/without_ros'
        )
        
        if result.returncode == 0:
            return True, f"Command '{command}' executed successfully. Output: {result.stdout.strip()}"
        else:
            return False, f"Command failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, f"Command '{command}' timed out"
    except Exception as e:
        return False, f"Error executing command: {str(e)}"
    finally:
        # Clean up temp file
        try:
            os.remove('/tmp/robot_cmd.py')
        except:
            pass

async def handle_websocket(websocket):
    await register_client(websocket)
    
    # Send welcome message
    try:
        await websocket.send(json.dumps({
            "type": "status",
            "message": "Connected to Robot WebSocket Server",
            "timestamp": datetime.now().isoformat()
        }))
    except:
        await unregister_client(websocket)
        return
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                command_type = data.get('type')
                command = data.get('command', '').lower()
                
                if command_type == 'robot_command':
                    valid_commands = ['stand', 'sit', 'walk', 'right', 'left', 'distance']
                    
                    if command in valid_commands:
                        print(f"Executing command: {command}")
                        success, message = execute_robot_command(command)
                        await send_response(websocket, message, success)
                    else:
                        await send_response(websocket, 
                            f"Invalid command. Valid: {', '.join(valid_commands)}", 
                            False)
                        
                elif command_type == 'status':
                    await send_response(websocket, "Robot server is ready")
                    
                else:
                    await send_response(websocket, "Unknown command type", False)
                    
            except json.JSONDecodeError:
                await send_response(websocket, "Invalid JSON format", False)
            except Exception as e:
                await send_response(websocket, f"Server error: {str(e)}", False)
                
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await unregister_client(websocket)

async def main():
    print("Starting Robot WebSocket Server...")
    print("WebSocket server: ws://localhost:8765")
    print("Valid commands: stand, sit, walk, right, left, distance")
    print("Press Ctrl+C to stop")
    
    server = await websockets.serve(handle_websocket, "0.0.0.0", 8765)
    
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
