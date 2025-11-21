#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685

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

# Clear all PWM signals at start
for i in range(16):
    pwm.channels[i].duty_cycle = 0

# Valid channels and their servo types
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8:"180", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
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

# User Instructions
print("Servo Control: Channels 0,1,2,4,5,6,8,9,10,12,13,14")
print("Channels 6,10,14 (180°?): 0-180 degrees")
print("Channels 0,1,2,4,5,8,9,12,13 (270°?): 0-270 degrees")
print("Enter 'q' to quit")

while True:
    channel_input = input("Enter channel number or 'q' to quit: ")
    if channel_input.lower() == 'q':
        break
    try:
        channel = int(channel_input)
        if channel not in servo_types:
            print("Invalid channel.")
            continue
    except ValueError:
        print("Invalid input.")
        continue

    servo_type = servo_types[channel]
    max_angle = 180 if servo_type == "180" else 270
    angle_input = input(f"Enter angle (0-{max_angle}): ")
    try:
        angle = float(angle_input)
        if not 0 <= angle <= max_angle:
            print(f"Invalid angle. Use 0{max_angle}.")
            continue
    except ValueError:
        print("Invalid angle input.")
        continue

    pwm_value = angle_to_pwm(angle, servo_type)
    print(f"Setting channel {channel} ({servo_type}°) to {angle}° (PWM: {pwm_value})")
    pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
    input("Press Enter to continue...")

    # Optional: deactivate channel after movement (may reduce twitching)
    pwm.channels[channel].duty_cycle = 0

# Reset all servos to neutral at end
print("Resetting all servos to neutral position...")
for channel, servo_type in servo_types.items():
    neutral_angle = 90 if servo_type == "180" else 135
    pwm_value = angle_to_pwm(neutral_angle, servo_type)
    pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)

print("Control complete. All servos reset to neutral.")

