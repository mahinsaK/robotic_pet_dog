#!/usr/bin/env python3
"""
Advanced MPU6050 Sensor with Complementary and Kalman Filters
This script provides precise orientation data using sensor fusion techniques.
"""

import smbus
import math
import time
import json
import os
import numpy as np
from collections import deque
import threading

class KalmanFilter:
    """
    1D Kalman filter for angle estimation
    """
    def __init__(self, Q_angle=0.001, Q_bias=0.003, R_measure=0.03):
        """
        Initialize Kalman filter
        
        Args:
            Q_angle: Process noise variance for angle
            Q_bias: Process noise variance for bias
            R_measure: Measurement noise variance
        """
        self.Q_angle = Q_angle
        self.Q_bias = Q_bias
        self.R_measure = R_measure
        
        self.angle = 0.0  # The angle calculated by the Kalman filter
        self.bias = 0.0   # The gyro bias calculated by the Kalman filter
        self.rate = 0.0   # Unbiased rate calculated from the rate and the calculated bias
        
        # Error covariance matrix
        self.P = np.array([[0.0, 0.0], [0.0, 0.0]])
        
    def get_angle(self, new_angle, new_rate, dt):
        """
        Update the Kalman filter with new measurements
        
        Args:
            new_angle: Angle measurement from accelerometer (degrees)
            new_rate: Angular rate from gyroscope (degrees/s)
            dt: Time step (seconds)
            
        Returns:
            Filtered angle (degrees)
        """
        # Predict step
        self.rate = new_rate - self.bias
        self.angle += dt * self.rate
        
        # Update error covariance matrix
        self.P[0][0] += dt * (dt * self.P[1][1] - self.P[0][1] - self.P[1][0] + self.Q_angle)
        self.P[0][1] -= dt * self.P[1][1]
        self.P[1][0] -= dt * self.P[1][1]
        self.P[1][1] += self.Q_bias * dt
        
        # Measurement update step
        S = self.P[0][0] + self.R_measure  # Innovation covariance
        K = [self.P[0][0] / S, self.P[1][0] / S]  # Kalman gain
        
        y = new_angle - self.angle  # Innovation or residual
        
        # Update angle and bias
        self.angle += K[0] * y
        self.bias += K[1] * y
        
        # Update error covariance matrix
        P00_temp = self.P[0][0]
        P01_temp = self.P[0][1]
        
        self.P[0][0] -= K[0] * P00_temp
        self.P[0][1] -= K[0] * P01_temp
        self.P[1][0] -= K[1] * P00_temp
        self.P[1][1] -= K[1] * P01_temp
        
        return self.angle

class ComplementaryFilter:
    """
    Complementary filter for sensor fusion
    """
    def __init__(self, alpha=0.98):
        """
        Initialize complementary filter
        
        Args:
            alpha: Weighting factor (0-1). Higher values favor gyroscope.
        """
        self.alpha = alpha
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.last_time = time.time()
        
    def update(self, accel_angle_x, accel_angle_y, gyro_rate_x, gyro_rate_y):
        """
        Update filter with new sensor data
        
        Args:
            accel_angle_x: Roll angle from accelerometer
            accel_angle_y: Pitch angle from accelerometer  
            gyro_rate_x: Angular rate around X axis
            gyro_rate_y: Angular rate around Y axis
            
        Returns:
            Tuple of (filtered_roll, filtered_pitch)
        """
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Complementary filter equations
        self.angle_x = self.alpha * (self.angle_x + gyro_rate_x * dt) + (1 - self.alpha) * accel_angle_x
        self.angle_y = self.alpha * (self.angle_y + gyro_rate_y * dt) + (1 - self.alpha) * accel_angle_y
        
        return self.angle_x, self.angle_y

