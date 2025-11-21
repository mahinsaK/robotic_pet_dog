#!/usr/bin/env python3
"""
Enhanced Robot Dog Control Script with Stop and Backward Functions
Based on p12-6.py with additional stop and backward capabilities
"""
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
    """Get distance measurement from HC-SR04 sensor"""
    try:
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        
        start_time = time.time()
        timeout = start_time + 0.1
        
        while GPIO.input(ECHO) == 0:
            start_time = time.time()
            if time.time() > timeout:
                return -1
                
        while GPIO.input(ECHO) == 1:
            stop_time = time.time()
            if time.time() > timeout:
                return -1
                
        time_elapsed = stop_time - start_time
        distance = (time_elapsed * 34300) / 2
        return distance
    except:
        return -1

# Servo types and channels
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "270", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Standing mode angles
standing_angles = {
    0: 200, 1: 10, 2: 145,
    4: 100, 5: 115, 6: 10,
    8: 220, 9: 19, 10: 150,
    12: 120, 13: 110, 14: 5
}

# Sitting mode angles
sitting_angles = {
    0: 207, 1: 70, 2: 50,
    4: 90, 5: 55, 6: 110,
    8: 220, 9: 79, 10: 50,
    12: 115, 13: 45, 14: 105
}

# Forward walking gait angles
walking_phases = {
    "front_right": [
        {5: 115, 6: 10},
        {5: 85, 6: 5},
        {5: 85, 6: 20},
        {5: 105, 6: 20}
    ],
    "front_left": [
        {1: 10, 2: 145},
        {1: 40, 2: 150},
        {1: 40, 2: 135},
        {1: 20, 2: 135}
    ],
    "rear_right": [
        {13: 110, 14: 5},
        {13: 80, 14: 0},
        {13: 80, 14: 15},
        {13: 100, 14: 15}
    ],
    "rear_left": [
        {9: 19, 10: 150},
        {9: 49, 10: 155},
        {9: 49, 10: 140},
        {9: 29, 10: 140}
    ]
}

# Backward walking gait angles (from backward.py)
backward_phases = {
    "front_right": [
        {5: 65, 6: 120},
        {5: 35, 6: 125},
        {5: 35, 6: 110},
        {5: 55, 6: 110}
    ],
    "front_left": [
        {1: 60, 2: 40},
        {1: 90, 2: 35},
        {1: 90, 2: 50},
        {1: 70, 2: 50}
    ],
    "rear_right": [
        {13: 55, 14: 115},
        {13: 25, 14: 120},
        {13: 25, 14: 105},
        {13: 45, 14: 105}
    ],
    "rear_left": [
        {9: 69, 10: 40},
        {9: 99, 10: 35},
        {9: 99, 10: 50},
        {9: 79, 10: 50}
    ]
}

# Right turn gait
right_turn_phases = {
    "front_right": [
        {5: 115, 6: 10}, {5: 85, 6: 5}, {5: 85, 6: 25}, {5: 105, 6: 25}
    ],
    "front_left": [
        {1: 10, 2: 145}, {1: 10, 2: 160}, {1: 10, 2: 120}, {1: 10, 2: 135}
    ],
    "rear_right": [
        {13: 110, 14: 5}, {13: 80, 14: 0}, {13: 80, 14: 20}, {13: 100, 14: 20}
    ],
    "rear_left": [
        {9: 19, 10: 150}, {9: 19, 10: 165}, {9: 19, 10: 125}, {9: 19, 10: 140}
    ]
}

# Left turn gait
left_turn_phases = {
    "front_right": [
        {5: 115, 6: 10}, {5: 115, 6: 25}, {5: 115, 6: -5}, {5: 115, 6: 10}
    ],
    "front_left": [
        {1: 10, 2: 145}, {1: 40, 2: 150}, {1: 40, 2: 130}, {1: 20, 2: 135}
    ],
    "rear_right": [
        {13: 110, 14: 5}, {13: 110, 14: 20}, {13: 110, 14: -10}, {13: 110, 14: 5}
    ],
    "rear_left": [
        {9: 19, 10: 150}, {9: 49, 10: 155}, {9: 49, 10: 135}, {9: 29, 10: 140}
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

def set_pose(target_angles, transition_time=0.3, steps=50):
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

def emergency_stop():
    """Emergency stop - immediately go to sitting position"""
    print("🛑 EMERGENCY STOP - Moving to safe sitting position")
    set_pose(sitting_angles, transition_time=0.1)
    print("✅ Emergency stop complete - robot in safe position")

def walk_trot(cycles=10, gait_phases=None, enable_obstacle_avoidance=False):
    """Generic trot walk function"""
    if gait_phases is None:
        gait_phases = walking_phases
        
    print("Starting trot movement...")
    set_pose(standing_angles, transition_time=0.5)

    for cycle in range(cycles):
        if enable_obstacle_avoidance:
            distance = get_distance()
            if distance != -1 and distance <= 30:
                print(f"🚨 Obstacle detected at {distance:.1f}cm - turning right")
                turn_right(cycles=15)
                set_pose(standing_angles, transition_time=0.3)
                continue

        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4

            angles = standing_angles.copy()
            angles.update(gait_phases["rear_left"][rl_fr])
            angles.update(gait_phases["front_right"][rl_fr])
            angles.update(gait_phases["rear_right"][rr_fl])
            angles.update(gait_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=0.15)
            time.sleep(0.005)

    set_pose(standing_angles, transition_time=0.5)
    print("Movement complete.")

def walk_forward(cycles=10):
    """Walk forward using forward gait"""
    walk_trot(cycles, walking_phases, enable_obstacle_avoidance=True)

def walk_backward(cycles=10):
    """Walk backward using backward gait"""
    print("Walking backward...")
    walk_trot(cycles, backward_phases, enable_obstacle_avoidance=False)

def turn_right(cycles=15):
    """Turn right"""
    print("Turning right...")
    walk_trot(cycles, right_turn_phases, enable_obstacle_avoidance=False)

def turn_left(cycles=15):
    """Turn left"""
    print("Turning left...")
    walk_trot(cycles, left_turn_phases, enable_obstacle_avoidance=False)

# Initialize current angles and ultrasonic sensor
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}
setup_ultrasonic()

# Main program
print("🐕 Enhanced Robot Dog Control")
print("Available commands: stand, sit, walk, backward, right, left, distance, stop, q")
print("🛑 Use 'stop' for emergency stop, 'q' to quit")

try:
    while True:
        cmd = input("Enter command: ").strip().lower()
        if cmd == 'q':
            break
        elif cmd == 'stand':
            print("Moving to standing mode...")
            set_pose(standing_angles)
            print("✅ Standing pose set.")
        elif cmd == 'sit':
            print("Moving to sitting mode...")
            set_pose(sitting_angles)
            print("✅ Sitting pose set.")
        elif cmd == 'walk':
            walk_forward(cycles=10)
        elif cmd == 'backward':
            walk_backward(cycles=10)
        elif cmd == 'right':
            turn_right(cycles=15)
        elif cmd == 'left':
            turn_left(cycles=15)
        elif cmd == 'stop':
            emergency_stop()
        elif cmd == 'distance':
            distance = get_distance()
            if distance == -1:
                print("Sensor timeout - check ultrasonic sensor connections")
            else:
                status = "🚨 OBSTACLE!" if distance <= 30 else "✅ Clear"
                print(f"Distance: {distance:.2f} cm | {status}")
        else:
            print("Invalid command. Use: stand/sit/walk/backward/right/left/distance/stop/q")
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
