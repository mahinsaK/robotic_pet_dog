#!/usr/bin/env python3
import board
import busio
import time
import math
import smbus
from adafruit_pca9685 import PCA9685
from mpu6050 import mpu6050

# Initialize I2C bus
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    print("I2C bus initialized successfully")
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit(1)

# Initialize PCA9685
try:
    pwm = PCA9685(i2c)
    pwm.frequency = 50  # 50 Hz for DS3240 servos
    print("PCA9685 initialized successfully")
except Exception as e:
    print(f"Error initializing PCA9685: {e}")
    exit(1)

# Initialize MPU-6050 with error handling and recovery
def initialize_mpu6050(max_retries=5):
    for attempt in range(max_retries):
        try:
            print(f"Attempting to initialize MPU-6050 (attempt {attempt + 1}/{max_retries})")
            sensor = mpu6050(0x68)
            
            # Test sensor by reading data once
            test_data = sensor.get_accel_data()
            print("MPU-6050 initialized successfully")
            return sensor
            
        except Exception as e:
            print(f"MPU-6050 initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Waiting 2 seconds before retry...")
                time.sleep(2)
            else:
                print("Failed to initialize MPU-6050 after all attempts")
                return None
    return None

sensor = initialize_mpu6050()
if sensor is None:
    print("Could not initialize MPU-6050. Exiting...")
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

# Sitting position angles (neutral/reference position)
sitting_angles = {
    0: 207,   # FL shoulder
    1: 70,    # FL thigh
    2: 50,    # FL knee
    4: 90,    # FR shoulder
    5: 55,    # FR thigh
    6: 110,   # FR knee
    8: 220,   # RL shoulder
    9: 79,    # RL thigh
    10: 50,   # RL knee
    12: 115,  # RR shoulder
    13: 45,   # RR thigh
    14: 105   # RR knee
}

# Servo channel mapping for easier reference
channels = {
    'FL_shoulder': 0, 'FL_thigh': 1, 'FL_knee': 2,
    'FR_shoulder': 4, 'FR_thigh': 5, 'FR_knee': 6,
    'RL_shoulder': 8, 'RL_thigh': 9, 'RL_knee': 10,
    'RR_shoulder': 12, 'RR_thigh': 13, 'RR_knee': 14
}

# Balance control configuration
DEAD_ZONE = 10.0  # Ignore first 10 degrees
ADJUSTMENT_RATE = 2.0  # 2 degrees servo adjustment per 1 degree of tilt
UPDATE_RATE = 0.05  # 50ms update rate (20 Hz)

def angle_to_pwm(angle, servo_type):
    """Convert angle to PWM value based on servo type"""
    if servo_type == "180":
        min_angle, max_angle = 0, 180
        min_pwm, max_pwm = 100, 500
    else:  # 270° servo
        min_angle, max_angle = 0, 270
        min_pwm, max_pwm = 100, 500
    
    # Clamp angle to valid range
    angle = max(min(angle, max_angle), min_angle)
    pwm_value = int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))
    return pwm_value

def set_servo_angle(channel, angle):
    """Set servo to specified angle"""
    servo_type = servo_types[channel]
    max_angle = 180 if servo_type == "180" else 270
    
    # Clamp angle to servo limits
    angle = max(0, min(angle, max_angle))
    
    pwm_value = angle_to_pwm(angle, servo_type)
    pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
    return angle

def get_balance_adjustments(pitch, roll):
    """Calculate servo adjustments based on pitch and roll angles"""
    adjustments = {}
    
    # Initialize all adjustments to 0
    for channel in sitting_angles.keys():
        adjustments[channel] = 0
    
    # Apply dead zone - ignore first 10 degrees
    effective_pitch = pitch - DEAD_ZONE if pitch > DEAD_ZONE else (pitch + DEAD_ZONE if pitch < -DEAD_ZONE else 0)
    effective_roll = roll - DEAD_ZONE if roll > DEAD_ZONE else (roll + DEAD_ZONE if roll < -DEAD_ZONE else 0)
    
    # Pitch adjustments
    if effective_pitch != 0:
        pitch_adjustment = effective_pitch * ADJUSTMENT_RATE
        
        if effective_pitch > 0:  # Positive pitch
            adjustments[channels['FL_thigh']] -= pitch_adjustment
            adjustments[channels['FL_knee']] += pitch_adjustment
            adjustments[channels['FR_thigh']] += pitch_adjustment
            adjustments[channels['FR_knee']] -= pitch_adjustment
            adjustments[channels['RL_thigh']] += pitch_adjustment
            adjustments[channels['RL_knee']] -= pitch_adjustment
            adjustments[channels['RR_thigh']] -= pitch_adjustment
            adjustments[channels['RR_knee']] += pitch_adjustment
        else:  # Negative pitch
            adjustments[channels['FL_thigh']] -= pitch_adjustment  # pitch_adjustment is negative, so this adds
            adjustments[channels['FL_knee']] += pitch_adjustment   # this subtracts
            adjustments[channels['FR_thigh']] += pitch_adjustment  # this subtracts
            adjustments[channels['FR_knee']] -= pitch_adjustment   # this adds
            adjustments[channels['RL_thigh']] += pitch_adjustment  # this subtracts
            adjustments[channels['RL_knee']] -= pitch_adjustment   # this adds
            adjustments[channels['RR_thigh']] -= pitch_adjustment  # this adds
            adjustments[channels['RR_knee']] += pitch_adjustment   # this subtracts
    
    # Roll adjustments
    if effective_roll != 0:
        roll_adjustment = effective_roll * ADJUSTMENT_RATE
        
        if effective_roll > 0:  # Positive roll
            adjustments[channels['FL_shoulder']] -= roll_adjustment
            adjustments[channels['FL_thigh']] += roll_adjustment
            adjustments[channels['FL_knee']] -= roll_adjustment
            adjustments[channels['FR_shoulder']] -= roll_adjustment
            adjustments[channels['FR_thigh']] += roll_adjustment
            adjustments[channels['FR_knee']] -= roll_adjustment
            adjustments[channels['RL_shoulder']] -= roll_adjustment
            adjustments[channels['RL_thigh']] += roll_adjustment
            adjustments[channels['RL_knee']] -= roll_adjustment
            adjustments[channels['RR_shoulder']] -= roll_adjustment
            adjustments[channels['RR_thigh']] += roll_adjustment
            adjustments[channels['RR_knee']] -= roll_adjustment
        else:  # Negative roll
            adjustments[channels['FL_shoulder']] -= roll_adjustment  # roll_adjustment is negative, so this adds
            adjustments[channels['FL_thigh']] += roll_adjustment     # this subtracts
            adjustments[channels['FL_knee']] -= roll_adjustment      # this adds
            adjustments[channels['FR_shoulder']] -= roll_adjustment  # this adds
            adjustments[channels['FR_thigh']] += roll_adjustment     # this subtracts
            adjustments[channels['FR_knee']] -= roll_adjustment      # this adds
            adjustments[channels['RL_shoulder']] -= roll_adjustment  # this adds
            adjustments[channels['RL_thigh']] += roll_adjustment     # this subtracts
            adjustments[channels['RL_knee']] -= roll_adjustment      # this adds
            adjustments[channels['RR_shoulder']] -= roll_adjustment  # this adds
            adjustments[channels['RR_thigh']] += roll_adjustment     # this subtracts
            adjustments[channels['RR_knee']] -= roll_adjustment      # this adds
    
    return adjustments

