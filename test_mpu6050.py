#!/usr/bin/env python3
"""
MPU-6050 Test Script
Tests the MPU-6050 accelerometer and gyroscope functionality with detailed diagnostics
"""
import time
import math
import json
import signal
import sys
import os

try:
    from mpu6050 import mpu6050
    print("✅ MPU6050 library imported successfully")
except ImportError as e:
    print("❌ Error importing MPU6050 library:")
    print(f"   {e}")
    print("   Install with: pip install mpu6050-raspberrypi")
    sys.exit(1)

# MPU-6050 configuration
MPU_ADDRESS = 0x68

def initialize_mpu():
    """Initialize MPU-6050 sensor"""
    try:
        sensor = mpu6050(MPU_ADDRESS)
        print(f"✅ MPU-6050 initialized at address 0x{MPU_ADDRESS:02X}")
        return sensor
    except Exception as e:
        print(f"❌ Error initializing MPU-6050: {e}")
        print("   Check I2C connections and address")
        return None

def load_calibration():
    """Load calibration data if available"""
    calib_file = "mpu6050_calibration.json"
    
    if os.path.exists(calib_file):
        try:
            with open(calib_file, 'r') as f:
                calibration = json.load(f)
            print("✅ Calibration data loaded from file")
            return calibration
        except Exception as e:
            print(f"⚠️  Error loading calibration: {e}")
    else:
        print("⚠️  No calibration file found")
    
    # Default calibration (no bias correction)
    return {
        'accel_bias': {'x': 0, 'y': 0, 'z': 0},
        'gyro_bias': {'x': 0, 'y': 0, 'z': 0}
    }

def test_basic_reading(sensor, calibration):
    """Test basic sensor readings"""
    print("\n📊 BASIC SENSOR READINGS")
    print("-" * 40)
    
    try:
        # Get raw data
        accel_data = sensor.get_accel_data()
        gyro_data = sensor.get_gyro_data()
        temp = sensor.get_temp()
        
        print("🌡️  Temperature:")
        print(f"   {temp:.2f}°C")
        
        print("\n📈 Raw Accelerometer (m/s²):")
        print(f"   X: {accel_data['x']:+8.4f}")
        print(f"   Y: {accel_data['y']:+8.4f}")
        print(f"   Z: {accel_data['z']:+8.4f}")
        
        print("\n🔄 Raw Gyroscope (°/s):")
        print(f"   X: {gyro_data['x']:+8.4f}")
        print(f"   Y: {gyro_data['y']:+8.4f}")
        print(f"   Z: {gyro_data['z']:+8.4f}")
        
        # Apply calibration if available
        accel_bias = calibration['accel_bias']
        gyro_bias = calibration['gyro_bias']
        
        if any(accel_bias.values()) or any(gyro_bias.values()):
            print("\n🎯 Calibrated Readings:")
            print("   Accelerometer (m/s²):")
            print(f"     X: {accel_data['x'] - accel_bias['x']:+8.4f}")
            print(f"     Y: {accel_data['y'] - accel_bias['y']:+8.4f}")
            print(f"     Z: {accel_data['z'] - accel_bias['z']:+8.4f}")
            
            print("   Gyroscope (°/s):")
            print(f"     X: {gyro_data['x'] - gyro_bias['x']:+8.4f}")
            print(f"     Y: {gyro_data['y'] - gyro_bias['y']:+8.4f}")
            print(f"     Z: {gyro_data['z'] - gyro_bias['z']:+8.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading sensor data: {e}")
        return False

def test_orientation(sensor, calibration):
    """Test orientation calculation"""
    print("\n🧭 ORIENTATION CALCULATION")
    print("-" * 40)
    
    try:
        accel_data = sensor.get_accel_data()
        accel_bias = calibration['accel_bias']
        
        # Apply calibration
        accel_x = accel_data['x'] - accel_bias['x']
        accel_y = accel_data['y'] - accel_bias['y']
        accel_z = accel_data['z'] - accel_bias['z']
        
        # Calculate pitch and roll from accelerometer
        pitch = math.atan2(accel_y, math.sqrt(accel_x**2 + accel_z**2)) * 180 / math.pi
        roll = math.atan2(-accel_x, accel_z) * 180 / math.pi
        
        # Calculate magnitude
        magnitude = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
        
        print(f"📐 Pitch: {pitch:+7.2f}°")
        print(f"📐 Roll:  {roll:+7.2f}°")
        print(f"📏 Acceleration magnitude: {magnitude:.4f} m/s²")
        print(f"🌍 Expected gravity: ~9.81 m/s²")
        
        # Orientation status
        if abs(pitch) < 5 and abs(roll) < 5:
            status = "✅ Level"
        elif abs(pitch) > 45 or abs(roll) > 45:
            status = "🔴 Steep angle"
        else:
            status = "🟡 Tilted"
        
        print(f"📊 Status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error calculating orientation: {e}")
        return False

