#!/usr/bin/env python3
"""
Enhanced Robot WebSocket Server with Complete Control Functions
Supports joystick controls, all robot movements, and sensors
"""

import asyncio
import websockets
import json
import sys
import os
import time
import threading
import subprocess
from datetime import datetime

# Add the robot control modules to path
sys.path.append('/home/ubuntu/without_ros')

# Import robot control functions
try:
    # Import hardware components
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    import numpy as np
    
    # Import sensor libraries
    try:
        import RPi.GPIO as GPIO
        GPIO_AVAILABLE = True
    except:
        GPIO_AVAILABLE = False
    
    try:
        from mpu6050 import mpu6050
        MPU_AVAILABLE = True
    except:
        MPU_AVAILABLE = False
        
    HARDWARE_AVAILABLE = True
except ImportError as e:
    print(f"Hardware imports not available: {e}")
    HARDWARE_AVAILABLE = False

class EnhancedRobotServer:
    def __init__(self):
        self.clients = set()
        self.robot_status = "stopped"
        self.current_mode = "idle"
        self.walking = False
        self.obstacle_avoidance = True
        
        # Initialize hardware if available
        if HARDWARE_AVAILABLE:
            self.init_hardware()
        else:
            self.hardware_ready = False
            
        # Robot state tracking
        self.current_angles = {}
        self.sensor_data = {}
        
        # Joystick control state
        self.joystick_active = False
        self.movement_thread = None
        self.movement_stop_event = threading.Event()
        
    def init_hardware(self):
        """Initialize all hardware components"""
        # Always define robot poses and servo types (even without hardware)
        self.servo_types = {
            0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
            6: "180", 8: "270", 9: "270", 10: "180", 12: "180",
            13: "270", 14: "180"
        }
        
        # Robot poses
        self.standing_angles = {
            0: 200, 1: 10, 2: 145,    # Front Left
            4: 100, 5: 115, 6: 10,    # Front Right
            8: 220, 9: 19, 10: 150,   # Rear Left
            12: 120, 13: 110, 14: 5   # Rear Right
        }
        
        self.sitting_angles = {
            0: 207, 1: 70, 2: 50,     # Front Left
            4: 90, 5: 55, 6: 110,     # Front Right
            8: 220, 9: 79, 10: 50,    # Rear Left
            12: 115, 13: 45, 14: 105  # Rear Right
        }
        
        # Initialize current angles
        self.current_angles = {ch: (90 if self.servo_types[ch] == "180" else 135) 
                             for ch in self.servo_types}
        
        try:
            # Try to initialize I2C and PCA9685
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.pwm = PCA9685(self.i2c)
            self.pwm.frequency = 50
            
            # Clear all PWM outputs
            for i in range(16):
                self.pwm.channels[i].duty_cycle = 0
            
            # Initialize sensors
            self.init_sensors()
            
            self.hardware_ready = True
            print("Hardware initialized successfully")
            
        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            self.hardware_ready = False
            # Initialize sensors with fallback
            self.init_sensors()
    
    def init_sensors(self, fallback=False):
        """Initialize sensors"""
        # Ultrasonic sensor pins
        self.TRIG_PIN = 24
        self.ECHO_PIN = 23
        
        # Initialize GPIO for ultrasonic sensor
        if GPIO_AVAILABLE and not fallback:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.TRIG_PIN, GPIO.OUT)
                GPIO.setup(self.ECHO_PIN, GPIO.IN)
                GPIO.output(self.TRIG_PIN, False)
                self.gpio_ready = True
            except Exception as e:
                print(f"GPIO initialization failed: {e}")
                self.gpio_ready = False
        else:
            self.gpio_ready = False
        
        # MPU6050 sensor
        if MPU_AVAILABLE and not fallback:
            try:
                self.mpu = mpu6050(0x68)
                self.mpu_ready = True
                print("MPU6050 sensor initialized")
            except Exception as e:
                print(f"MPU6050 initialization failed: {e}")
                self.mpu_ready = False
        else:
            self.mpu_ready = False
            print("MPU6050 sensor disabled or not available")
    
    def angle_to_pwm(self, angle, servo_type):
        """Convert angle to PWM value"""
        if servo_type == "180":
            min_angle, max_angle = 0, 180
        else:
            min_angle, max_angle = 0, 270
        min_pwm, max_pwm = 100, 500
        angle = max(min(angle, max_angle), min_angle)
        return int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))
    
    def set_pose(self, target_angles, transition_time=0.3, steps=50):
        """Smoothly transition to target pose"""
        if not self.hardware_ready:
            return False
            
        step_angles = {}
        for ch in target_angles:
            start = self.current_angles.get(ch, 90 if self.servo_types[ch] == "180" else 135)
            end = target_angles[ch]
            step_angles[ch] = np.linspace(start, end, steps)

        for i in range(steps):
            for ch in target_angles:
                angle = step_angles[ch][i]
                pwm_value = self.angle_to_pwm(angle, self.servo_types[ch])
                try:
                    self.pwm.channels[ch].duty_cycle = int(pwm_value * 65535 / 4096)
                except Exception as e:
                    print(f"Error setting PWM on channel {ch}: {e}")
            time.sleep(transition_time / steps)

        self.current_angles.update(target_angles)
        return True
    
    def get_distance(self):
        """Get ultrasonic sensor distance"""
        if not GPIO_AVAILABLE:
            return 50  # Mock distance
            
        try:
            GPIO.output(self.TRIG_PIN, True)
            time.sleep(0.00001)
            GPIO.output(self.TRIG_PIN, False)
            
            start_time = time.time()
            stop_time = time.time()
            
            while GPIO.input(self.ECHO_PIN) == 0:
                start_time = time.time()
                
            while GPIO.input(self.ECHO_PIN) == 1:
                stop_time = time.time()
                
            time_elapsed = stop_time - start_time
            distance = (time_elapsed * 34300) / 2
            
            return round(distance, 2)
        except:
            return 50  # Default safe distance
    
    def get_mpu_data(self):
        """Get MPU6050 sensor data"""
        if not self.mpu_ready:
            return {"gyro": {"x": 0, "y": 0, "z": 0}, "accel": {"x": 0, "y": 0, "z": 0}}
        
        try:
            gyro_data = self.mpu.get_gyro_data()
            accel_data = self.mpu.get_accel_data()
            return {"gyro": gyro_data, "accel": accel_data}
        except:
            return {"gyro": {"x": 0, "y": 0, "z": 0}, "accel": {"x": 0, "y": 0, "z": 0}}
    
    # Robot Movement Functions
    def stand(self):
        """Move robot to standing position"""
        self.current_mode = "standing"
        return self.set_pose(self.standing_angles)
    
    def sit(self):
        """Move robot to sitting position"""
        self.current_mode = "sitting"
        return self.set_pose(self.sitting_angles)
    
    def walk_forward(self, cycles=5):
        """Walk forward with trot gait"""
        if not self.hardware_ready:
            return False
            
        self.current_mode = "walking_forward"
        
        # Walking phases for forward movement
        walking_phases = {
            "front_right": [
                {5: 115, 6: 10},   # Move forward
                {5: 85, 6: 5},     # Lift leg
                {5: 85, 6: 20},    # Push back
                {5: 105, 6: 20}    # Lower leg
            ],
            "front_left": [
                {1: 10, 2: 145},   # Move forward
                {1: 40, 2: 140},   # Lift leg
                {1: 40, 2: 155},   # Push back
                {1: 20, 2: 155}    # Lower leg
            ],
            "rear_right": [
                {13: 110, 14: 5},  # Move forward
                {13: 80, 14: 0},   # Lift leg
                {13: 80, 14: 15},  # Push back
                {13: 100, 14: 15}  # Lower leg
            ],
            "rear_left": [
                {9: 19, 10: 150},  # Move forward
                {9: 49, 10: 145},  # Lift leg
                {9: 49, 10: 160},  # Push back
                {9: 29, 10: 160}   # Lower leg
            ]
        }
        
        try:
            for cycle in range(cycles):
                if self.movement_stop_event.is_set():
                    break
                    
                for phase_idx in range(4):
                    # Diagonal gait pattern
                    rl_fr = phase_idx
                    rr_fl = (phase_idx + 2) % 4

                    angles = self.sitting_angles.copy()
                    angles.update(walking_phases["rear_left"][rl_fr])
                    angles.update(walking_phases["front_right"][rl_fr])
                    angles.update(walking_phases["rear_right"][rr_fl])
                    angles.update(walking_phases["front_left"][rr_fl])

                    self.set_pose(angles, transition_time=0.1, steps=10)
                    time.sleep(0.05)
                    
                    # Check for obstacles
                    if self.obstacle_avoidance and self.get_distance() < 15:
                        break
            
            self.set_pose(self.sitting_angles, transition_time=0.2)
            return True
        except Exception as e:
            print(f"Walk forward error: {e}")
            return False
    
    def walk_backward(self, cycles=5):
        """Walk backward (reverse of forward)"""
        if not self.hardware_ready:
            return False
            
        self.current_mode = "walking_backward"
        
        # Backward walking phases (reverse of forward)
        walking_phases = {
            "front_right": [
                {5: 65, 6: 120},   # Phase 4: Move forward (now Phase 1: Move backward)
                {5: 35, 6: 125},   # Phase 3: Lift leg (now Phase 2)
                {5: 35, 6: 110},   # Phase 2: Push back (now Phase 3)
                {5: 55, 6: 110}    # Phase 1: Lower leg (now Phase 4)
            ],
            "front_left": [
                {1: 60, 2: 40},    # Phase 4: Move forward (now Phase 1)
                {1: 90, 2: 35},    # Phase 3: Lift leg (now Phase 2)
                {1: 90, 2: 50},    # Phase 2: Push back (now Phase 3)
                {1: 70, 2: 50}     # Phase 1: Lower leg (now Phase 4)
            ],
            "rear_right": [
                {13: 55, 14: 115}, # Phase 4: Move forward (now Phase 1)
                {13: 25, 14: 120}, # Phase 3: Lift leg (now Phase 2)
                {13: 25, 14: 105}, # Phase 2: Push back (now Phase 3)
                {13: 45, 14: 105}  # Phase 1: Lower leg (now Phase 4)
            ],
            "rear_left": [
                {9: 69, 10: 40},   # Phase 4: Move forward (now Phase 1)
                {9: 99, 10: 35},   # Phase 3: Lift leg (now Phase 2)
                {9: 99, 10: 50},   # Phase 2: Push back (now Phase 3)
                {9: 79, 10: 50}    # Phase 1: Lower leg (now Phase 4)
            ]
        }
        
        try:
            for cycle in range(cycles):
                if self.movement_stop_event.is_set():
                    break
                    
                for phase_idx in range(4):
                    rl_fr = phase_idx
                    rr_fl = (phase_idx + 2) % 4

                    angles = self.sitting_angles.copy()
                    angles.update(walking_phases["rear_left"][rl_fr])
                    angles.update(walking_phases["front_right"][rl_fr])
                    angles.update(walking_phases["rear_right"][rr_fl])
                    angles.update(walking_phases["front_left"][rr_fl])

                    self.set_pose(angles, transition_time=0.1, steps=10)
                    time.sleep(0.05)
            
            self.set_pose(self.sitting_angles, transition_time=0.2)
            return True
        except Exception as e:
            print(f"Walk backward error: {e}")
            return False
    
    def turn_right(self, cycles=10):
        """Turn robot right"""
        if not self.hardware_ready:
            return False
            
        self.current_mode = "turning_right"
        
        try:
            for cycle in range(cycles):
                if self.movement_stop_event.is_set():
                    break
                    
                # Right turn movement
                turn_angles = self.sitting_angles.copy()
                turn_angles.update({
                    1: 40, 2: 100,    # Front left leg forward
                    13: 80, 14: 50,   # Rear right leg forward
                })
                self.set_pose(turn_angles, transition_time=0.15, steps=15)
                time.sleep(0.1)
                
                # Return to sitting
                self.set_pose(self.sitting_angles, transition_time=0.15, steps=15)
                time.sleep(0.1)
                
            return True
        except Exception as e:
            print(f"Turn right error: {e}")
            return False
    
    def turn_left(self, cycles=10):
        """Turn robot left"""
        if not self.hardware_ready:
            return False
            
        self.current_mode = "turning_left"
        
        try:
            for cycle in range(cycles):
                if self.movement_stop_event.is_set():
                    break
                    
                # Left turn movement
                turn_angles = self.sitting_angles.copy()
                turn_angles.update({
                    5: 85, 6: 60,     # Front right leg forward
                    9: 49, 10: 100,   # Rear left leg forward
                })
                self.set_pose(turn_angles, transition_time=0.15, steps=15)
                time.sleep(0.1)
                
                # Return to sitting
                self.set_pose(self.sitting_angles, transition_time=0.15, steps=15)
                time.sleep(0.1)
                
            return True
        except Exception as e:
            print(f"Turn left error: {e}")
            return False
    
    def emergency_stop(self):
        """Emergency stop - stop all movement"""
        self.movement_stop_event.set()
        self.current_mode = "stopped"
        if self.movement_thread and self.movement_thread.is_alive():
            self.movement_thread.join(timeout=1.0)
        self.sit()
        return True
    
    def shutdown_robot(self):
        """Safely shutdown robot"""
        self.emergency_stop()
        if self.hardware_ready:
            # Reset all servos to neutral
            for channel, servo_type in self.servo_types.items():
                neutral_angle = 90 if servo_type == "180" else 135
                pwm_value = self.angle_to_pwm(neutral_angle, servo_type)
                self.pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
                time.sleep(0.01)
            time.sleep(0.5)
            for i in range(16):
                self.pwm.channels[i].duty_cycle = 0
            self.pwm.deinit()
    
    # WebSocket Server Functions
    async def register_client(self, websocket):
        """Register new WebSocket client"""
        self.clients.add(websocket)
        print(f"Client connected. Total: {len(self.clients)}")
        
        # Send initial status (simplified)
        try:
            await self.send_to_client(websocket, {
                "type": "status",
                "message": "Connected to Enhanced Robot Server",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error sending initial status: {e}")
    
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
    
    def execute_movement_threaded(self, movement_func, *args, **kwargs):
        """Execute movement in separate thread"""
        self.movement_stop_event.clear()
        self.movement_thread = threading.Thread(
            target=movement_func, 
            args=args, 
            kwargs=kwargs,
            daemon=True
        )
        self.movement_thread.start()
    
    async def handle_joystick_command(self, data):
        """Handle joystick input commands"""
        try:
            x = float(data.get('x', 0))
            y = float(data.get('y', 0))
            
            # Determine movement based on joystick position
            # Deadzone threshold
            threshold = 0.3
            
            if abs(x) < threshold and abs(y) < threshold:
                # Center position - stop movement
                self.emergency_stop()
                return {"success": True, "message": "Movement stopped"}
            
            # Determine primary direction
            if abs(y) > abs(x):
                # Forward/Backward movement
                if y > threshold:
                    # Forward
                    cycles = int(abs(y) * 10)  # Scale based on joystick magnitude
                    self.execute_movement_threaded(self.walk_forward, cycles)
                    return {"success": True, "message": f"Walking forward (cycles: {cycles})"}
                elif y < -threshold:
                    # Backward
                    cycles = int(abs(y) * 10)
                    self.execute_movement_threaded(self.walk_backward, cycles)
                    return {"success": True, "message": f"Walking backward (cycles: {cycles})"}
            else:
                # Left/Right movement
                if x > threshold:
                    # Right
                    cycles = int(abs(x) * 15)
                    self.execute_movement_threaded(self.turn_right, cycles)
                    return {"success": True, "message": f"Turning right (cycles: {cycles})"}
                elif x < -threshold:
                    # Left
                    cycles = int(abs(x) * 15)
                    self.execute_movement_threaded(self.turn_left, cycles)
                    return {"success": True, "message": f"Turning left (cycles: {cycles})"}
            
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
                        "message": "Moving to standing position" if success else "Failed to stand"
                    })
                
                elif command == 'sit':
                    success = self.sit()
                    response.update({
                        "success": success,
                        "message": "Moving to sitting position" if success else "Failed to sit"
                    })
                
                elif command == 'walk' or command == 'forward':
                    self.execute_movement_threaded(self.walk_forward, 10)
                    response.update({
                        "success": True,
                        "message": "Walking forward"
                    })
                
                elif command == 'backward':
                    self.execute_movement_threaded(self.walk_backward, 10)
                    response.update({
                        "success": True,
                        "message": "Walking backward"
                    })
                
                elif command == 'right':
                    self.execute_movement_threaded(self.turn_right, 15)
                    response.update({
                        "success": True,
                        "message": "Turning right"
                    })
                
                elif command == 'left':
                    self.execute_movement_threaded(self.turn_left, 15)
                    response.update({
                        "success": True,
                        "message": "Turning left"
                    })
                
                elif command == 'stop' or command == 'q':
                    self.emergency_stop()
                    response.update({
                        "success": True,
                        "message": "Emergency stop activated"
                    })
                
                elif command == 'distance':
                    distance = self.get_distance()
                    response.update({
                        "success": True,
                        "message": f"Distance: {distance} cm",
                        "distance": distance
                    })
                
                elif command == 'sensors':
                    sensor_data = {
                        "distance": self.get_distance(),
                        "mpu": self.get_mpu_data()
                    }
                    response.update({
                        "success": True,
                        "message": "Sensor data retrieved",
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
                    "walking": self.walking,
                    "obstacle_avoidance": self.obstacle_avoidance
                }
                response.update({
                    "success": True,
                    "message": "Status retrieved",
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
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        print(f"🔌 New connection attempt from {client_ip}")
        
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"📱 Client {client_ip} disconnected")
        except Exception as e:
            print(f"❌ WebSocket error from {client_ip}: {e}")
        finally:
            await self.unregister_client(websocket)

# Main server startup
async def main():
    robot_server = EnhancedRobotServer()
    
    print("Starting Enhanced Robot WebSocket Server...")
    print(f"🌐 WebSocket server: ws://0.0.0.0:8765")
    print(f"🌐 External access: ws://{subprocess.check_output(['hostname', '-I']).decode().strip()}:8765")
    print("Available commands: stand, sit, walk, forward, backward, right, left, stop, distance, sensors")
    print("Joystick control supported")
    print("Press Ctrl+C to stop")
    

    try:
        start_server = websockets.serve(robot_server.websocket_handler, "0.0.0.0", 9000)
        await start_server
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down server...")
        robot_server.shutdown_robot()
    except Exception as e:
        print(f"Server error: {e}")
        robot_server.shutdown_robot()

if __name__ == "__main__":
    asyncio.run(main())
