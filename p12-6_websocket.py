
# --- BEGIN NEW ROBOT WEBSOCKET SERVER (from p12-7.py + backward.py) ---
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

# --- Robot logic and movement functions (from p12-7.py and backward.py) ---

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
    distance = pulse_duration * 17150  # Speed of sound = 343m/s, divide by 2 for round trip
    distance = round(distance, 2)
    
    return distance

def check_obstacle():
    """
    Check if there's an obstacle within 30cm
    Returns True if obstacle detected, False otherwise
    """
    distance = get_distance()
    if distance == -1:  # Sensor timeout
        return False  # Assume no obstacle if sensor fails
    return distance <= 30  # Return True if obstacle within 30cm

# Speed control configuration
SPEED_SETTINGS = {
    "slow": {
        "transition_time": 0.025,
        "phase_delay": 0.010,
        "description": "Slow and steady"
    },
    "normal": {
        "transition_time": 0.015,
        "phase_delay": 0.0025,
        "description": "Normal walking speed"
    },
    "fast": {
        "transition_time": 0.010,
        "phase_delay": 0.001,
        "description": "Fast walking"
    }
}

# Current speed setting
current_speed = "normal"

def get_speed_params():
    """Get current speed parameters"""
    return SPEED_SETTINGS[current_speed]

# Servo types and channels
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "180", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Standing mode angles (formerly sitting mode)
standing_angles = {
    0: 207, 1: 70, 2: 50,    
    4: 90, 5: 55, 6: 110,    
    8: 150, 9: 79, 10: 50,   
    12: 115, 13: 45, 14: 105  
}

# Sitting mode angles
sitting_angles = {
    0: 207, 1: 110, 2: 10,    
    4: 90, 5: 15, 6: 150,    
    8: 150, 9: 119, 10: 10,   
    12: 115, 13: 5, 14: 145  
}

# Walking gait angles (forward)
walking_phases = {
    "front_right": [
        {5: 55, 6: 110},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 65, 6: 120}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 70, 2: 50},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 60, 2: 40}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 45, 14: 105},  # Phase 1: Lower leg
        {13: 25, 14: 105},  # Phase 2: Push back
        {13: 25, 14: 120}, # Phase 3: Lift leg
        {13: 55, 14: 115}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 79, 10: 50},  # Phase 1: Lower leg
        {9: 99, 10: 50},  # Phase 2: Push back
        {9: 99, 10: 35},  # Phase 3: Lift leg
        {9: 69, 10: 40}   # Phase 4: Move forward
    ]
}

# Backward walking gait angles (from backward.py)
backward_phases = {
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

# Turn right gait angles
turn_right_phases = {
    "front_right": [
        {5: 50, 6: 105},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 60, 6: 115}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 65, 2: 45},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 55, 2: 35}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 40, 14: 100},  # Phase 1: Lower leg
        {13: 25, 14: 105},  # Phase 2: Push back
        {13: 25, 14: 120}, # Phase 3: Lift leg
        {13: 50, 14: 110}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 74, 10: 45},  # Phase 1: Lower leg
        {9: 99, 10: 50},  # Phase 2: Push back
        {9: 99, 10: 35},  # Phase 3: Lift leg
        {9: 64, 10: 35}   # Phase 4: Move forward
    ]
}

# Turn left gait angles
turn_left_phases = {
    "front_right": [
        {5: 65, 6: 120},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 75, 6: 130}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 80, 2: 60},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 70, 2: 50}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 55, 14: 115},  # Phase 1: Lower leg
        {13: 25, 14: 105},  # Phase 2: Push back
        {13: 25, 14: 120}, # Phase 3: Lift leg
        {13: 65, 14: 125}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 89, 10: 60},  # Phase 1: Lower leg
        {9: 99, 10: 50},  # Phase 2: Push back
        {9: 99, 10: 35},  # Phase 3: Lift leg
        {9: 79, 10: 50}   # Phase 4: Move forward
    ]
}

def angle_to_pwm(angle, servo_type):
    if servo_type == "180":
        min_angle, max_angle = 0, 180
    else:
        min_angle, max_angle = 0, 270
    min_pwm, max_pwm = 100, 500
    angle = max(min(angle, max_angle), min_angle)
    return int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))

def set_pose(target_angles, transition_time=None, steps=50, deactivate_after_move=False):
    global current_angles
    
    # Use current speed setting if no transition_time specified
    if transition_time is None:
        transition_time = get_speed_params()["transition_time"]
    
    step_angles = {}
    for ch in target_angles:
        start = current_angles.get(ch, 90 if servo_types[ch] == "180" else 135)
        end = target_angles[ch]
        step_angles[ch] = np.linspace(start, end, steps)

    for i in range(steps):
        for ch in target_angles:
            angle = step_angles[ch][i]
            pwm_value = angle_to_pwm(angle, servo_types[ch])
            try:
                pwm.channels[ch].duty_cycle = int(pwm_value * 65535 / 4096)
            except Exception as e:
                print(f"Error setting PWM on channel {ch}: {e}")
        time.sleep(transition_time / steps)

    current_angles.update(target_angles)

    if deactivate_after_move:
        time.sleep(0.1)
        for ch in target_angles:
            pwm.channels[ch].duty_cycle = 0

