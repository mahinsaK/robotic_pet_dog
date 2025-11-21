#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685
from mpu6050 import mpu6050
import time
import math

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
    sensor = mpu6050(0x68)  # Default I2C address
    print("MPU-6050 initialized at address 0x68")
except Exception as e:
    print(f"Error initializing MPU-6050: {e}")
    exit(1)

# Servo configuration
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "180", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Sitting position angles
sitting_angles = {
    0: 207,  # FL shoulder
    1: 70,   # FL thigh
    2: 50,   # FL knee
    4: 90,   # FR shoulder
    5: 55,   # FR thigh
    6: 110,  # FR knee
    8: 150,  # RL shoulder
    9: 79,   # RL thigh
    10: 50,  # RL knee
    12: 115, # RR shoulder
    13: 45,  # RR thigh
    14: 105  # RR knee
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
for channel, angle in sitting_angles.items():
    pwm_value = angle_to_pwm(angle, servo_types[channel])
    pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)

# Calibration biases from calibration script
accel_bias = {'x': 0.6829, 'y': -0.1726, 'z': 0.1176}
gyro_bias = {'x': -1.7045, 'y': 1.1312, 'z': 0.5857}
print("Using calibration biases:")
print(f"Accelerometer Bias (m/s²): {accel_bias}")
print(f"Gyroscope Bias (deg/s): {gyro_bias}")

# Complementary filter constants
alpha = 0.98
dt = 0.05  # 50ms loop time
accel_angle = {'pitch': 0, 'roll': 0}
gyro_angle = {'pitch': 0, 'roll': 0}

try:
    while True:
        # Read accelerometer and gyroscope data
        accel_data = sensor.get_accel_data()
        gyro_data = sensor.get_gyro_data()

        # Apply calibration biases
        accel_x = accel_data['x'] - accel_bias['x']
        accel_y = accel_data['y'] - accel_bias['y']
        accel_z = accel_data['z'] - accel_bias['z']
        gyro_x = gyro_data['x'] - gyro_bias['x']
        gyro_y = gyro_data['y'] - gyro_bias['y']

        # Calculate accelerometer-based pitch and roll
        accel_pitch = math.atan2(accel_y, math.sqrt(accel_x**2 + accel_z**2)) * 180 / math.pi
        accel_roll = math.atan2(-accel_x, accel_z) * 180 / math.pi

        # Calculate gyroscope-based pitch and roll
        gyro_angle['pitch'] += gyro_y * dt
        gyro_angle['roll'] += gyro_x * dt

        # Apply complementary filter
        accel_angle['pitch'] = alpha * (accel_angle['pitch'] + gyro_y * dt) + (1 - alpha) * accel_pitch
        accel_angle['roll'] = alpha * (accel_angle['roll'] + gyro_x * dt) + (1 - alpha) * accel_roll

        pitch = accel_angle['pitch']
        roll = accel_angle['roll']

        # Initialize angle adjustments
        adjustments = {ch: 0 for ch in sitting_angles}

        # Apply pitch adjustments (no 10-degree deadband)
        if pitch > 0:
            adjustments[1] -= 2 * pitch  # FL thigh
            adjustments[2] += 2 * pitch  # FL knee
            adjustments[5] += 2 * pitch  # FR thigh
            adjustments[6] -= 2 * pitch  # FR knee
            adjustments[9] += 2 * pitch  # RL thigh
            adjustments[10] -= 2 * pitch  # RL knee
            adjustments[13] -= 2 * pitch  # RR thigh
            adjustments[14] += 2 * pitch  # RR knee
        elif pitch < 0:
            adjustments[1] += 2 * (-pitch)  # FL thigh
            adjustments[2] -= 2 * (-pitch)  # FL knee
            adjustments[5] -= 2 * (-pitch)  # FR thigh
            adjustments[6] += 2 * (-pitch)  # FR knee
            adjustments[9] -= 2 * (-pitch)  # RL thigh
            adjustments[10] += 2 * (-pitch)  # RL knee
            adjustments[13] += 2 * (-pitch)  # RR thigh
            adjustments[14] -= 2 * (-pitch)  # RR knee

        # Apply roll adjustments (no 10-degree deadband)
        if roll > 0:
            adjustments[0] -= 1 * roll  # FL shoulder
            adjustments[1] += 1 * roll  # FL thigh
            adjustments[2] -= 1 * roll  # FL knee
            adjustments[4] -= 1 * roll  # FR shoulder
            adjustments[5] += 1 * roll  # FR thigh
            adjustments[6] -= 1 * roll  # FR knee
            adjustments[8] -= 1 * roll  # RL shoulder
            adjustments[9] += 1 * roll  # RL thigh
            adjustments[10] -= 1 * roll  # RL knee
            adjustments[12] -= 1 * roll  # RR shoulder
            adjustments[13] += 1 * roll  # RR thigh
            adjustments[14] -= 1 * roll  # RR knee
        elif roll < 0:
            adjustments[0] += 1 * (-roll)  # FL shoulder
            adjustments[1] -= 1 * (-roll)  # FL thigh
            adjustments[2] += 1 * (-roll)  # FL knee
            adjustments[4] += 1 * (-roll)  # FR shoulder
            adjustments[5] -= 1 * (-roll)  # FR thigh
            adjustments[6] += 1 * (-roll)  # FR knee
            adjustments[8] += 1 * (-roll)  # RL shoulder
            adjustments[9] -= 1 * (-roll)  # RL thigh
            adjustments[10] += 1 * (-roll)  # RL knee
            adjustments[12] += 1 * (-roll)  # RR shoulder
            adjustments[13] -= 1 * (-roll)  # RR thigh
            adjustments[14] += 1 * (-roll)  # RR knee

        # Apply adjustments and update servos
        for channel in sitting_angles:
            new_angle = sitting_angles[channel] + adjustments[channel]
            servo_type = servo_types[channel]
            max_angle = 180 if servo_type == "180" else 270
            new_angle = max(min(new_angle, max_angle), 0)
            pwm_value = angle_to_pwm(new_angle, servo_type)
            pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)

        time.sleep(dt)

except KeyboardInterrupt:
    print("Resetting all servos to neutral position...")
    for channel, servo_type in servo_types.items():
        neutral_angle = 90 if servo_type == "180" else 135
        pwm_value = angle_to_pwm(neutral_angle, servo_type)
        pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
    print("Program terminated.")