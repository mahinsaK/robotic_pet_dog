#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685
import time
import numpy as np
import RPi.GPIO as GPIO

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

# Ultrasonic sensor configuration
TRIG = 23  # GPIO23
ECHO = 24  # GPIO24

def setup_ultrasonic():
    """Initialize GPIO pins for ultrasonic sensor"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("Ultrasonic sensor initialized")

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

# Servo types and channels
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "180", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Straight mode angles (previously standing mode)
straight_angles = {
    0: 170, 1: 10, 2: 150,    
    4: 100, 5: 115, 6: 10,    
    8: 143.5, 9: 23, 10: 150,  
    12: 115, 13: 117, 14: 5   
}

# Stand mode angles (previously sitting mode)
stand_angles = {
    0: 170, 1: 70, 2: 50,    
    4: 100, 5: 55, 6: 110,    
    8: 143.5, 9: 83, 10: 50,   
    12: 115, 13: 57, 14: 105  
}

# New sitting mode angles
sit_angles = {
    0: 170, 1: 110, 2: 10,    
    4: 100, 5: 15, 6: 150,    
    8: 143.5, 9: 123, 10: 10,   
    12: 115, 13: 17, 14: 145  
}

# Walking gait angles (using stand_angles as base) -> walk 2
walking_phases = {
    "front_right": [
        {5: 45, 6: 115},  # Phase 1: Lower leg {5: 55, 6: 110}
        {5: 35, 6: 115},  # Phase 2: Push back {5: 35, 6: 110}
        {5: 35, 6: 125},  # Phase 3: Lift leg
        {5: 65, 6: 120}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 80, 2: 45},   # Phase 1: Lower leg {1: 70, 2: 50}
        {1: 90, 2: 45},   # Phase 2: Push back {1: 90, 2: 50}
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 60, 2: 40}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 47, 14: 110},  # Phase 1: Lower leg {13: 57, 14: 105}
        {13: 37, 14: 110},  # Phase 2: Push back {13: 37, 14: 105}
        {13: 37, 14: 120}, # Phase 3: Lift leg
        {13: 67, 14: 115}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 93, 10: 45},  # Phase 1: Lower leg {9: 83, 10: 50}
        {9: 103, 10: 45},  # Phase 2: Push back {9: 103, 10: 50}
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 73, 10: 40}   # Phase 4: Move forward
    ]
}

# Turn right gait angles -> turn right 3
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
        {13: 52, 14: 100},  # Phase 1: Lower leg
        {13: 37, 14: 105},  # Phase 2: Push back
        {13: 37, 14: 120}, # Phase 3: Lift leg
        {13: 62, 14: 110}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 78, 10: 45},  # Phase 1: Lower leg
        {9: 103, 10: 50},  # Phase 2: Push back
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 68, 10: 35}   # Phase 4: Move forward
    ]
}

# Turn left gait angles -> turn left 3
turn_left_phases = {
    "front_right": [
        {5: 60, 6: 115},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 70, 6: 125}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 75, 2: 55},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 65, 2: 45}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 62, 14: 110},  # Phase 1: Lower leg
        {13: 37, 14: 105},  # Phase 2: Push back
        {13: 37, 14: 120}, # Phase 3: Lift leg
        {13: 72, 14: 120}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 88, 10: 55},  # Phase 1: Lower leg
        {9: 103, 10: 50},  # Phase 2: Push back
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 78, 10: 45}   # Phase 4: Move forward
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

def set_pose(target_angles, transition_time=1.0, steps=5, deactivate_after_move=False): #0.3
    global current_angles
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

def walk_trot(cycles=50, enable_obstacle_avoidance=True):
    print("Starting trot walk...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will turn right if obstacle detected within 30cm")
    
    set_pose(stand_angles, transition_time=0.25)

    for cycle in range(cycles):
        # Check for obstacles before each cycle if avoidance is enabled
        if enable_obstacle_avoidance and check_obstacle():
            distance = get_distance()
            print(f"🚨 Obstacle detected at {distance:.1f}cm! Stopping forward walk and turning right...")
            
            # Stop current walk and start turning right until obstacle is cleared
            obstacle_turn_cycles = 0
            max_turn_cycles = 100  # Prevent infinite turning
            
            while check_obstacle() and obstacle_turn_cycles < max_turn_cycles:
                # Execute one turn right cycle
                for phase_idx in range(4):
                    fr_rl = phase_idx
                    fl_rr = (phase_idx + 2) % 4

                    angles = stand_angles.copy()
                    angles.update(turn_right_phases["front_right"][fr_rl])
                    angles.update(turn_right_phases["rear_left"][fr_rl])
                    angles.update(turn_right_phases["front_left"][fl_rr])
                    angles.update(turn_right_phases["rear_right"][fl_rr])

                    set_pose(angles, transition_time=0.25) #0.015
                    #time.sleep(0.0025)
                
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
        
        # Execute normal walk cycle
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4

            angles = stand_angles.copy()
            angles.update(walking_phases["rear_left"][rl_fr])
            angles.update(walking_phases["front_right"][rl_fr])
            angles.update(walking_phases["rear_right"][rr_fl])
            angles.update(walking_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=0.25)
            #time.sleep(0.0025)

    set_pose(stand_angles, transition_time=0.25)
    print("Trot walk complete.")

def turn_right(cycles=30, enable_obstacle_avoidance=False):
    print("Starting right turn...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will stop if obstacle detected within 30cm")
    
    set_pose(stand_angles, transition_time=0.25)

    for cycle in range(cycles):
        # Check for obstacles before each cycle if avoidance is enabled
        if enable_obstacle_avoidance and check_obstacle():
            distance = get_distance()
            print(f"🚨 Obstacle detected at {distance:.1f}cm! Stopping right turn...")
            break
        
        for phase_idx in range(4):
            # Diagonal pairs: FR-RL and FL-RR with 2 phase difference
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4

            angles = stand_angles.copy()
            angles.update(turn_right_phases["front_right"][fr_rl])
            angles.update(turn_right_phases["rear_left"][fr_rl])
            angles.update(turn_right_phases["front_left"][fl_rr])
            angles.update(turn_right_phases["rear_right"][fl_rr])

            set_pose(angles, transition_time=0.25)
            #time.sleep(0.0025)

    set_pose(stand_angles, transition_time=0.25)
    print("Right turn complete.")

def turn_left(cycles=30, enable_obstacle_avoidance=False):
    print("Starting left turn...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will stop if obstacle detected within 30cm")
    
    set_pose(stand_angles, transition_time=0.25)

    for cycle in range(cycles):
        # Check for obstacles before each cycle if avoidance is enabled
        if enable_obstacle_avoidance and check_obstacle():
            distance = get_distance()
            print(f"🚨 Obstacle detected at {distance:.1f}cm! Stopping left turn...")
            break
        
        for phase_idx in range(4):
            # Diagonal pairs: FR-RL and FL-RR with 2 phase difference
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4

            angles = stand_angles.copy()
            angles.update(turn_left_phases["front_right"][fr_rl])
            angles.update(turn_left_phases["rear_left"][fr_rl])
            angles.update(turn_left_phases["front_left"][fl_rr])
            angles.update(turn_left_phases["rear_right"][fl_rr])

            set_pose(angles, transition_time=0.25)
            #time.sleep(0.0025)

    set_pose(stand_angles, transition_time=0.25)
    print("Left turn complete.")

# Initialize current angles
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}

# Initialize ultrasonic sensor
setup_ultrasonic()

# Main program
print("Quadruped Robot: Straight / Stand / Sit / Walk / Turn Right / Turn Left / Test Distance / Quit")
print("� Interactive obstacle avoidance - you can choose to enable/disable for each movement command")
print("🚨 Walk mode: obstacle avoidance enabled by default (robot turns right when obstacle detected)")
print("🔄 Turn modes: obstacle avoidance disabled by default (robot stops when obstacle detected)")

try:
    while True:
        cmd = input("Enter mode (straight/stand/sit/walk/right/left/distance/q): ").strip().lower()
        if cmd == 'q':
            break
        elif cmd == 'straight':
            print("Moving to straight mode...")
            set_pose(straight_angles)
            input("Straight pose set. Press Enter to continue.")
        elif cmd == 'stand':
            print("Moving to stand mode...")
            set_pose(stand_angles)
            input("Stand pose set. Press Enter to continue.")
        elif cmd == 'sit':
            print("Moving to sit mode...")
            set_pose(sit_angles)
            input("Sit pose set. Press Enter to continue.")
        elif cmd == 'walk':
            obstacle_choice = input("Enable obstacle avoidance? (y/n, default=y): ").strip().lower()
            enable_avoidance = obstacle_choice != 'n'
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED - robot will turn right if obstacle detected within 30cm")
            else:
                print("⚠️ Obstacle avoidance DISABLED - robot will walk forward regardless of obstacles")
            walk_trot(cycles=50, enable_obstacle_avoidance=enable_avoidance)
            input("Walk finished. Press Enter to continue.")
        elif cmd == 'right':
            obstacle_choice = input("Enable obstacle avoidance during turn? (y/n, default=n): ").strip().lower()
            enable_avoidance = obstacle_choice == 'y'
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED during right turn")
            else:
                print("⚠️ Obstacle avoidance DISABLED during right turn")
            turn_right(cycles=30, enable_obstacle_avoidance=enable_avoidance)
            input("Right turn finished. Press Enter to continue.")
        elif cmd == 'left':
            obstacle_choice = input("Enable obstacle avoidance during turn? (y/n, default=n): ").strip().lower()
            enable_avoidance = obstacle_choice == 'y'
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED during left turn")
            else:
                print("⚠️ Obstacle avoidance DISABLED during left turn")
            turn_left(cycles=30, enable_obstacle_avoidance=enable_avoidance)
            input("Left turn finished. Press Enter to continue.")
        elif cmd == 'distance':
            distance = get_distance()
            if distance == -1:
                print("Sensor timeout - check ultrasonic sensor connections")
            else:
                status = "🚨 OBSTACLE!" if distance <= 30 else "✅ Clear"
                print(f"Distance: {distance:.2f} cm | {status}")
        else:
            print("Invalid command. Use: straight/stand/sit/walk/right/left/distance/q")
finally:
    print("Resetting all servos to neutral...")
    for channel, servo_type in servo_types.items():
        neutral_angle = 90 if servo_type == "180" else 135
        pwm_value = angle_to_pwm(neutral_angle, servo_type)
        pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
        time.sleep(0.01)
    time.sleep(0.5)
    for i in range(16):
        pwm.channels[i].duty_cycle = 0
    pwm.deinit()
    
    # Cleanup GPIO
    GPIO.cleanup()
    print("Shutdown complete - servos and GPIO cleaned up.")
