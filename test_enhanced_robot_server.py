#!/usr/bin/env python3
"""
Enhanced Robot WebSocket Server - Test Mode
This version runs without hardware for testing the interface
"""

import asyncio
import websockets
import json
import time
import threading
from datetime import datetime

class TestRobotServer:
    def __init__(self):
        self.clients = set()
        self.robot_status = "test_mode"
        self.current_mode = "idle"
        self.walking = False
        self.hardware_ready = False  # Test mode - no hardware
        
        # Mock sensor data
        self.mock_distance = 25.0
        self.mock_gyro = {"x": 0.1, "y": -0.2, "z": 0.05}
        self.mock_accel = {"x": 0.0, "y": 0.0, "z": 9.8}
        
        print("🧪 Test Robot Server initialized (No hardware required)")
    
    def get_distance(self):
        """Mock distance sensor"""
        import random
        self.mock_distance += random.uniform(-2, 2)
        self.mock_distance = max(5, min(50, self.mock_distance))
        return round(self.mock_distance, 2)
    
    def get_mpu_data(self):
        """Mock MPU6050 data"""
        import random
        
        # Add some random variation
        self.mock_gyro["x"] += random.uniform(-0.1, 0.1)
        self.mock_gyro["y"] += random.uniform(-0.1, 0.1)
        self.mock_gyro["z"] += random.uniform(-0.1, 0.1)
        
        self.mock_accel["x"] += random.uniform(-0.2, 0.2)
        self.mock_accel["y"] += random.uniform(-0.2, 0.2)
        
        return {"gyro": self.mock_gyro.copy(), "accel": self.mock_accel.copy()}
    
    # Mock robot movement functions
    def stand(self):
        """Mock stand function"""
        self.current_mode = "standing"
        time.sleep(0.5)  # Simulate movement time
        return True
    
    def sit(self):
        """Mock sit function"""
        self.current_mode = "sitting"
        time.sleep(0.5)
        return True
    
    def walk_forward(self, cycles=5):
        """Mock walk forward"""
        self.current_mode = "walking_forward"
        time.sleep(cycles * 0.2)  # Simulate walking time
        return True
    
    def walk_backward(self, cycles=5):
        """Mock walk backward"""
        self.current_mode = "walking_backward"
        time.sleep(cycles * 0.2)
        return True
    
    def turn_right(self, cycles=10):
        """Mock turn right"""
        self.current_mode = "turning_right"
        time.sleep(cycles * 0.1)
        return True
    
    def turn_left(self, cycles=10):
        """Mock turn left"""
        self.current_mode = "turning_left"
        time.sleep(cycles * 0.1)
        return True
    
    def emergency_stop(self):
        """Mock emergency stop"""
        self.current_mode = "stopped"
        return True
    
    def execute_movement_threaded(self, movement_func, *args, **kwargs):
        """Execute movement in separate thread"""
        def run_movement():
            result = movement_func(*args, **kwargs)
            self.current_mode = "idle"
        
        thread = threading.Thread(target=run_movement, daemon=True)
        thread.start()
    
    # WebSocket Server Functions
    async def register_client(self, websocket):
        """Register new WebSocket client"""
        self.clients.add(websocket)
        print(f"Client connected. Total: {len(self.clients)}")
        
        # Send initial status
        await self.send_to_client(websocket, {
            "type": "status",
            "message": "Connected to Test Robot Server (No hardware required)",
            "robot_status": self.robot_status,
            "current_mode": self.current_mode,
            "hardware_ready": self.hardware_ready,
            "timestamp": datetime.now().isoformat()
        })
    
    async def unregister_client(self, websocket):
        """Unregister WebSocket client"""
        self.clients.discard(websocket)
        print(f"Client disconnected. Total: {len(self.clients)}")
    
    async def send_to_client(self, websocket, data):
        """Send data to specific client"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def broadcast_to_all(self, data):
        """Broadcast data to all clients"""
        if self.clients:
            await asyncio.gather(
                *[self.send_to_client(client, data) for client in self.clients],
                return_exceptions=True
            )
    
    async def handle_joystick_command(self, data):
        """Handle joystick input commands"""
        try:
            x = float(data.get('x', 0))
            y = float(data.get('y', 0))
            
            # Deadzone threshold
            threshold = 0.3
            
            if abs(x) < threshold and abs(y) < threshold:
                # Center position - stop movement
                self.emergency_stop()
                return {"success": True, "message": "Movement stopped (TEST MODE)"}
            
            # Determine primary direction
            if abs(y) > abs(x):
                # Forward/Backward movement
                if y > threshold:
                    # Forward
                    cycles = int(abs(y) * 10)
                    self.execute_movement_threaded(self.walk_forward, cycles)
                    return {"success": True, "message": f"Walking forward - TEST MODE (cycles: {cycles})"}
                elif y < -threshold:
                    # Backward
                    cycles = int(abs(y) * 10)
                    self.execute_movement_threaded(self.walk_backward, cycles)
                    return {"success": True, "message": f"Walking backward - TEST MODE (cycles: {cycles})"}
            else:
                # Left/Right movement
                if x > threshold:
                    # Right
                    cycles = int(abs(x) * 15)
                    self.execute_movement_threaded(self.turn_right, cycles)
                    return {"success": True, "message": f"Turning right - TEST MODE (cycles: {cycles})"}
                elif x < -threshold:
                    # Left
                    cycles = int(abs(x) * 15)
                    self.execute_movement_threaded(self.turn_left, cycles)
                    return {"success": True, "message": f"Turning left - TEST MODE (cycles: {cycles})"}
            
            return {"success": False, "message": "Invalid joystick input"}
            
        except Exception as e:
            return {"success": False, "message": f"Joystick error: {str(e)}"}
    
    async def handle_client_message(self, websocket, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            command_type = data.get('type', '')
            
            response = {"type": "response", "timestamp": datetime.now().isoformat()}
            
            if command_type == 'robot_command':
                command = data.get('command', '').lower()
                
                if command == 'stand':
                    success = self.stand()
                    response.update({
                        "success": success,
                        "message": "Moving to standing position - TEST MODE" if success else "Failed to stand"
                    })
                
                elif command == 'sit':
                    success = self.sit()
                    response.update({
                        "success": success,
                        "message": "Moving to sitting position - TEST MODE" if success else "Failed to sit"
                    })
                
                elif command == 'walk' or command == 'forward':
                    self.execute_movement_threaded(self.walk_forward, 10)
                    response.update({
                        "success": True,
                        "message": "Walking forward - TEST MODE"
                    })
                
                elif command == 'backward':
                    self.execute_movement_threaded(self.walk_backward, 10)
                    response.update({
                        "success": True,
                        "message": "Walking backward - TEST MODE"
                    })
                
                elif command == 'right':
                    self.execute_movement_threaded(self.turn_right, 15)
                    response.update({
                        "success": True,
                        "message": "Turning right - TEST MODE"
                    })
                
                elif command == 'left':
                    self.execute_movement_threaded(self.turn_left, 15)
                    response.update({
                        "success": True,
                        "message": "Turning left - TEST MODE"
                    })
                
                elif command == 'stop' or command == 'q':
                    self.emergency_stop()
                    response.update({
                        "success": True,
                        "message": "Emergency stop activated - TEST MODE"
                    })
                
                elif command == 'distance':
                    distance = self.get_distance()
                    response.update({
                        "success": True,
                        "message": f"Distance: {distance} cm (MOCK DATA)",
                        "distance": distance
                    })
                
                elif command == 'sensors':
                    sensor_data = {
                        "distance": self.get_distance(),
                        "mpu": self.get_mpu_data()
                    }
                    response.update({
                        "success": True,
                        "message": "Sensor data retrieved (MOCK DATA)",
                        "sensors": sensor_data
                    })
                
                else:
                    response.update({
                        "success": False,
                        "message": f"Unknown command: {command}"
                    })
            
            elif command_type == 'joystick':
                joystick_response = await self.handle_joystick_command(data)
                response.update(joystick_response)
            
            elif command_type == 'status_request':
                status_data = {
                    "robot_status": self.robot_status,
                    "current_mode": self.current_mode,
                    "hardware_ready": self.hardware_ready,
                    "walking": self.walking
                }
                response.update({
                    "success": True,
                    "message": "Status retrieved - TEST MODE",
                    "status": status_data
                })
            
            else:
                response.update({
                    "success": False,
                    "message": f"Unknown message type: {command_type}"
                })
            
            await self.send_to_client(websocket, response)
            
        except json.JSONDecodeError:
            await self.send_to_client(websocket, {
                "type": "response",
                "success": False,
                "message": "Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            await self.send_to_client(websocket, {
                "type": "response",
                "success": False,
                "message": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def websocket_handler(self, websocket, path=None):
        """Main WebSocket connection handler"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

# Main server startup
async def main():
    robot_server = TestRobotServer()
    
    print("🧪 Starting Enhanced Robot WebSocket Server - TEST MODE")
    print("=" * 60)
    print("🔧 No hardware required - perfect for testing the interface!")
    print("WebSocket server: ws://localhost:8765")
    print("Available commands: stand, sit, walk, forward, backward, right, left, stop, distance, sensors")
    print("🕹️ Joystick control supported")
    print("📊 Mock sensor data provided")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        start_server = websockets.serve(robot_server.websocket_handler, "0.0.0.0", 8765)
        await start_server
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\n🛑 Shutting down test server...")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