def move_to_sitting_position():
    """Move all servos to sitting position"""
    print("Moving to sitting position...")
    for channel, angle in sitting_angles.items():
        set_servo_angle(channel, angle)
    time.sleep(1.0)  # Allow time for servos to reach position
    print("Sitting position reached")

def read_sensor_data_with_retry(sensor, max_retries=3):
    """Read sensor data with error handling and retry logic"""
    for attempt in range(max_retries):
        try:
            accel_data = sensor.get_accel_data()
            gyro_data = sensor.get_gyro_data()
            return accel_data, gyro_data
        except OSError as e:
            if e.errno == 121:  # Remote I/O error
                print(f"I/O error on attempt {attempt + 1}, retrying...")
                time.sleep(0.1)  # Brief delay before retry
                if attempt == max_retries - 1:
                    print("Max retries reached, sensor may be disconnected")
                    raise
            else:
                raise
        except Exception as e:
            print(f"Unexpected sensor error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(0.1)
    
    return None, None
    """Calculate pitch and roll from accelerometer data"""
    ax, ay, az = accel_data['x'], accel_data['y'], accel_data['z']
    
    # Calculate pitch and roll in degrees
    pitch = math.atan2(ax, math.sqrt(ay*ay + az*az)) * 180 / math.pi
    roll = math.atan2(ay, math.sqrt(ax*ax + az*az)) * 180 / math.pi
    
    return pitch, roll

def main():
    print("SpotMicro Balance Control System")
    print("================================")
    print(f"Dead zone: {DEAD_ZONE} degrees")
    print(f"Adjustment rate: {ADJUSTMENT_RATE} degrees servo per degree tilt")
    print(f"Update rate: {1/UPDATE_RATE} Hz")
    print("Press Ctrl+C to stop")
    
    # Move to sitting position
    move_to_sitting_position()
    
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    try:
        while True:
            try:
                # Read sensor data with retry logic
                accel_data, gyro_data = read_sensor_data_with_retry(sensor)
                
                if accel_data is None or gyro_data is None:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print("Too many consecutive sensor errors. Stopping...")
                        break
                    continue
                
                # Reset error counter on successful read
                consecutive_errors = 0
                
                # Calculate pitch and roll
                pitch, roll = calculate_pitch_roll(accel_data, gyro_data)
                
                # Get balance adjustments
                adjustments = get_balance_adjustments(pitch, roll)
                
                # Apply adjustments to servos
                adjusted_angles = {}
                for channel in sitting_angles.keys():
                    new_angle = sitting_angles[channel] + adjustments[channel]
                    adjusted_angles[channel] = set_servo_angle(channel, new_angle)
                
                # Print status (every 20 iterations to avoid spam)
                if int(time.time() * 20) % 20 == 0:
                    print(f"Pitch: {pitch:6.2f}°, Roll: {roll:6.2f}°", end="")
                    if abs(pitch) > DEAD_ZONE or abs(roll) > DEAD_ZONE:
                        print(" [BALANCING]")
                    else:
                        print(" [STABLE]")
                
                time.sleep(UPDATE_RATE)
                
            except OSError as e:
                if e.errno == 121:
                    consecutive_errors += 1
                    print(f"I/O error occurred (count: {consecutive_errors})")
                    if consecutive_errors >= max_consecutive_errors:
                        print("Too many I/O errors. Sensor may be disconnected.")
                        break
                    time.sleep(0.5)  # Wait before continuing
                else:
                    raise
            
    except KeyboardInterrupt:
        print("\nStopping balance control...")
        
    finally:
        # Return to sitting position
        move_to_sitting_position()
        
        # Clear all PWM signals
        for i in range(16):
            pwm.channels[i].duty_cycle = 0
        
        print("Balance control stopped. All servos deactivated.")

if __name__ == "__main__":
    main()