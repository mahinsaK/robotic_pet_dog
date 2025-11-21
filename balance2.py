#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685
import time
import math
import adafruit_mpu6050

# Initialize I2C bus
try:
    i2c = busio.I2C(board.SCL, board.SDA)
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit(1)

# Initialize PCA9685
try:
    pwm = PCA9685(i2c)
    pwm.frequency = 50  # 50 Hz for DS3240 servos
except Exception as e:
    print(f"Error initializing PCA9685: {e}")
    exit(1)

# Initialize MPU6050
try:
    mpu = adafruit_mpu6050.MPU6050(i2c)
except Exception as e:
    print(f"Error initializing MPU6050: {e}")
    exit(1)

# Clear all PWM signals at start
for i in range(16):
    pwm.channels[i].duty_cycle = 0

# Servo configuration
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "270", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Sitting position angles
sitting_angles = {
    0: 207, 1: 70, 2: 50, 4: 90, 5: 55, 6: 110,
    8: 220, 9: 79, 10: 50, 12: 115, 13: 45, 14: 105
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
    return pwm_value

# Set initial sitting position
def set_sitting_position():
    for channel, angle in sitting_angles.items():
        servo_type = servo_types[channel]
        pwm_value = angle_to_pwm(angle, servo_type)
        pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)

# Get pitch and roll from MPU6050
def get_orientation():
    accel_x, accel_y, accel_z = mpu.acceleration
    pitch = math.atan2(accel_y, math.sqrt(accel_x*2 + accel_z*2)) * 180 / math.pi
    roll = math.atan2(-accel_x, accel_z) * 180 / math.pi
    return pitch, roll

# Apply angle adjustments
def adjust_servos(pitch, roll):
    adjustments = {ch: 0 for ch in sitting_angles}
    
    # Handle pitch
    if abs(pitch) > 10:
        pitch_adjust = pitch - (10 if pitch > 0 else -10)
        adjustments[1] += -2 * pitch_adjust if pitch > 0 else 2 * abs(pitch_adjust)  # FL thigh
        adjustments[2] += 2 * pitch_adjust if pitch > 0 else -2 * abs(pitch_adjust)  # FL knee
        adjustments[5] += 2 * pitch_adjust if pitch > 0 else -2 * abs(pitch_adjust)  # FR thigh
        adjustments[6] += -2 * pitch_adjust if pitch > 0 else 2 * abs(pitch_adjust)  # FR knee
        adjustments[9] += 2 * pitch_adjust if pitch > 0 else -2 * abs(pitch_adjust)  # RL thigh
        adjustments[10] += -2 * pitch_adjust if pitch > 0 else 2 * abs(pitch_adjust)  # RL knee
        adjustments[13] += -2 * pitch_adjust if pitch > 0 else 2 * abs(pitch_adjust)  # RR thigh
        adjustments[14] += 2 * pitch_adjust if pitch > 0 else -2 * abs(pitch_adjust)  # RR knee

    # Handle roll
    if abs(roll) > 10:
        roll_adjust = roll - (10 if roll > 0 else -10)
        adjustments[0] += -2 * roll_adjust if roll > 0 else 2 * abs(roll_adjust)   # FL shoulder
        adjustments[1] += 2 * roll_adjust if roll > 0 else -2 * abs(roll_adjust)   # FL thigh
        adjustments[2] += -2 * roll_adjust if roll > 0 else 2 * abs(roll_adjust)   # FL knee
        adjustments[4] += -2 * roll_adjust if roll > 0 else 2 * abs(roll_adjust)   # FR shoulder
        adjustments[5] += 2 * roll_adjust if roll > 0 else -2 * abs(roll_adjust)   # FR thigh
        adjustments[6] += -2 * roll_adjust if roll > 0 else 2 * abs(roll_adjust)   # FR knee
        adjustments[8] += -2 * roll_adjust if roll > 0 else 2 * abs(roll_adjust)   # RL shoulder
        adjustments[9] += 2 * roll_adjust if roll > 0 else -2 * abs(roll_adjust)   # RL thigh
        adjustments[10] += -2 * roll_adjust if roll > 0 else 2 * abs(roll_adjust)  # RL knee
        adjustments[12] += -2 * roll_adjust if roll > 0 else 2 * abs(roll_adjust)  # RR shoulder
        adjustments[13] += 2 * roll_adjust if roll > 0 else -2 * abs(roll_adjust)  # RR thigh
        adjustments[14] += -2 * roll_adjust if roll > 0 else 2 * abs(roll_adjust)  # RR knee

    # Apply adjustments
    for channel, adjustment in adjustments.items():
        servo_type = servo_types[channel]
        max_angle = 180 if servo_type == "180" else 270
        new_angle = max(min(sitting_angles[channel] + adjustment, max_angle), 0)
        pwm_value = angle_to_pwm(new_angle, servo_type)
        pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)

# Main control loop
try:
    set_sitting_position()
    print("Balancing robot in sitting position. Press Ctrl+C to stop.")
    while True:
        pitch, roll = get_orientation()
        print(f"Pitch: {pitch:.2f}°, Roll: {roll:.2f}°")
        adjust_servos(pitch, roll)
        time.sleep(0.1)  # 10 Hz update rate
except KeyboardInterrupt:
    print("\nStopping balance control...")
finally:
    # Reset to sitting position on exit
    set_sitting_position()
    time.sleep(0.5)
    for i in range(16):
        pwm.channels[i].duty_cycle = 0
    print("Servos reset to neutral and deactivated.")