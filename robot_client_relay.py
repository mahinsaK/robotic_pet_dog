# robot_client_relay.py - Robot WebSocket Client for Relay Server
import asyncio
import websockets
import json
import time
import threading
import numpy as np
import board
import busio
from adafruit_pca9685 import PCA9685
import RPi.GPIO as GPIO
import signal
import sys

# --- Configuration ---
RELAY_URL = "ws://localhost:8765"  # Replace with your relay server's URL

# --- Robot logic and movement functions ---

# Initialize I2C bus
try:
    i2c = busio.I2C(board.SCL, board.SDA)
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit(1)

# Initialize PCA9685
try:
    pwm = PCA9685(i2c)
    pwm.frequency = 50  # 50 Hz for servos
except Exception as e:
    print(f"Error initializing PCA9685: {e}")
    exit(1)

# Clear all PWM outputs at startup
for i in range(16):
    pwm.channels[i].duty_cycle = 0

# Touch sensor configuration
TOUCH_PIN = 26  # GPIO26

# Ultrasonic sensor configuration
TRIG = 23  # GPIO23
ECHO = 24  # GPIO24

def setup_sensors():
    """Initialize GPIO pins for touch and ultrasonic sensors"""
    GPIO.setmode(GPIO.BCM)
    # Touch sensor setup
    GPIO.setup(TOUCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # Ultrasonic sensor setup
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("Ultrasonic sensor initialized")

def cleanup_gpio(signum=None, frame=None):
    """Clean up GPIO and PWM on exit"""
    print("\nCleaning up GPIO and PWM...")
    
    # Reset all servos to neutral
    for channel, servo_type in servo_types.items():
        neutral_angle = 90 if servo_type == "180" else 135
        pwm_value = angle_to_pwm(neutral_angle, servo_type)
        pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
        time.sleep(0.01)
    time.sleep(0.5)
    
    # Disable all PWM outputs
    for i in range(16):
        pwm.channels[i].duty_cycle = 0
    pwm.deinit()
    
    # Cleanup GPIO
    GPIO.cleanup()
    print("Shutdown complete - servos and GPIO cleaned up.")

def get_distance():
    """
    Get distance measurement from HC-SR04 sensor
    Returns distance in centimeters, -1 if timeout
    """
    # Send 10us pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIG, False)
    
    # Wait for echo to start
    pulse_start = time.time()
    timeout_start = pulse_start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        # Timeout protection (max ~0.1 second for faster response)
        if pulse_start - timeout_start > 0.1:
            return -1  # Timeout error
    
    # Wait for echo to end
    pulse_end = time.time()
    timeout_start = pulse_end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        # Timeout protection (max ~0.1 second for faster response)
        if pulse_end - timeout_start > 0.1:
            return -1  # Timeout error
    
    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound calculation
    distance = round(distance, 2)
    
    return distance if 2 <= distance <= 400 else -1  # Valid range for HC-SR04

def is_touch_detected():
    """Check if touch sensor is activated"""
    return GPIO.input(TOUCH_PIN) == 1

# Servo configuration
servo_channels = {
    'front_left_hip': 0,
    'front_left_knee': 1,
    'front_right_hip': 2,
    'front_right_knee': 3,
    'rear_left_hip': 4,
    'rear_left_knee': 5,
    'rear_right_hip': 6,
    'rear_right_knee': 7
}

servo_types = {
    0: "270",   # front_left_hip
    1: "180",   # front_left_knee  
    2: "270",   # front_right_hip
    3: "180",   # front_right_knee
    4: "270",   # rear_left_hip
    5: "180",   # rear_left_knee
    6: "270",   # rear_right_hip
    7: "180"    # rear_right_knee
}

def angle_to_pwm(angle, servo_type):
    """Convert angle to PWM value based on servo type"""
    if servo_type == "180":
        # 180-degree servo: 0° = 1ms, 90° = 1.5ms, 180° = 2ms
        if angle < 0:
            angle = 0
        elif angle > 180:
            angle = 180
        pulse_width = 1.0 + (angle / 180.0) * 1.0  # 1ms to 2ms
    else:  # "270"
        # 270-degree servo: 0° = 0.5ms, 135° = 1.5ms, 270° = 2.5ms
        if angle < 0:
            angle = 0
        elif angle > 270:
            angle = 270
        pulse_width = 0.5 + (angle / 270.0) * 2.0  # 0.5ms to 2.5ms
    
    # Convert to PWM value (0-4096 for PCA9685)
    return int((pulse_width / 20.0) * 4096)

def set_servo_angle(channel, angle):
    """Set servo to specific angle"""
    servo_type = servo_types.get(channel, "180")
    pwm_value = angle_to_pwm(angle, servo_type)
    pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)

