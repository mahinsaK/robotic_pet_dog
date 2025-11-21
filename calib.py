#!/usr/bin/env python3
import time
from mpu6050 import mpu6050
import json

# Initialize MPU-6050
try:
    sensor = mpu6050(0x68)  # Default I2C address
    print("MPU-6050 initialized successfully at address 0x68")
except Exception as e:
    print(f"Error initializing MPU-6050: {e}")
    print("Check I2C wiring, address (0x68 or 0x69), or run with sudo")
    exit(1)

# Calibration settings
num_samples = 1000  # Number of samples to average
sample_interval = 0.01  # Time between samples (seconds)

# Initialize accumulators for biases
accel_bias = {'x': 0, 'y': 0, 'z': 0}
gyro_bias = {'x': 0, 'y': 0, 'z': 0}

print("Starting MPU-6050 calibration...")
print("Keep the sensor stationary on a flat surface during calibration.")

# Collect samples
for i in range(num_samples):
    try:
        accel_data = sensor.get_accel_data()
        gyro_data = sensor.get_gyro_data()
        
        accel_bias['x'] += accel_data['x'] / num_samples
        accel_bias['y'] += accel_data['y'] / num_samples
        accel_bias['z'] += (accel_data['z'] - 9.81) / num_samples  # Subtract gravity (approx 9.81 m/s²)
        gyro_bias['x'] += gyro_data['x'] / num_samples
        gyro_bias['y'] += gyro_data['y'] / num_samples
        gyro_bias['z'] += gyro_data['z'] / num_samples
        
        if (i + 1) % 100 == 0:
            print(f"Collected {i + 1}/{num_samples} samples...")
        time.sleep(sample_interval)
    except Exception as e:
        print(f"Error reading sensor data: {e}")
        exit(1)

# Round biases to 4 decimal places
accel_bias = {k: round(v, 4) for k, v in accel_bias.items()}
gyro_bias = {k: round(v, 4) for k, v in gyro_bias.items()}

# Save calibration data to a file
calibration_data = {
    'accel_bias': accel_bias,
    'gyro_bias': gyro_bias
}
try:
    with open('mpu6050_calibration.json', 'w') as f:
        json.dump(calibration_data, f, indent=4)
    print("Calibration data saved to mpu6050_calibration.json")
except Exception as e:
    print(f"Error saving calibration data: {e}")

# Display results
print("\nCalibration Results:")
print(f"Accelerometer Bias (m/s²): {accel_bias}")
print(f"Gyroscope Bias (deg/s): {gyro_bias}")
print("\nUse these biases in your balance control script.")