def walk_trot(cycles=30, enable_obstacle_avoidance=True, speed=None):
    """
    Walk with trot gait and optional obstacle avoidance
    """
    # Use specified speed or current global speed
    if speed and speed in SPEED_SETTINGS:
        speed_params = SPEED_SETTINGS[speed]
        print(f"Starting trot walk at {speed} speed...")
    else:
        speed_params = get_speed_params()
        print(f"Starting trot walk at {current_speed} speed...")
    
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will turn right if obstacle detected within 30cm")
    
    set_pose(standing_angles, transition_time=speed_params["transition_time"])

    for cycle in range(cycles):
        # Check for obstacles before each cycle if avoidance is enabled
        if enable_obstacle_avoidance and check_obstacle():
            distance = get_distance()
            print(f"🚨 Obstacle detected at {distance:.1f}cm! Stopping forward walk and turning right...")
            
            # Stop current walk and start turning right until obstacle is cleared
            obstacle_turn_cycles = 0
            max_turn_cycles = 20  # Prevent infinite turning
            
            while check_obstacle() and obstacle_turn_cycles < max_turn_cycles:
                # Execute one turn right cycle with current speed
                for phase_idx in range(4):
                    fr_rl = phase_idx
                    fl_rr = (phase_idx + 2) % 4

                    angles = standing_angles.copy()
                    angles.update(turn_right_phases["front_right"][fr_rl])
                    angles.update(turn_right_phases["rear_left"][fr_rl])
                    angles.update(turn_right_phases["front_left"][fl_rr])
                    angles.update(turn_right_phases["rear_right"][fl_rr])

                    set_pose(angles, transition_time=speed_params["transition_time"])
                    time.sleep(speed_params["phase_delay"])
                
                obstacle_turn_cycles += 1
                
                # Brief pause to check obstacle status
                time.sleep(0.1)
            
            if obstacle_turn_cycles >= max_turn_cycles:
                print("⚠️ Maximum turn cycles reached. Stopping for safety.")
                break
            else:
                distance = get_distance()
                print(f"✅ Obstacle cleared! Distance now: {distance:.1f}cm. Resuming forward walk...")
                continue  # Continue with remaining walk cycles
        
        # Execute normal walk cycle with speed control
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4

            angles = standing_angles.copy()
            angles.update(walking_phases["rear_left"][rl_fr])
            angles.update(walking_phases["front_right"][rl_fr])
            angles.update(walking_phases["rear_right"][rr_fl])
            angles.update(walking_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=speed_params["transition_time"])
            time.sleep(speed_params["phase_delay"])

    set_pose(standing_angles, transition_time=speed_params["transition_time"])
    print("Trot walk complete.")

def backward_trot(cycles=20):
    """Backward trot walking"""
    print("Starting backward trot walk...")
    speed_params = get_speed_params()
    set_pose(standing_angles, transition_time=speed_params["transition_time"])

    for _ in range(cycles):
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4

            angles = standing_angles.copy()
            angles.update(backward_phases["rear_left"][rl_fr])
            angles.update(backward_phases["front_right"][rl_fr])
            angles.update(backward_phases["rear_right"][rr_fl])
            angles.update(backward_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=speed_params["transition_time"])
            time.sleep(speed_params["phase_delay"])

    set_pose(standing_angles, transition_time=speed_params["transition_time"])
    print("Backward trot walk complete.")

def turn_right(cycles=20, speed=None):
    """Turn right with speed control"""
    # Use specified speed or current global speed
    if speed and speed in SPEED_SETTINGS:
        speed_params = SPEED_SETTINGS[speed]
        print(f"Starting right turn at {speed} speed...")
    else:
        speed_params = get_speed_params()
        print(f"Starting right turn at {current_speed} speed...")
    
    set_pose(standing_angles, transition_time=speed_params["transition_time"])

    for _ in range(cycles):
        for phase_idx in range(4):
            # Diagonal pairs: FR-RL and FL-RR with 2 phase difference
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4

            angles = standing_angles.copy()
            angles.update(turn_right_phases["front_right"][fr_rl])
            angles.update(turn_right_phases["rear_left"][fr_rl])
            angles.update(turn_right_phases["front_left"][fl_rr])
            angles.update(turn_right_phases["rear_right"][fl_rr])

            set_pose(angles, transition_time=speed_params["transition_time"])
            time.sleep(speed_params["phase_delay"])

    set_pose(standing_angles, transition_time=speed_params["transition_time"])
    print("Right turn complete.")