class AdvancedMPU6050:
    """
    Advanced MPU6050 class with filtering capabilities
    """
    def __init__(self, bus_number=1, device_address=0x68):
        """
        Initialize MPU6050 sensor with advanced filtering
        """
        self.bus = smbus.SMBus(bus_number)
        self.device_address = device_address
        
        # MPU6050 register addresses
        self.PWR_MGMT_1 = 0x6B
        self.SMPLRT_DIV = 0x19
        self.CONFIG = 0x1A
        self.GYRO_CONFIG = 0x1B
        self.ACCEL_CONFIG = 0x1C
        self.INT_ENABLE = 0x38
        
        # Accelerometer registers
        self.ACCEL_XOUT_H = 0x3B
        self.ACCEL_YOUT_H = 0x3D
        self.ACCEL_ZOUT_H = 0x3F
        
        # Gyroscope registers
        self.GYRO_XOUT_H = 0x43
        self.GYRO_YOUT_H = 0x45
        self.GYRO_ZOUT_H = 0x47
        
        # Temperature register
        self.TEMP_OUT_H = 0x41
        
        # Initialize sensor
        self.initialize_sensor()
        
        # Load calibration
        self.calibration_data = self.load_calibration()
        
        # Initialize filters
        self.kalman_roll = KalmanFilter()
        self.kalman_pitch = KalmanFilter()
        self.complementary = ComplementaryFilter(alpha=0.98)
        
        # Data history for moving average
        self.data_history = {
            'accel_x': deque(maxlen=10),
            'accel_y': deque(maxlen=10),
            'accel_z': deque(maxlen=10),
            'gyro_x': deque(maxlen=10),
            'gyro_y': deque(maxlen=10),
            'gyro_z': deque(maxlen=10)
        }
        
        # Timing
        self.last_time = time.time()
        
        # Statistics
        self.reading_count = 0
        self.start_time = time.time()
        
    def initialize_sensor(self):
        """Initialize the MPU6050 sensor with optimized settings"""
        try:
            # Wake up the MPU6050
            self.bus.write_byte_data(self.device_address, self.PWR_MGMT_1, 0)
            time.sleep(0.1)
            
            # Set sample rate to 100Hz (1kHz / (9+1))
            self.bus.write_byte_data(self.device_address, self.SMPLRT_DIV, 9)
            
            # Set DLPF to 42Hz bandwidth for better noise filtering
            self.bus.write_byte_data(self.device_address, self.CONFIG, 3)
            
            # Set gyroscope range to ±500°/s for better precision
            self.bus.write_byte_data(self.device_address, self.GYRO_CONFIG, 0x08)
            
            # Set accelerometer range to ±4g for better sensitivity
            self.bus.write_byte_data(self.device_address, self.ACCEL_CONFIG, 0x08)
            
            # Enable data ready interrupt
            self.bus.write_byte_data(self.device_address, self.INT_ENABLE, 1)
            
            print("✅ Advanced MPU6050 initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing MPU6050: {e}")
            raise
    
    def read_raw_data(self, register):
        """Read raw 16-bit data from sensor register"""
        try:
            high = self.bus.read_byte_data(self.device_address, register)
            low = self.bus.read_byte_data(self.device_address, register + 1)
            
            value = (high << 8) | low
            if value > 32767:
                value = value - 65536
                
            return value
        except Exception as e:
            print(f"Error reading register {hex(register)}: {e}")
            return 0
    
    def get_raw_sensor_data(self):
        """Get raw sensor data with moving average filtering"""
        # Read raw data
        accel_x = self.read_raw_data(self.ACCEL_XOUT_H)
        accel_y = self.read_raw_data(self.ACCEL_YOUT_H)
        accel_z = self.read_raw_data(self.ACCEL_ZOUT_H)
        
        gyro_x = self.read_raw_data(self.GYRO_XOUT_H)
        gyro_y = self.read_raw_data(self.GYRO_YOUT_H)
        gyro_z = self.read_raw_data(self.GYRO_ZOUT_H)
        
        # Convert accelerometer (±4g range, 8192 LSB/g)
        accel_x_g = accel_x / 8192.0
        accel_y_g = accel_y / 8192.0
        accel_z_g = accel_z / 8192.0
        
        # Convert gyroscope (±500°/s range, 65.5 LSB/°/s)
        gyro_x_dps = gyro_x / 65.5
        gyro_y_dps = gyro_y / 65.5
        gyro_z_dps = gyro_z / 65.5
        
        # Apply calibration if available
        if self.calibration_data:
            accel_x_g -= self.calibration_data.get('accel_x_offset', 0)
            accel_y_g -= self.calibration_data.get('accel_y_offset', 0)
            accel_z_g -= self.calibration_data.get('accel_z_offset', 0)
            gyro_x_dps -= self.calibration_data.get('gyro_x_offset', 0)
            gyro_y_dps -= self.calibration_data.get('gyro_y_offset', 0)
            gyro_z_dps -= self.calibration_data.get('gyro_z_offset', 0)
        
        # Add to history for moving average
        self.data_history['accel_x'].append(accel_x_g)
        self.data_history['accel_y'].append(accel_y_g)
        self.data_history['accel_z'].append(accel_z_g)
        self.data_history['gyro_x'].append(gyro_x_dps)
        self.data_history['gyro_y'].append(gyro_y_dps)
        self.data_history['gyro_z'].append(gyro_z_dps)
        
        # Calculate moving averages
        accel_x_avg = sum(self.data_history['accel_x']) / len(self.data_history['accel_x'])
        accel_y_avg = sum(self.data_history['accel_y']) / len(self.data_history['accel_y'])
        accel_z_avg = sum(self.data_history['accel_z']) / len(self.data_history['accel_z'])
        gyro_x_avg = sum(self.data_history['gyro_x']) / len(self.data_history['gyro_x'])
        gyro_y_avg = sum(self.data_history['gyro_y']) / len(self.data_history['gyro_y'])
        gyro_z_avg = sum(self.data_history['gyro_z']) / len(self.data_history['gyro_z'])
        
        return {
            'accel': {'x': accel_x_avg, 'y': accel_y_avg, 'z': accel_z_avg},
            'gyro': {'x': gyro_x_avg, 'y': gyro_y_avg, 'z': gyro_z_avg},
            'raw_accel': {'x': accel_x, 'y': accel_y, 'z': accel_z},
            'raw_gyro': {'x': gyro_x, 'y': gyro_y, 'z': gyro_z}
        }
    
    def calculate_accelerometer_angles(self, accel_data):
        """Calculate roll and pitch from accelerometer data"""
        x = accel_data['x']
        y = accel_data['y']
        z = accel_data['z']
        
        # Calculate angles with better accuracy
        roll_rad = math.atan2(y, math.sqrt(x*x + z*z))
        pitch_rad = math.atan2(-x, math.sqrt(y*y + z*z))
        
        roll_deg = math.degrees(roll_rad)
        pitch_deg = math.degrees(pitch_rad)
        
        return roll_deg, pitch_deg
    
    def get_temperature(self):
        """Read temperature data"""
        temp_raw = self.read_raw_data(self.TEMP_OUT_H)
        temperature_c = (temp_raw / 340.0) + 36.53
        return temperature_c
    
    def load_calibration(self):
        """Load calibration data from file"""
        calibration_file = "/home/ubuntu/without_ros/mpu6050_calibration.json"
        try:
            if os.path.exists(calibration_file):
                with open(calibration_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Could not load calibration: {e}")
        return None
    
    def get_filtered_data(self):
        """Get data with all filtering applied"""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Ensure minimum dt to prevent division by zero
        if dt < 0.001:
            dt = 0.001
        
        # Get raw sensor data
        raw_data = self.get_raw_sensor_data()
        
        # Calculate accelerometer angles
        accel_roll, accel_pitch = self.calculate_accelerometer_angles(raw_data['accel'])
        
        # Get gyroscope rates
        gyro_roll_rate = raw_data['gyro']['x']
        gyro_pitch_rate = raw_data['gyro']['y']
        gyro_yaw_rate = raw_data['gyro']['z']
        
        # Apply Kalman filters
        kalman_roll = self.kalman_roll.get_angle(accel_roll, gyro_roll_rate, dt)
        kalman_pitch = self.kalman_pitch.get_angle(accel_pitch, gyro_pitch_rate, dt)
        
        # Apply complementary filter
        comp_roll, comp_pitch = self.complementary.update(
            accel_roll, accel_pitch, gyro_roll_rate, gyro_pitch_rate
        )
        
        # Update statistics
        self.reading_count += 1
        
        return {
            'timestamp': current_time,
            'dt': dt,
            'raw_data': raw_data,
            'accelerometer_angles': {
                'roll': accel_roll,
                'pitch': accel_pitch
            },
            'gyroscope_rates': {
                'roll': gyro_roll_rate,
                'pitch': gyro_pitch_rate,
                'yaw': gyro_yaw_rate
            },
            'kalman_filtered': {
                'roll': kalman_roll,
                'pitch': kalman_pitch
            },
            'complementary_filtered': {
                'roll': comp_roll,
                'pitch': comp_pitch
            },
            'temperature': self.get_temperature(),
            'statistics': {
                'reading_count': self.reading_count,
                'sample_rate': self.reading_count / (current_time - self.start_time) if (current_time - self.start_time) > 0 else 0
            }
        }

def display_filtered_data(data):
    """Display filtered sensor data in a comprehensive format"""
    # Clear screen (works on most terminals)
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("🚀 ADVANCED MPU6050 SENSOR DATA WITH FILTERS")
    print("=" * 80)
    print(f"Time: {time.strftime('%H:%M:%S')} | Sample Rate: {data['statistics']['sample_rate']:.1f} Hz | Count: {data['statistics']['reading_count']}")
    print("=" * 80)
    
    # Raw accelerometer data
    accel = data['raw_data']['accel']
    print(f"\n📊 RAW ACCELEROMETER (g-force):")
    print(f"   X: {accel['x']:8.4f} g   Y: {accel['y']:8.4f} g   Z: {accel['z']:8.4f} g")
    
    # Raw gyroscope data
    gyro = data['raw_data']['gyro']
    print(f"\n🔄 RAW GYROSCOPE (degrees/second):")
    print(f"   X: {gyro['x']:8.2f} °/s Y: {gyro['y']:8.2f} °/s Z: {gyro['z']:8.2f} °/s")
    
    # Accelerometer-derived angles
    accel_angles = data['accelerometer_angles']
    print(f"\n📐 ACCELEROMETER ANGLES:")
    print(f"   Roll: {accel_angles['roll']:8.2f}°   Pitch: {accel_angles['pitch']:8.2f}°")
    
    # Kalman filtered angles
    kalman = data['kalman_filtered']
    print(f"\n🎯 KALMAN FILTERED ANGLES:")
    print(f"   Roll: {kalman['roll']:8.2f}°   Pitch: {kalman['pitch']:8.2f}°")
    
    # Complementary filtered angles
    comp = data['complementary_filtered']
    print(f"\n⚖️  COMPLEMENTARY FILTERED ANGLES:")
    print(f"   Roll: {comp['roll']:8.2f}°   Pitch: {comp['pitch']:8.2f}°")
    
    # Temperature
    print(f"\n🌡️  TEMPERATURE: {data['temperature']:.2f}°C")
    
    # Additional metrics
    total_accel = math.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)
    total_gyro = math.sqrt(gyro['x']**2 + gyro['y']**2 + gyro['z']**2)
    
    print(f"\n📈 MAGNITUDE:")
    print(f"   Total Acceleration: {total_accel:.4f} g")
    print(f"   Total Gyro Rate:    {total_gyro:.2f} °/s")
    
    # Angle differences (for comparison)
    roll_diff_kc = abs(kalman['roll'] - comp['roll'])
    pitch_diff_kc = abs(kalman['pitch'] - comp['pitch'])
    
    print(f"\n🔍 FILTER COMPARISON:")
    print(f"   Roll Difference (K-C):  {roll_diff_kc:.3f}°")
    print(f"   Pitch Difference (K-C): {pitch_diff_kc:.3f}°")
    
    print(f"\n⏱️  Timing: dt = {data['dt']*1000:.2f} ms")
    print("-" * 80)

