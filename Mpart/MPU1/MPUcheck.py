#!/usr/bin/env python3
"""
MPU6050 Sensor Value Checker
This script reads and displays accelerometer and gyroscope values from the MPU6050 sensor.
"""

import smbus
import math
import time
import json
import os

class MPU6050:
    def __init__(self, bus_number=1, device_address=0x68):
        """
        Initialize MPU6050 sensor
        
        Args:
            bus_number: I2C bus number (usually 1 for Raspberry Pi)
            device_address: MPU6050 I2C address (default 0x68)
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
        self.ACCEL_XOUT_L = 0x3C
        self.ACCEL_YOUT_H = 0x3D
        self.ACCEL_YOUT_L = 0x3E
        self.ACCEL_ZOUT_H = 0x3F
        self.ACCEL_ZOUT_L = 0x40
        
        # Gyroscope registers
        self.GYRO_XOUT_H = 0x43
        self.GYRO_XOUT_L = 0x44
        self.GYRO_YOUT_H = 0x45
        self.GYRO_YOUT_L = 0x46
        self.GYRO_ZOUT_H = 0x47
        self.GYRO_ZOUT_L = 0x48
        
        # Temperature register
        self.TEMP_OUT_H = 0x41
        self.TEMP_OUT_L = 0x42
        
        # Initialize the sensor
        self.initialize_sensor()
        
        # Load calibration values if available
        self.calibration_data = self.load_calibration()
        
    def initialize_sensor(self):
        """Initialize the MPU6050 sensor with default settings"""
        try:
            # Wake up the MPU6050 (it starts in sleep mode)
            self.bus.write_byte_data(self.device_address, self.PWR_MGMT_1, 0)
            
            # Set sample rate divider (1kHz sample rate)
            self.bus.write_byte_data(self.device_address, self.SMPLRT_DIV, 7)
            
            # Set configuration register (disable FSYNC, 260Hz DLPF)
            self.bus.write_byte_data(self.device_address, self.CONFIG, 0)
            
            # Set gyroscope configuration (±250°/s)
            self.bus.write_byte_data(self.device_address, self.GYRO_CONFIG, 0)
            
            # Set accelerometer configuration (±2g)
            self.bus.write_byte_data(self.device_address, self.ACCEL_CONFIG, 0)
            
            # Enable data ready interrupt
            self.bus.write_byte_data(self.device_address, self.INT_ENABLE, 1)
            
            print("MPU6050 initialized successfully!")
            
        except Exception as e:
            print(f"Error initializing MPU6050: {e}")
            raise
    
    def read_raw_data(self, register):
        """Read raw 16-bit data from sensor register"""
        try:
            # Read high and low bytes
            high = self.bus.read_byte_data(self.device_address, register)
            low = self.bus.read_byte_data(self.device_address, register + 1)
            
            # Combine bytes to get 16-bit value
            value = (high << 8) | low
            
            # Convert to signed value
            if value > 32767:
                value = value - 65536
                
            return value
        except Exception as e:
            print(f"Error reading register {hex(register)}: {e}")
            return 0
    
    def get_accelerometer_data(self):
        """Read accelerometer data and convert to g-force"""
        # Read raw accelerometer data
        accel_x = self.read_raw_data(self.ACCEL_XOUT_H)
        accel_y = self.read_raw_data(self.ACCEL_YOUT_H)
        accel_z = self.read_raw_data(self.ACCEL_ZOUT_H)
        
        # Convert to g-force (±2g range, 16384 LSB/g)
        accel_x_g = accel_x / 16384.0
        accel_y_g = accel_y / 16384.0
        accel_z_g = accel_z / 16384.0
        
        # Apply calibration if available
        if self.calibration_data:
            accel_x_g -= self.calibration_data.get('accel_x_offset', 0)
            accel_y_g -= self.calibration_data.get('accel_y_offset', 0)
            accel_z_g -= self.calibration_data.get('accel_z_offset', 0)
        
        return {
            'x': accel_x_g,
            'y': accel_y_g,
            'z': accel_z_g,
            'raw_x': accel_x,
            'raw_y': accel_y,
            'raw_z': accel_z
        }
    
    def get_gyroscope_data(self):
        """Read gyroscope data and convert to degrees per second"""
        # Read raw gyroscope data
        gyro_x = self.read_raw_data(self.GYRO_XOUT_H)
        gyro_y = self.read_raw_data(self.GYRO_YOUT_H)
        gyro_z = self.read_raw_data(self.GYRO_ZOUT_H)
        
        # Convert to degrees per second (±250°/s range, 131 LSB/°/s)
        gyro_x_dps = gyro_x / 131.0
        gyro_y_dps = gyro_y / 131.0
        gyro_z_dps = gyro_z / 131.0
        
        # Apply calibration if available
        if self.calibration_data:
            gyro_x_dps -= self.calibration_data.get('gyro_x_offset', 0)
            gyro_y_dps -= self.calibration_data.get('gyro_y_offset', 0)
            gyro_z_dps -= self.calibration_data.get('gyro_z_offset', 0)
        
        return {
            'x': gyro_x_dps,
            'y': gyro_y_dps,
            'z': gyro_z_dps,
            'raw_x': gyro_x,
            'raw_y': gyro_y,
            'raw_z': gyro_z
        }
    
    def get_temperature(self):
        """Read temperature data"""
        temp_raw = self.read_raw_data(self.TEMP_OUT_H)
        # Convert to Celsius (temperature in degrees C = (TEMP_OUT Register Value as a signed number)/340 + 36.53)
        temperature_c = (temp_raw / 340.0) + 36.53
        temperature_f = (temperature_c * 9/5) + 32
        
        return {
            'celsius': temperature_c,
            'fahrenheit': temperature_f,
            'raw': temp_raw
        }
    
    def calculate_angles(self, accel_data):
        """Calculate roll and pitch angles from accelerometer data"""
        x = accel_data['x']
        y = accel_data['y']
        z = accel_data['z']
        
        # Calculate roll and pitch in radians
        roll_rad = math.atan2(y, math.sqrt(x*x + z*z))
        pitch_rad = math.atan2(-x, math.sqrt(y*y + z*z))
        
        # Convert to degrees
        roll_deg = math.degrees(roll_rad)
        pitch_deg = math.degrees(pitch_rad)
        
        return {
            'roll': roll_deg,
            'pitch': pitch_deg,
            'roll_rad': roll_rad,
            'pitch_rad': pitch_rad
        }
    
    def load_calibration(self):
        """Load calibration data from file"""
        calibration_file = "/home/ubuntu/without_ros/mpu6050_calibration.json"
        try:
            if os.path.exists(calibration_file):
                with open(calibration_file, 'r') as f:
                    calibration_data = json.load(f)
                print("Calibration data loaded successfully!")
                return calibration_data
        except Exception as e:
            print(f"Could not load calibration data: {e}")
        return None
    
    def get_all_data(self):
        """Get all sensor data in a single call"""
        accel_data = self.get_accelerometer_data()
        gyro_data = self.get_gyroscope_data()
        temp_data = self.get_temperature()
        angles = self.calculate_angles(accel_data)
        
        return {
            'accelerometer': accel_data,
            'gyroscope': gyro_data,
            'temperature': temp_data,
            'angles': angles,
            'timestamp': time.time()
        }

def display_sensor_data(mpu):
    """Display sensor data in a formatted way"""
    print("\n" + "="*60)
    print("MPU6050 SENSOR DATA")
    print("="*60)
    
    try:
        data = mpu.get_all_data()
        
        # Accelerometer data
        accel = data['accelerometer']
        print(f"\n📊 ACCELEROMETER (g-force):")
        print(f"   X: {accel['x']:8.3f} g  (Raw: {accel['raw_x']:6d})")
        print(f"   Y: {accel['y']:8.3f} g  (Raw: {accel['raw_y']:6d})")
        print(f"   Z: {accel['z']:8.3f} g  (Raw: {accel['raw_z']:6d})")
        
        # Gyroscope data
        gyro = data['gyroscope']
        print(f"\n🔄 GYROSCOPE (degrees/second):")
        print(f"   X: {gyro['x']:8.3f} °/s (Raw: {gyro['raw_x']:6d})")
        print(f"   Y: {gyro['y']:8.3f} °/s (Raw: {gyro['raw_y']:6d})")
        print(f"   Z: {gyro['z']:8.3f} °/s (Raw: {gyro['raw_z']:6d})")
        
        # Temperature data
        temp = data['temperature']
        print(f"\n🌡️  TEMPERATURE:")
        print(f"   {temp['celsius']:6.2f} °C / {temp['fahrenheit']:6.2f} °F (Raw: {temp['raw']:6d})")
        
        # Calculated angles
        angles = data['angles']
        print(f"\n📐 CALCULATED ANGLES:")
        print(f"   Roll:  {angles['roll']:7.2f}°")
        print(f"   Pitch: {angles['pitch']:7.2f}°")
        
        # Additional calculations
        total_accel = math.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)
        total_gyro = math.sqrt(gyro['x']**2 + gyro['y']**2 + gyro['z']**2)
        
        print(f"\n📈 MAGNITUDE:")
        print(f"   Total Acceleration: {total_accel:.3f} g")
        print(f"   Total Gyro Rate:    {total_gyro:.3f} °/s")
        
    except Exception as e:
        print(f"Error reading sensor data: {e}")

def calibrate_sensor(mpu, samples=100):
    """Perform basic calibration by averaging readings when sensor is stationary"""
    print(f"\n🔧 CALIBRATING SENSOR...")
    print("Please keep the sensor stationary during calibration!")
    print("Calibration will start in 3 seconds...")
    
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("Calibrating... Please wait.")
    
    accel_x_total = accel_y_total = accel_z_total = 0
    gyro_x_total = gyro_y_total = gyro_z_total = 0
    
    for i in range(samples):
        data = mpu.get_all_data()
        accel = data['accelerometer']
        gyro = data['gyroscope']
        
        accel_x_total += accel['x']
        accel_y_total += accel['y']
        accel_z_total += accel['z'] - 1.0  # Subtract 1g for gravity
        
        gyro_x_total += gyro['x']
        gyro_y_total += gyro['y']
        gyro_z_total += gyro['z']
        
        if (i + 1) % 20 == 0:
            print(f"Progress: {i + 1}/{samples}")
        
        time.sleep(0.01)
    
    # Calculate averages (these are the offsets)
    calibration_data = {
        'accel_x_offset': accel_x_total / samples,
        'accel_y_offset': accel_y_total / samples,
        'accel_z_offset': accel_z_total / samples,
        'gyro_x_offset': gyro_x_total / samples,
        'gyro_y_offset': gyro_y_total / samples,
        'gyro_z_offset': gyro_z_total / samples,
        'calibration_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save calibration data
    calibration_file = "/home/ubuntu/without_ros/mpu6050_calibration.json"
    try:
        with open(calibration_file, 'w') as f:
            json.dump(calibration_data, f, indent=2)
        print(f"✅ Calibration completed and saved to {calibration_file}")
        print("\nCalibration offsets:")
        print(f"  Accelerometer: X={calibration_data['accel_x_offset']:.6f}, Y={calibration_data['accel_y_offset']:.6f}, Z={calibration_data['accel_z_offset']:.6f}")
        print(f"  Gyroscope:     X={calibration_data['gyro_x_offset']:.6f}, Y={calibration_data['gyro_y_offset']:.6f}, Z={calibration_data['gyro_z_offset']:.6f}")
    except Exception as e:
        print(f"❌ Error saving calibration: {e}")
        return None
    
    return calibration_data

def main():
    """Main function to demonstrate MPU6050 functionality"""
    print("🤖 MPU6050 Sensor Checker")
    print("=" * 40)
    
    try:
        # Initialize MPU6050
        print("Initializing MPU6050...")
        mpu = MPU6050()
        
        while True:
            print("\nChoose an option:")
            print("1. Read sensor values once")
            print("2. Continuous monitoring")
            print("3. Calibrate sensor")
            print("4. Test sensor connection")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                display_sensor_data(mpu)
                
            elif choice == '2':
                print("\n🔄 CONTINUOUS MONITORING (Press Ctrl+C to stop)")
                print("-" * 50)
                try:
                    while True:
                        display_sensor_data(mpu)
                        time.sleep(1)
                        print("\n" + "-" * 60)
                except KeyboardInterrupt:
                    print("\n\n⏹️  Monitoring stopped.")
                    
            elif choice == '3':
                calibrate_sensor(mpu)
                # Reload the sensor with new calibration
                mpu = MPU6050()
                
            elif choice == '4':
                print("\n🔍 TESTING SENSOR CONNECTION...")
                try:
                    data = mpu.get_all_data()
                    print("✅ Sensor connection OK!")
                    print(f"   Sample reading - Accel X: {data['accelerometer']['x']:.3f}g")
                except Exception as e:
                    print(f"❌ Sensor connection failed: {e}")
                    
            elif choice == '5':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
    except Exception as e:
        print(f"❌ Error initializing MPU6050: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check I2C connections (SDA, SCL, VCC, GND)")
        print("2. Verify I2C is enabled: sudo raspi-config")
        print("3. Check I2C devices: sudo i2cdetect -y 1")
        print("4. Install required packages: sudo apt-get install python3-smbus")

if __name__ == "__main__":
    main()