def turn_left(cycles=20, speed=None):
    """Turn left with speed control"""
    # Use specified speed or current global speed
    if speed and speed in SPEED_SETTINGS:
        speed_params = SPEED_SETTINGS[speed]
        print(f"Starting left turn at {speed} speed...")
    else:
        speed_params = get_speed_params()
        print(f"Starting left turn at {current_speed} speed...")
    
    set_pose(standing_angles, transition_time=speed_params["transition_time"])

    for _ in range(cycles):
        for phase_idx in range(4):
            # Diagonal pairs: FR-RL and FL-RR with 2 phase difference
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4

            angles = standing_angles.copy()
            angles.update(turn_left_phases["front_right"][fr_rl])
            angles.update(turn_left_phases["rear_left"][fr_rl])
            angles.update(turn_left_phases["front_left"][fl_rr])
            angles.update(turn_left_phases["rear_right"][fl_rr])

            set_pose(angles, transition_time=speed_params["transition_time"])
            time.sleep(speed_params["phase_delay"])

    set_pose(standing_angles, transition_time=speed_params["transition_time"])
    print("Left turn complete.")

# Initialize current angles
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}

# Set up signal handlers for clean exit
signal.signal(signal.SIGINT, cleanup_gpio)
signal.signal(signal.SIGTERM, cleanup_gpio)

# Initialize sensors
setup_sensors()

print("🐕 SpotMicro Pet Robot Control System 🐕")
print("=" * 60)
print("🚨 Obstacle avoidance enabled - robot will automatically turn right when obstacles detected within 30cm during walking")
print(f"🏃 Current speed: {current_speed} - {SPEED_SETTINGS[current_speed]['description']}")

# --- WebSocket Server ---
class RobotWebSocketServer:
    def __init__(self):
        self.clients = set()
        self.loop = None
        self.robot_status = "ready"
        self.lock = threading.Lock()

    async def register_client(self, websocket):
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        await self.send_to_client(websocket, {
            "type": "status",
            "message": "Connected to Robot WebSocket Server",
            "robot_status": self.robot_status,
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')
        })

    async def unregister_client(self, websocket):
        self.clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")

    async def send_to_client(self, websocket, data):
        try:
            await websocket.send(json.dumps(data))
        except Exception:
            pass

    async def broadcast_to_all(self, data):
        if self.clients:
            await asyncio.gather(*[self.send_to_client(client, data) for client in self.clients], return_exceptions=True)

    async def handle_client_message(self, websocket, message):
        try:
            data = json.loads(message)
            command_type = data.get('type')
            command = data.get('command', '').lower()
            response = {
                "type": "response",
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')
            }
            if command_type == 'robot_command':
                # Map commands to robot functions
                if command == 'walk' or command == 'forward':
                    threading.Thread(target=self._run_safe, args=(walk_trot, 30, True), daemon=True).start()
                    response["message"] = "Started walking (trot gait with obstacle avoidance)"
                elif command == 'backward':
                    threading.Thread(target=self._run_safe, args=(backward_trot, 30), daemon=True).start()
                    response["message"] = "Started backward walking"
                elif command == 'right':
                    threading.Thread(target=self._run_safe, args=(turn_right, 20), daemon=True).start()
                    response["message"] = "Started turning right"
                elif command == 'left':
                    threading.Thread(target=self._run_safe, args=(turn_left, 20), daemon=True).start()
                    response["message"] = "Started turning left"
                elif command == 'stand':
                    threading.Thread(target=self._run_safe, args=(set_pose, standing_angles), daemon=True).start()
                    response["message"] = "Standing pose set"
                elif command == 'sit':
                    threading.Thread(target=self._run_safe, args=(set_pose, sitting_angles), daemon=True).start()
                    response["message"] = "Sitting pose set"
                elif command == 'distance':
                    dist = get_distance()
                    response["message"] = f"Distance: {dist:.2f} cm" if dist != -1 else "Sensor timeout"
                elif command == 'q':
                    cleanup_gpio()
                    response["message"] = "Robot stopped and cleaned up"
                else:
                    response["message"] = f"Unknown command: {command}"
                    response["success"] = False
            else:
                response["message"] = "Unknown command type"
                response["success"] = False
            await self.send_to_client(websocket, response)
        except Exception as e:
            await self.send_to_client(websocket, {
                "type": "error",
                "message": f"Server error: {str(e)}"
            })

    def _run_safe(self, func, *args, **kwargs):
        with self.lock:
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Robot function error: {e}")

    async def websocket_handler(self, websocket):
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

robot_server = RobotWebSocketServer()

async def main():
    print("Starting Robot WebSocket Server...")
    print("Server will be available at:")
    print("  ws://localhost:8765")
    print("  ws://YOUR_PI_IP:8765")
    print("\nValid commands: walk, backward, right, left, stand, sit, distance, q")
    print("Press Ctrl+C to stop the server")
    robot_server.loop = asyncio.get_running_loop()
    server = await websockets.serve(
        robot_server.websocket_handler,
        "0.0.0.0",
        8765
    )
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        cleanup_gpio()
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