def main():
    """Main function"""
    print("🔬 Advanced MPU6050 with Kalman and Complementary Filters")
    print("=" * 60)
    
    try:
        # Initialize advanced MPU6050
        print("Initializing advanced MPU6050...")
        mpu = AdvancedMPU6050()
        
        # Wait for filters to stabilize
        print("Stabilizing filters...")
        for i in range(10):
            mpu.get_filtered_data()
            time.sleep(0.1)
        
        print("\n✅ System ready! Starting continuous monitoring...")
        print("Press Ctrl+C to stop\n")
        
        # Continuous monitoring
        try:
            while True:
                data = mpu.get_filtered_data()
                display_filtered_data(data)
                time.sleep(0.05)  # 20Hz display rate
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped.")
            
            # Display final statistics
            final_data = mpu.get_filtered_data()
            runtime = time.time() - mpu.start_time
            
            print(f"\n📊 SESSION STATISTICS:")
            print(f"   Runtime: {runtime:.1f} seconds")
            print(f"   Total readings: {final_data['statistics']['reading_count']}")
            print(f"   Average sample rate: {final_data['statistics']['sample_rate']:.1f} Hz")
            print("\n👋 Goodbye!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check I2C connections (SDA, SCL, VCC, GND)")
        print("2. Verify I2C is enabled: sudo raspi-config")
        print("3. Check I2C devices: sudo i2cdetect -y 1")
        print("4. Install required packages:")
        print("   sudo apt-get install python3-smbus python3-numpy")

if __name__ == "__main__":
    main()