def set_pose(angles):
    """Set all servos to specified angles simultaneously"""
    for i, angle in enumerate(angles):
        if i < len(servo_channels):
            set_servo_angle(i, angle)
            time.sleep(0.01)  # Small delay between servo commands
    time.sleep(0.1)  # Allow servos to reach position

# Define poses
standing_angles = [135, 45, 135, 135, 135, 45, 135, 135]  # Standing pose
sitting_angles = [135, 120, 135, 60, 135, 120, 135, 60]   # Sitting pose

# Gait patterns
def walk_trot(steps=10, check_obstacles=True):
    """Improved trot gait with obstacle avoidance"""
    for step in range(steps):
        if check_obstacles:
            distance = get_distance()
            if distance != -1 and distance < 30:  # Obstacle detected
                print(f"Obstacle detected at {distance:.2f}cm - turning right")
                turn_right(8)  # Quick turn
                continue  # Skip this step and check again
        
        # Trot gait: front_left + rear_right together, then front_right + rear_left
        # Phase 1: Lift and move forward front_left and rear_right
        set_pose([120, 30, 135, 135, 135, 45, 150, 120])  # Lift front_left and rear_right
        time.sleep(0.15)
        
        # Phase 2: Put down and shift weight
        set_pose([135, 45, 135, 135, 135, 45, 135, 135])  # Standard standing
        time.sleep(0.1)
        
        # Phase 3: Lift and move forward front_right and rear_left  
        set_pose([135, 45, 120, 120, 150, 30, 135, 135])  # Lift front_right and rear_left
        time.sleep(0.15)
        
        # Phase 4: Put down and prepare for next step
        set_pose([135, 45, 135, 135, 135, 45, 135, 135])  # Back to standing
        time.sleep(0.1)

def backward_trot(steps=10):
    """Trot gait for backward movement"""
    for step in range(steps):
        # Reverse trot: similar to forward but different leg positioning
        # Phase 1: Lift front_left and rear_right, move backward
        set_pose([150, 60, 135, 135, 135, 45, 120, 120])
        time.sleep(0.15)
        
        # Phase 2: Put down and shift
        set_pose([135, 45, 135, 135, 135, 45, 135, 135])
        time.sleep(0.1)
        
        # Phase 3: Lift front_right and rear_left, move backward
        set_pose([135, 45, 150, 120, 120, 60, 135, 135])
        time.sleep(0.15)
        
        # Phase 4: Put down
        set_pose([135, 45, 135, 135, 135, 45, 135, 135])
        time.sleep(0.1)

def turn_right(steps=10):
    """Turn right in place"""
    for step in range(steps):
        # Lift front legs and adjust for right turn
        set_pose([120, 30, 150, 120, 135, 45, 135, 45])
        time.sleep(0.15)
        set_pose([135, 45, 135, 135, 135, 45, 135, 135])
        time.sleep(0.1)
        
        # Lift rear legs and adjust for right turn  
        set_pose([135, 45, 135, 135, 120, 30, 150, 120])
        time.sleep(0.15)
        set_pose([135, 45, 135, 135, 135, 45, 135, 135])
        time.sleep(0.1)

def turn_left(steps=10):
    """Turn left in place"""
    for step in range(steps):
        # Lift front legs and adjust for left turn
        set_pose([150, 120, 120, 30, 135, 45, 135, 45])
        time.sleep(0.15)
        set_pose([135, 45, 135, 135, 135, 45, 135, 135])
        time.sleep(0.1)
        
        # Lift rear legs and adjust for left turn
        set_pose([135, 45, 135, 135, 150, 120, 120, 30])
        time.sleep(0.15)
        set_pose([135, 45, 135, 135, 135, 45, 135, 135])
        time.sleep(0.1)

