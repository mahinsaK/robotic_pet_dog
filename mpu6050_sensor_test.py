#!/usr/bin/env python3
"""
Simple MPU6050 test script to verify sensor connection and readings
"""
import smbus
import math
import time

# MPU6050 Configuration
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F

# Initialize I2C for MPU6050
try:
    bus = smbus.SMBus(1)  # I2C bus 1
    print("✅ I2C bus initialized successfully")
except Exception as e:
    print(f"❌ Error initializing I2C bus: {e}")
    exit(1)

def init_mpu6050():
    """Initialize MPU6050 sensor"""
    try:
        # Wake up the MPU6050
        bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
        print("✅ MPU6050 initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing MPU6050: {e}")
        return False

def read_raw_data(addr):
    """Read raw 16-bit data from MPU6050"""
    try:
        high = bus.read_byte_data(MPU6050_ADDR, addr)
        low = bus.read_byte_data(MPU6050_ADDR, addr + 1)
        value = ((high << 8) | low)
        if value > 32768:
            value = value - 65536
        return value
    except Exception as e:
        print(f"❌ Error reading from address {addr}: {e}")
        return 0

def get_mpu6050_data():
    """Get accelerometer data from MPU6050"""
    try:
        # Read accelerometer data
        acc_x = read_raw_data(ACCEL_XOUT_H)
        acc_y = read_raw_data(ACCEL_YOUT_H)
        acc_z = read_raw_data(ACCEL_ZOUT_H)
        
        # Convert to meaningful units
        # Accelerometer: ±2g scale, 16384 LSB/g
        ax = acc_x / 16384.0
        ay = acc_y / 16384.0
        az = acc_z / 16384.0
        
        return ax, ay, az, acc_x, acc_y, acc_z
    except Exception as e:
        print(f"❌ Error reading MPU6050 data: {e}")
        return 0, 0, 0, 0, 0, 0

def calculate_angles(ax, ay, az):
    """Calculate pitch and roll angles from accelerometer data"""
    try:
        # Calculate pitch (rotation around Y-axis)
        pitch = math.atan2(ax, math.sqrt(ay*ay + az*az)) * 180 / math.pi
        
        # Calculate roll (rotation around X-axis)  
        roll = math.atan2(ay, math.sqrt(ax*ax + az*az)) * 180 / math.pi
        
        return pitch, roll
    except Exception as e:
        print(f"❌ Error calculating angles: {e}")
        return 0, 0

print("🔍 MPU6050 Sensor Test")
print("=" * 50)

# Initialize sensor
if not init_mpu6050():
    print("❌ Failed to initialize MPU6050. Check connections:")
    print("   - VCC -> 3.3V (not 5V!)")
    print("   - GND -> GND")
    print("   - SDA -> GPIO 2 (Pin 3)")
    print("   - SCL -> GPIO 3 (Pin 5)")
    exit(1)

print("\n📊 Testing sensor readings...")
print("Tilt the sensor to see pitch and roll changes")
print("Press Ctrl+C to stop")
print()

try:
    for i in range(200):  # Run for about 20 seconds
        ax, ay, az, raw_x, raw_y, raw_z = get_mpu6050_data()
        
        if ax == 0 and ay == 0 and az == 0:
            print("❌ No data from sensor - check connections")
            break
            
        pitch, roll = calculate_angles(ax, ay, az)
        
        # Print formatted output
        print(f"Sample {i+1:3d}: "
              f"Accel(g): X={ax:6.2f} Y={ay:6.2f} Z={az:6.2f} | "
              f"Angles: Pitch={pitch:6.1f}° Roll={roll:6.1f}° | "
              f"Raw: {raw_x:6d} {raw_y:6d} {raw_z:6d}")
        
        time.sleep(0.1)  # 10 Hz update rate

except KeyboardInterrupt:
    print("\n⏹️ Test stopped by user")

print("\n✅ MPU6050 test complete")
print("\n📋 Understanding the readings:")
print("   - Pitch: Forward/backward tilt (+ = forward, - = backward)")
print("   - Roll: Left/right tilt (+ = left side down, - = right side down)")
print("   - If readings are stable, sensor is working correctly")
print("   - If readings are noisy or zero, check connections")
