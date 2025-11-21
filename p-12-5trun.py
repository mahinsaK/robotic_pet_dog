#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685
import time
import numpy as np

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

# Servo types and channels
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "180", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Standing mode angles
standing_angles = {
    0: 200, 1: 10, 2: 145,    # FLS: 200, FLH: 10, FLK: 145
    4: 100, 5: 115, 6: 10,    # FRS: 100, FRH: 115, FRK: 10
    8: 150, 9: 19, 10: 150,   # RLS: 150, RLH: 19, RLK: 150
    12: 120, 13: 110, 14: 5   # RRS: 120, RRH: 110, RRK: 5
}

# Sitting mode angles
sitting_angles = {
    0: 207, 1: 70, 2: 50,    # FLS: 207, FLH: 70, FLK: 50
    4: 90, 5: 55, 6: 110,    # FRS: 90, FRH: 55, FRK: 110
    8: 150, 9: 79, 10: 50,   # RLS: 150, RLH: 79, RLK: 50
    12: 115, 13: 45, 14: 105  # RRS: 115, RRH: 45, RRK: 105
}

# Walking gait angles
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
        {1: 90, 2: 35},   # Phase 3: Lift leg
        {1: 60, 2: 40}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 45, 14: 105},  # Phase 1: Lower leg
        {13: 25, 14: 105},  # Phase 2: Push back
        {13: 25, 14: 120},  # Phase 3: Lift leg
        {13: 55, 14: 115}   # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 79, 10: 50},  # Phase 1: Lower leg
        {9: 99, 10: 50},  # Phase 2: Push back
        {9: 99, 10: 35},  # Phase 3: Lift leg
        {9: 69, 10: 40}   # Phase 4: Move forward
    ]
}

# Turning right angles
turning_right_phases = {
    "front_right": [
        {5: 45, 6: 100},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 55, 6: 110}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 60, 2: 40},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},   # Phase 3: Lift leg
        {1: 50, 2: 30}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 35, 14: 95},  # Phase 1: Lower leg
        {13: 25, 14: 105},  # Phase 2: Push back
        {13: 25, 14: 120}, # Phase 3: Lift leg
        {13: 45, 14: 105}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 69, 10: 40},  # Phase 1: Lower leg
        {9: 99, 10: 50},  # Phase 2: Push back
        {9: 99, 10: 35},  # Phase 3: Lift leg
        {9: 59, 10: 30}   # Phase 4: Move forward
    ]
}

# Turning left angles
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
        {1: 90, 2: 35},   # Phase 3: Lift leg
        {1: 70, 2: 50}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 55, 14: 115},  # Phase 1: Lower leg
        {13: 25, 14: 105},  # Phase 2: Push back
        {13: 25, 14: 120},  # Phase 3: Lift leg
        {13: 65, 14: 125}   # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 89, 10: 60},  # Phase 1: Lower leg
        {9: 99, 10: 50},  # Phase 2: Push back
        {9: 99, 10: 35},  # Phase 3: Lift leg
        {9: 79, 10: 50}   # Phase 4: Move forward
    ]
}