# --- WebSocket Client for Relay Server ---
class RobotWebSocketClient:
    def __init__(self):
        self.websocket = None
        self.loop = None
        self.lock = threading.Lock()
        self.running = False

    async def connect(self):
        self.running = True
        while self.running:
            try:
                print(f"🔗 Connecting to relay server at {RELAY_URL}...")
                self.websocket = await websockets.connect(RELAY_URL)
                
                # Identify as robot
                await self.websocket.send(json.dumps({
                    "type": "identify", 
                    "client_type": "robot"
                }))
                
                print("✅ Connected to relay server as robot")
                await self.handle_messages()
                
            except Exception as e:
                print(f"❌ Connection error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            finally:
                if self.websocket:
                    await self.websocket.close()

    async def send_to_relay(self, data):
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(data))
            except Exception as e:
                print(f"❌ Failed to send to relay: {e}")

    async def handle_messages(self):
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    command_type = data.get('type')
                    
                    if command_type == 'robot_command':
                        command = data.get('command', '').lower()
                        print(f"📥 Received command: {command}")
                        
                        response = {
                            "type": "response",
                            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S'),
                            "success": True
                        }
                        
                        if command == 'walk' or command == 'forward':
                            threading.Thread(target=self._run_safe, args=(walk_trot, 30, True), daemon=True).start()
                            response["message"] = "🚶 Started walking (trot gait with obstacle avoidance)"
                            
                        elif command == 'backward':
                            threading.Thread(target=self._run_safe, args=(backward_trot, 30), daemon=True).start()
                            response["message"] = "🔙 Started backward walking"
                            
                        elif command == 'right':
                            threading.Thread(target=self._run_safe, args=(turn_right, 20), daemon=True).start()
                            response["message"] = "↪️ Started turning right"
                            
                        elif command == 'left':
                            threading.Thread(target=self._run_safe, args=(turn_left, 20), daemon=True).start()
                            response["message"] = "↩️ Started turning left"
                            
                        elif command == 'stand':
                            threading.Thread(target=self._run_safe, args=(set_pose, standing_angles), daemon=True).start()
                            response["message"] = "🧍 Standing pose set"
                            
                        elif command == 'sit':
                            threading.Thread(target=self._run_safe, args=(set_pose, sitting_angles), daemon=True).start()
                            response["message"] = "🪑 Sitting pose set"
                            
                        elif command == 'distance':
                            dist = get_distance()
                            if dist != -1:
                                response["message"] = f"📏 Distance: {dist:.2f} cm"
                            else:
                                response["message"] = "❌ Sensor timeout"
                                response["success"] = False
                                
                        elif command == 'q' or command == 'stop':
                            cleanup_gpio()
                            response["message"] = "🛑 Robot stopped and cleaned up"
                            self.running = False
                            
                        else:
                            response["message"] = f"❓ Unknown command: {command}"
                            response["success"] = False
                            
                        await self.send_to_relay(response)
                        
                except Exception as e:
                    error_msg = f"Robot error: {str(e)}"
                    print(f"❌ {error_msg}")
                    await self.send_to_relay({
                        "type": "error", 
                        "message": error_msg
                    })
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed. Will reconnect...")
        except Exception as e:
            print(f"❌ Message handling error: {e}")

    def _run_safe(self, func, *args, **kwargs):
        """Safely run robot functions with error handling"""
        with self.lock:
            try:
                func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Robot function error: {str(e)}"
                print(f"❌ {error_msg}")
                # Send error to relay if possible
                if self.loop and not self.loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        self.send_to_relay({
                            "type": "error", 
                            "message": error_msg
                        }), 
                        self.loop
                    )

    def stop(self):
        self.running = False

# Initialize components
setup_sensors()
signal.signal(signal.SIGINT, cleanup_gpio)
signal.signal(signal.SIGTERM, cleanup_gpio)

robot_client = RobotWebSocketClient()

async def main():
    print("🐕 SpotMicro Pet Robot Control System 🐕")
    print("=" * 60)
    print("🚨 Obstacle avoidance enabled - robot will automatically turn right when obstacles detected within 30cm during walking")
    print("🏃 Current speed: normal - Normal walking speed")
    print(f"🔗 Connecting to relay server at {RELAY_URL}")
    print()
    print("Valid commands: walk, backward, right, left, stand, sit, distance, q")
    print("Press Ctrl+C to stop the robot")
    print("=" * 60)
    
    robot_client.loop = asyncio.get_event_loop()
    await robot_client.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down robot client...")
        robot_client.stop()
        cleanup_gpio()
