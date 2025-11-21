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
    6: "180", 8: "270", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Standing mode angles
standing_angles = {
    0: 200, 1: 10, 2: 145,    # FLS: 200 (unchanged)
    4: 100, 5: 115, 6: 10,    # FRS: 100 (was 90)
    8: 220, 9: 19, 10: 150,   # RLS: 220 (was 230)
    12: 120, 13: 110, 14: 5   # RRS: 120 (was 85)
}

# Sitting mode angles
sitting_angles = {
    0: 207, 1: 70, 2: 50,    # FLS: 200 (unchanged), FL Hip: 70, Knee: 45
    4: 90, 5: 55, 6: 110,    # FRS: 100 (was 90)
    8: 220, 9: 79, 10: 50,   # RLS: 220 (was 230)
    12: 115, 13: 45, 14: 105  # RRS: 120 (was 85)
}

# Walking gait angles
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

def walk_trot(cycles=10):
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

# Initialize current angles
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}

# Main program
print("Quadruped Robot: Stand / Sit / Walk / Quit")

try:
    while True:
        cmd = input("Enter mode (stand/sit/walk/q): ").strip().lower()
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
            walk_trot(cycles=10)
            input("Walk finished. Press Enter to continue.")
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