def test_motion_detection(sensor, calibration):
    """Test motion detection"""
    print("\n🏃 MOTION DETECTION TEST")
    print("-" * 40)
    print("Move the sensor to test motion detection...")
    print("Press Ctrl+C to stop")
    
    try:
        gyro_bias = calibration['gyro_bias']
        motion_threshold = 10  # degrees/second
        samples = 0
        motion_count = 0
        
        while True:
            gyro_data = sensor.get_gyro_data()
            
            # Apply calibration
            gyro_x = gyro_data['x'] - gyro_bias['x']
            gyro_y = gyro_data['y'] - gyro_bias['y']
            gyro_z = gyro_data['z'] - gyro_bias['z']
            
            # Calculate total angular velocity
            total_rotation = math.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)
            
            samples += 1
            
            if total_rotation > motion_threshold:
                motion_count += 1
                status = "🟢 MOTION DETECTED"
            else:
                status = "⚪ Still"
            
            print(f"Sample #{samples}: {total_rotation:6.2f}°/s | {status}")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        motion_percentage = (motion_count / samples * 100) if samples > 0 else 0
        print(f"\n📊 Motion Detection Summary:")
        print(f"   Total samples: {samples}")
        print(f"   Motion detected: {motion_count} ({motion_percentage:.1f}%)")
        print(f"   Threshold: {motion_threshold}°/s")

def test_stability(sensor, calibration):
    """Test sensor stability over time"""
    print("\n📊 STABILITY TEST")
    print("-" * 40)
    print("Keep sensor still for stability test...")
    
    num_samples = 100
    accel_readings = {'x': [], 'y': [], 'z': []}
    gyro_readings = {'x': [], 'y': [], 'z': []}
    
    print(f"Collecting {num_samples} samples...")
    
    try:
        for i in range(num_samples):
            accel_data = sensor.get_accel_data()
            gyro_data = sensor.get_gyro_data()
            
            # Store readings
            for axis in ['x', 'y', 'z']:
                accel_readings[axis].append(accel_data[axis])
                gyro_readings[axis].append(gyro_data[axis])
            
            print(f"Progress: {i+1}/{num_samples}", end='\r')
            time.sleep(0.05)
        
        print("\n")
        
        # Calculate statistics
        print("📈 ACCELEROMETER STABILITY:")
        for axis in ['x', 'y', 'z']:
            values = accel_readings[axis]
            mean = sum(values) / len(values)
            variance = sum((x - mean)**2 for x in values) / len(values)
            std_dev = math.sqrt(variance)
            
            print(f"   {axis.upper()}: Mean={mean:+7.4f}, StdDev={std_dev:.6f} m/s²")
        
        print("\n🔄 GYROSCOPE STABILITY:")
        for axis in ['x', 'y', 'z']:
            values = gyro_readings[axis]
            mean = sum(values) / len(values)
            variance = sum((x - mean)**2 for x in values) / len(values)
            std_dev = math.sqrt(variance)
            
            print(f"   {axis.upper()}: Mean={mean:+7.4f}, StdDev={std_dev:.6f} °/s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during stability test: {e}")
        return False

def continuous_monitoring(sensor, calibration):
    """Continuous sensor monitoring"""
    print("\n📡 CONTINUOUS MONITORING")
    print("-" * 40)
    print("Real-time sensor monitoring - Press Ctrl+C to stop")
    print("Format: Pitch | Roll | Temp | Motion")
    print()
    
    try:
        accel_bias = calibration['accel_bias']
        gyro_bias = calibration['gyro_bias']
        
        while True:
            # Read sensor data
            accel_data = sensor.get_accel_data()
            gyro_data = sensor.get_gyro_data()
            temp = sensor.get_temp()
            
            # Apply calibration
            accel_x = accel_data['x'] - accel_bias['x']
            accel_y = accel_data['y'] - accel_bias['y']
            accel_z = accel_data['z'] - accel_bias['z']
            
            gyro_x = gyro_data['x'] - gyro_bias['x']
            gyro_y = gyro_data['y'] - gyro_bias['y']
            gyro_z = gyro_data['z'] - gyro_bias['z']
            
            # Calculate orientation
            pitch = math.atan2(accel_y, math.sqrt(accel_x**2 + accel_z**2)) * 180 / math.pi
            roll = math.atan2(-accel_x, accel_z) * 180 / math.pi
            
            # Calculate motion
            motion = math.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)
            
            # Motion status
            if motion > 20:
                motion_status = "🔴 HIGH"
            elif motion > 5:
                motion_status = "🟡 MED"
            else:
                motion_status = "🟢 LOW"
            
            print(f"P:{pitch:+6.1f}° | R:{roll:+6.1f}° | T:{temp:5.1f}°C | M:{motion:5.1f}°/s {motion_status}")
            
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\n📊 Monitoring stopped")

def main():
    """Main test function"""
    print("📱 MPU-6050 ACCELEROMETER/GYROSCOPE TEST SCRIPT")
    print("=" * 60)
    
    # Initialize sensor
    sensor = initialize_mpu()
    if not sensor:
        sys.exit(1)
    
    # Load calibration
    calibration = load_calibration()
    
    try:
        while True:
            print("\n🧪 TEST MENU:")
            print("1. Basic sensor readings")
            print("2. Orientation calculation")
            print("3. Motion detection")
            print("4. Stability test")
            print("5. Continuous monitoring")
            print("6. Quit")
            
            choice = input("\nSelect test (1-6): ").strip()
            
            if choice == '1':
                test_basic_reading(sensor, calibration)
                
            elif choice == '2':
                test_orientation(sensor, calibration)
                
            elif choice == '3':
                test_motion_detection(sensor, calibration)
                
            elif choice == '4':
                test_stability(sensor, calibration)
                
            elif choice == '5':
                continuous_monitoring(sensor, calibration)
                
            elif choice == '6':
                break
                
            else:
                print("❌ Invalid choice. Please select 1-6.")
                
            if choice != '5' and choice != '3':  # Skip for continuous tests
                input("\nPress Enter to continue...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n👋 Test script terminated by user")
    
    print("✅ Test complete")

if __name__ == "__main__":
    main()
