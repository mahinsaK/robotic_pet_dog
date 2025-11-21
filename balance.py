#!/usr/bin/env python3
import board
import busio
import adafruit_mpu6050
import adafruit_pca9685
import math
import time

# Initialize I2C bus
try:
    i2c = busio.I2C(board.SCL, board.SDA)
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit(1)

# Initialize PCA9685
try:
    pwm = adafruit_pca9685.PCA9685(i2c)
    pwm.frequency = 50  # 50 Hz for DS3240 servos
except Exception as e:
    print(f"Error initializing PCA9685: {e}")
    exit(1)

# Initialize MPU-6050
try:
    mpu = adafruit_mpu6050.MPU6050(i2c)
except Exception as e:
    print(f"Error initializing MPU-6050: {e}")
    exit(1)

# Clear all PWM signals at start
for i in range(16):
    pwm.channels[i].duty_cycle = 0

# Servo configuration: channel -> (servo_type, sitting_angle)
servo_config = {
    0: ("270", 207),  # FL shoulder
    1: ("270", 70),   # FL thigh
    2: ("270", 50),   # FL knee
    4: ("270", 90),   # FR shoulder
    5: ("270", 55),   # FR thigh
    6: ("180", 110),  # FR knee
    8: ("270", 220),  # RL shoulder
    9: ("270", 79),   # RL thigh
    10: ("180", 50),  # RL knee
    12: ("180", 115), # RR shoulder
    13: ("270", 45),  # RR thigh
    14: ("180", 105)  # RR knee
}

# Angle to PWM conversion
def angle_to_pwm(angle, servo_type):
    if servo_type == "180":
        min_angle, max_angle = 0, 180
        min_pwm, max_pwm = 100, 500
    else:  # 270° servo
        min_angle, max_angle = 0, 270
        min_pwm, max_pwm = 100, 500
    angle = max(min(angle, max_angle), min_angle)
    pwm_value = int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))
    return int(pwm_value * 65535 / 4096)

# Set all servos to sitting position
def set_sitting_position():
    for channel, (servo_type, angle) in servo_config.items():
        pwm.channels[channel].duty_cycle = angle_to_pwm(angle, servo_type)

# Adjustment rules based on tilt direction
adjustments = {
    "forward": {
        1: -1,  # FL thigh decrease
        2: 1,   # FL knee increase
        5: 1,   # FR thigh increase
        6: -1,  # FR knee decrease
        9: 1,   # RL thigh increase
        10: -1, # RL knee decrease
        13: -1, # RR thigh decrease
        14: 1   # RR knee increase
    },
    "backward": {
        1: 1,   # FL thigh increase
        2: -1,  # FL knee decrease
        5: -1,  # FR thigh decrease
        6: 1,   # FR knee increase
        9: -1,  # RL thigh decrease
        10: 1,  # RL knee increase
        13: 1,  # RR thigh increase
        14: -1  # RR knee decrease
    },
    "right": {
        0: -1,  # FL shoulder decrease
        1: 1,   # FL thigh increase
        2: -1,  # FL knee decrease
        4: -1,  # FR shoulder decrease
        5: 1,   # FR thigh increase
        6: -1,  # FR knee decrease
        8: -1,  # RL shoulder decrease
        9: 1,   # RL thigh increase
        10: -1, # RL knee decrease
        12: -1, # RR shoulder decrease
        13: 1,  # RR thigh increase
        14: -1  # RR knee decrease
    },
    "left": {
        0: 1,   # FL shoulder increase
        1: -1,  # FL thigh decrease
        2: 1,   # FL knee increase
        4: 1,   # FR shoulder increase
        5: -1,  # FR thigh decrease
        6: 1,   # FR knee increase
        8: 1,   # RL shoulder increase
        9: -1,  # RL thigh decrease
        10: 1,  # RL knee increase
        12: 1,  # RR shoulder increase
        13: -1, # RR thigh decrease
        14: 1   # RR knee increase
    }
}

# Maximum adjustment angle (degrees) to prevent overextension
MAX_ADJUSTMENT = 20
# Proportional gain for tilt correction
GAIN = 1.0

# Set initial sitting position
set_sitting_position()
print("Robot set to sitting position. Starting balance control...")
print("Press Ctrl+C to exit.")

try:
    while True:
        # Read accelerometer data
        accel = mpu.acceleration
        ax, ay, az = accel

        # Calculate pitch (y-axis, forward/backward) and roll (x-axis, left/right)
        # Pitch: positive = forward tilt, negative = backward tilt
        # Roll: positive = left tilt, negative = right tilt
        pitch = math.degrees(math.atan2(-ay, math.sqrt(ax*2 + az*2)))
        roll = math.degrees(math.atan2(ax, math.sqrt(ay*2 + az*2)))

        # Initialize current angles from sitting position
        current_angles = {ch: config[1] for ch, config in servo_config.items()}

        # Apply adjustments based on tilt
        if pitch > 2:  # Forward tilt
            for channel, direction in adjustments["forward"].items():
                adjustment = direction * min(pitch * GAIN, MAX_ADJUSTMENT)
                servo_type = servo_config[channel][0]
                max_angle = 180 if servo_type == "180" else 270
                new_angle = max(min(current_angles[channel] + adjustment, max_angle), 0)
                pwm.channels[channel].duty_cycle = angle_to_pwm(new_angle, servo_type)
        elif pitch < -2:  # Backward tilt
            for channel, direction in adjustments["backward"].items():
                adjustment = direction * min(abs(pitch) * GAIN, MAX_ADJUSTMENT)
                servo_type = servo_config[channel][0]
                max_angle = 180 if servo_type == "180" else 270
                new_angle = max(min(current_angles[channel] + adjustment, max_angle), 0)
                pwm.channels[channel].duty_cycle = angle_to_pwm(new_angle, servo_type)

        if roll > 2:  # Left tilt
            for channel, direction in adjustments["left"].items():
                adjustment = direction * min(roll * GAIN, MAX_ADJUSTMENT)
                servo_type = servo_config[channel][0]
                max_angle = 180 if servo_type == "180" else 270
                new_angle = max(min(current_angles[channel] + adjustment, max_angle), 0)
                pwm.channels[channel].duty_cycle = angle_to_pwm(new_angle, servo_type)
        elif roll < -2:  # Right tilt
            for channel, direction in adjustments["right"].items():
                adjustment = direction * min(abs(roll) * GAIN, MAX_ADJUSTMENT)
                servo_type = servo_config[channel][0]
                max_angle = 180 if servo_type == "180" else 270
                new_angle = max(min(current_angles[channel] + adjustment, max_angle), 0)
                pwm.channels[channel].duty_cycle = angle_to_pwm(new_angle, servo_type)

        # Small delay to prevent excessive updates
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nExiting and resetting servos to sitting position...")
    set_sitting_position()
    time.sleep(1)
    for channel in servo_config:
        pwm.channels[channel].duty_cycle = 0
    print("Servos reset. Program terminated.")