# Backward walking gait angles
walking_backward_phases = {
    "front_right": [
        {5: 65, 6: 120},   # Phase 1: Move backward
        {5: 35, 6: 125},   # Phase 2: Lift leg
        {5: 35, 6: 110},   # Phase 3: Push back
        {5: 55, 6: 110}    # Phase 4: Lower leg
    ],
    "front_left": [
        {1: 60, 2: 40},    # Phase 1: Move backward
        {1: 90, 2: 35},    # Phase 2: Lift leg
        {1: 90, 2: 50},    # Phase 3: Push back
        {1: 70, 2: 50}     # Phase 4: Lower leg
    ],
    "rear_right": [
        {13: 55, 14: 115}, # Phase 1: Move backward
        {13: 25, 14: 120}, # Phase 2: Lift leg
        {13: 25, 14: 105}, # Phase 3: Push back
        {13: 45, 14: 105}  # Phase 4: Lower leg
    ],
    "rear_left": [
        {9: 69, 10: 40},   # Phase 1: Move backward
        {9: 99, 10: 35},   # Phase 2: Lift leg
        {9: 99, 10: 50},   # Phase 3: Push back
        {9: 79, 10: 50}    # Phase 4: Lower leg
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

def set_pose(target_angles, transition_time=0.3, steps=50, deactivate_after_move=False):
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

def walk_trot(cycles=50):
    print("Starting trot walk...")
    set_pose(sitting_angles, transition_time=0.015)

    for _ in range(cycles):
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4
            
            angles = sitting_angles.copy()
            angles.update(walking_phases["rear_left"][rl_fr])
            angles.update(walking_phases["front_right"][rl_fr])
            angles.update(walking_phases["rear_right"][rr_fl])
            angles.update(walking_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=0.015)
            time.sleep(0.0025)

    set_pose(sitting_angles, transition_time=0.015)
    print("Trot walk complete.")

def turn_right(cycles=50):
    print("Starting right turn...")
    set_pose(sitting_angles, transition_time=0.015)

    for _ in range(cycles):
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4
            
            angles = sitting_angles.copy()
            angles.update(turning_right_phases["rear_left"][rl_fr])
            angles.update(turning_right_phases["front_right"][rl_fr])
            angles.update(turning_right_phases["rear_right"][rr_fl])
            angles.update(turning_right_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=0.015)
            time.sleep(0.0025)

    set_pose(sitting_angles, transition_time=0.015)
    print("Right turn complete.")

def turn_left(cycles=50):
    print("Starting left turn...")
    set_pose(sitting_angles, transition_time=0.015)

    for _ in range(cycles):
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4
            
            angles = sitting_angles.copy()
            angles.update(turn_left_phases["rear_left"][rl_fr])
            angles.update(turn_left_phases["front_right"][rl_fr])
            angles.update(turn_left_phases["rear_right"][rr_fl])
            angles.update(turn_left_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=0.015)
            time.sleep(0.0025)

    set_pose(sitting_angles, transition_time=0.015)
    print("Left turn complete.")

def walk_backward(cycles=50):
    print("Starting backward walk...")
    set_pose(sitting_angles, transition_time=0.015)

    for _ in range(cycles):
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4
            
            angles = sitting_angles.copy()
            angles.update(walking_backward_phases["rear_left"][rl_fr])
            angles.update(walking_backward_phases["front_right"][rl_fr])
            angles.update(walking_backward_phases["rear_right"][rr_fl])
            angles.update(walking_backward_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=0.015)
            time.sleep(0.0025)

    set_pose(sitting_angles, transition_time=0.015)
    print("Backward walk complete.")

# Initialize current angles
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}

# Main program
print("Quadruped Robot: Stand / Sit / Walk / TurnRight / TurnLeft / Backward / Quit")

try:
    while True:
        cmd = input("Enter mode (stand/sit/walk/turnright/turnleft/backward/q): ").strip().lower()
        if cmd == 'q':
            break
        elif cmd == 'stand':
            print("Moving to standing mode...")
            set_pose(standing_angles)
            input("Standing pose set. Press Enter to continue.")
        elif cmd == 'sit':
            print("Moving to sitting mode...")
            set_pose(sitting_angles)
            input("Sitting pose set. Press Enter to continue.")
        elif cmd == 'walk':
            walk_trot(cycles=50)
            input("Walk finished. Press Enter to continue.")
        elif cmd == 'turnright':
            turn_right(cycles=50)
            input("Right turn finished. Press Enter to continue.")
        elif cmd == 'turnleft':
            turn_left(cycles=50)
            input("Left turn finished. Press Enter to continue.")
        elif cmd == 'backward':
            walk_backward(cycles=50)
            input("Backward walk finished. Press Enter to continue.")
        else:
            print("Invalid command.")
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
    print("Shutdown complete.")