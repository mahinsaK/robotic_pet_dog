#!/usr/bin/env python3

import asyncio
import websockets
import json

async def test_robot_commands():
    """Test various robot commands"""
    uri = "ws://localhost:8765"
    
    try:
        print(f"Attempting to connect to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected to Enhanced Robot Server")
            print("Testing various commands...\n")
            
            # Test commands
            commands = [
                {"type": "robot_command", "command": "stand"},
                {"type": "robot_command", "command": "sit"},
                {"type": "robot_command", "command": "sensors"},
                {"type": "robot_command", "command": "distance"},
                {"type": "joystick", "x": 0.5, "y": 0.8},  # Forward movement
                {"type": "joystick", "x": -0.3, "y": 0.0}, # Left turn
                {"type": "robot_command", "command": "stop"},
                {"type": "status_request"}
            ]
            
            for i, cmd in enumerate(commands, 1):
                print(f"Test {i}: Sending {cmd}")
                await websocket.send(json.dumps(cmd))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"Response: {response}")
                except asyncio.TimeoutError:
                    print("No response received (timeout)")
                
                print()
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_robot_commands())
