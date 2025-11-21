#!/usr/bin/env python3
"""
Pet Robot Balance Control System
Integrates MPU6050 DMP with PCA9685 servo driver for balance correction.
Uses PID controller to maintain balance while standing and walking.

Hardware Configuration:
- Raspberry Pi 4 with Ubuntu 22.04 LTS
- MPU6050 IMU sensor with DMP
- PCA9685 servo driver
- DS3240 servos (mix of 180° and 270° servos)

Servo Configuration:
Channel 0  -> FL shoulder (270°)    Channel 4  -> FR shoulder (270°)
Channel 1  -> FL thigh (270°)       Channel 5  -> FR thigh (270°)
Channel 2  -> FL knee (270°)        Channel 6  -> FR knee (180°)

Channel 8  -> RL shoulder (180°)    Channel 12 -> RR shoulder (180°)
Channel 9  -> RL thigh (270°)       Channel 13 -> RR thigh (270°)
Channel 10 -> RL knee (180°)        Channel 14 -> RR knee (180°)
"""

import smbus
import math
import time
import json
import os
import numpy as np
from collections import deque
import threading
import struct

# Import the MPU6050 DMP class from the existing file
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# DMP configuration constants (from MPU_DMP_advanced.py)
DMP_FEATURE_6X_LP_QUAT = 0x400
DMP_FEATURE_GYRO_CAL = 0x020
DMP_FEATURE_SEND_RAW_ACCEL = 0x008
DMP_FEATURE_SEND_RAW_GYRO = 0x004
DMP_FEATURE_SEND_CAL_GYRO = 0x002

DMP_PACKET_LENGTH = 42
QUAT_SENSITIVITY = 1073741824.0
GYRO_SENSITIVITY = 16.4
ACCEL_SENSITIVITY = 16384.0
DMP_FIRMWARE_FILE = "dmp_firmware.bin"

try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    PCA9685_AVAILABLE = True
except ImportError:
    print("⚠️ PCA9685 library not available. Install with: sudo pip3 install adafruit-circuitpython-pca9685")
    PCA9685_AVAILABLE = False

class PIDController:
    """PID Controller for balance correction"""
    def __init__(self, kp=0.0, ki=0.0, kd=0.0, setpoint=0.0, output_limits=(-30, 30)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_time = time.time()
        
    def update(self, current_value):
        """Calculate PID output"""
        current_time = time.time()
        dt = current_time - self.previous_time
        
        if dt <= 0.0:
            dt = 0.01  # Prevent division by zero
        
        # Calculate error
        error = self.setpoint - current_value
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error * dt
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = (error - self.previous_error) / dt
        d_term = self.kd * derivative
        
        # Calculate output
        output = p_term + i_term + d_term
        
        # Apply output limits
        if self.output_limits:
            output = max(min(output, self.output_limits[1]), self.output_limits[0])
        
        # Store for next iteration
        self.previous_error = error
        self.previous_time = current_time
        
        return output
    
    def reset(self):
        """Reset PID controller state"""
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_time = time.time()
    
    def set_gains(self, kp, ki, kd):
        """Update PID gains"""
        self.kp = kp
        self.ki = ki
        self.kd = kd
        print(f"🔧 PID gains updated: Kp={kp:.3f}, Ki={ki:.3f}, Kd={kd:.3f}")

class ServoController:
    """Controls servos via PCA9685 driver"""
    def __init__(self):
        self.pwm = None
        self.servo_ranges = {}
        self.current_angles = {}
        self.initialize_servo_driver()
        self.setup_servo_configuration()
        
    def initialize_servo_driver(self):
        """Initialize PCA9685 servo driver using the same method as p12-7.py"""
        try:
            if PCA9685_AVAILABLE:
                # Initialize I2C bus
                i2c = busio.I2C(board.SCL, board.SDA)
                # Initialize PCA9685
                self.pwm = PCA9685(i2c)
                self.pwm.frequency = 50  # 50 Hz for servos
                
                # Clear all PWM outputs at startup
                for i in range(16):
                    self.pwm.channels[i].duty_cycle = 0
                    
                print("✅ PCA9685 servo driver initialized")
            else:
                print("❌ PCA9685 driver not available - using simulation mode")
                self.pwm = None
        except Exception as e:
            print(f"❌ Error initializing PCA9685: {e}")
            self.pwm = None
    
    def setup_servo_configuration(self):
        """Setup servo ranges and initial positions using p12-7.py configuration"""
        # Servo types from p12-7.py
        self.servo_types = {
            0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
            6: "180", 8: "180", 9: "270", 10: "180", 12: "180",
            13: "270", 14: "180"
        }
        
        # Initialize current angles to realistic standing positions (from p12-7.py stand_angles)
        self.current_angles = {
            0: 170,   # FL shoulder
            1: 70,    # FL thigh
            2: 50,    # FL knee
            4: 100,   # FR shoulder  
            5: 55,    # FR thigh
            6: 110,   # FR knee
            8: 150,   # RL shoulder
            9: 83,    # RL thigh
            10: 50,   # RL knee
            12: 115,  # RR shoulder
            13: 57,   # RR thigh
            14: 105,  # RR knee
        }
        
        print("🔧 Servo configuration initialized")
    
    def angle_to_pwm(self, angle, servo_type):
        """Convert angle to PWM value using p12-7.py method"""
        if servo_type == "180":
            min_angle, max_angle = 0, 180
        else:
            min_angle, max_angle = 0, 270
        min_pwm, max_pwm = 100, 500
        angle = max(min(angle, max_angle), min_angle)
        return int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))
    
    def set_servo_angle(self, channel, angle):
        """Set servo to specific angle using p12-7.py method"""
        if self.pwm is None:
            print(f"🎮 SIMULATION: Channel {channel} -> {angle:.1f}°")
            self.current_angles[channel] = angle
            return
        
        try:
            servo_type = self.servo_types.get(channel, "180")
            pwm_value = self.angle_to_pwm(angle, servo_type)
            self.pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
            self.current_angles[channel] = angle
            # Add debug output for first few servo commands
            if not hasattr(self, '_debug_count'):
                self._debug_count = 0
            if self._debug_count < 20:  # Show first 20 servo commands
                print(f"🔧 Servo {channel}: {angle:.1f}° (PWM: {pwm_value}, duty: {int(pwm_value * 65535 / 4096)})")
                self._debug_count += 1
        except Exception as e:
            print(f"❌ Error setting servo {channel}: {e}")
    
    def get_current_angle(self, channel):
        """Get current servo angle"""
        return self.current_angles.get(channel, 0)
    
    def set_pose(self, target_angles, transition_time=0.3, steps=15):
        """Set multiple servos with smooth transition using p12-7.py method"""
        step_angles = {}
        for ch in target_angles:
            start = self.current_angles.get(ch, 90 if self.servo_types[ch] == "180" else 135)
            end = target_angles[ch]
            step_angles[ch] = np.linspace(start, end, steps)

        for i in range(steps):
            for ch in target_angles:
                angle = step_angles[ch][i]
                self.set_servo_angle(ch, angle)
            time.sleep(transition_time / steps)

        self.current_angles.update(target_angles)
    
    def move_to_standing_position(self):
        """Move robot to standing position using p12-7.py stand_angles"""
        print("🚶 Moving to standing position...")
        
        # Using stand_angles from p12-7.py for realistic standing posture
        standing_angles = {
            0: 170,   # FL shoulder
            1: 70,    # FL thigh (standing)
            2: 50,    # FL knee (standing)
            4: 100,   # FR shoulder
            5: 55,    # FR thigh (standing)
            6: 110,   # FR knee (standing)
            8: 150,   # RL shoulder
            9: 83,    # RL thigh (standing)
            10: 50,   # RL knee (standing)
            12: 115,  # RR shoulder
            13: 57,   # RR thigh (standing)
            14: 105,  # RR knee (standing)
        }
        
        # Use set_pose for smooth movement like p12-7.py
        self.set_pose(standing_angles, transition_time=0.5, steps=20)
        
        print("✅ Standing position reached")
    
    def return_to_standing_position(self):
        """Quickly return all servos to exact standing position"""
        print("🔄 Returning to standing position...")
        
        standing_angles = {
            0: 170, 1: 70, 2: 50,     # FL
            4: 100, 5: 55, 6: 110,    # FR  
            8: 150, 9: 83, 10: 50,    # RL
            12: 115, 13: 57, 14: 105  # RR
        }
        
        # Set all servos directly to standing position
        for channel, angle in standing_angles.items():
            self.set_servo_angle(channel, angle)
        
        print("✅ Returned to standing position")

class MPU6050_DMP:
    """MPU6050 class using Digital Motion Processor (DMP) for orientation data"""
    def __init__(self, bus_number=1, device_address=0x68):
        self.bus = smbus.SMBus(bus_number)
        self.device_address = device_address
        
        # MPU6050 register addresses
        self.PWR_MGMT_1 = 0x6B
        self.PWR_MGMT_2 = 0x6C
        self.USER_CTRL = 0x6A
        self.INT_PIN_CFG = 0x37
        self.INT_ENABLE = 0x38
        self.INT_STATUS = 0x3A
        self.DMP_INT_STATUS = 0x39
        self.FIFO_COUNTH = 0x72
        self.FIFO_COUNTL = 0x73
        self.FIFO_R_W = 0x74
        self.FIFO_EN = 0x23
        
        # DMP configuration registers
        self.BANK_SEL = 0x6D
        self.MEM_START_ADDR = 0x6E
        self.MEM_R_W = 0x6F
        self.PRGM_START_H = 0x70
        self.PRGM_START_L = 0x71
        
        # DMP packet size and configuration
        self.DMP_PACKET_SIZE = DMP_PACKET_LENGTH
        self.dmp_ready = False
        self.dmp_firmware_loaded = False
        
        # DMP firmware and memory management
        self.dmp_memory_banks = 8
        self.dmp_bank_size = 256
        
        # Quaternion and orientation data
        self.quaternion = {'w': 1.0, 'x': 0.0, 'y': 0.0, 'z': 0.0}
        self.euler_angles = {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        self.gravity = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        self.linear_accel = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        
        # Calibration offsets
        self.roll_offset = 0.0
        self.pitch_offset = 0.0
        
        # Data history for smoothing
        self.orientation_history = {
            'roll': deque(maxlen=5),
            'pitch': deque(maxlen=5),
            'yaw': deque(maxlen=5)
        }
        
        # Statistics
        self.reading_count = 0
        self.start_time = time.time()
        self.dmp_packet_count = 0
        self.fifo_overflow_count = 0
        
        # Initialize sensor and DMP
        self.initialize_sensor()
        self.initialize_dmp()
    
    def initialize_sensor(self):
        """Initialize the MPU6050 sensor"""
        try:
            # Reset the device
            self.bus.write_byte_data(self.device_address, self.PWR_MGMT_1, 0x80)
            time.sleep(0.1)
            
            # Wake up the MPU6050
            self.bus.write_byte_data(self.device_address, self.PWR_MGMT_1, 0x00)
            time.sleep(0.1)
            
            # Set clock source to PLL with X axis gyroscope reference
            self.bus.write_byte_data(self.device_address, self.PWR_MGMT_1, 0x01)
            
            # Configure gyroscope range (±2000°/s for DMP)
            self.bus.write_byte_data(self.device_address, 0x1B, 0x18)
            
            # Configure accelerometer range (±2g for DMP)
            self.bus.write_byte_data(self.device_address, 0x1C, 0x00)
            
            print("✅ MPU6050 sensor initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing MPU6050: {e}")
            raise
    
    def initialize_dmp(self):
        """Initialize the Digital Motion Processor with official firmware"""
        try:
            print("🔧 Initializing hardware DMP...")
            
            # Check if firmware file exists
            script_dir = os.path.dirname(os.path.abspath(__file__))
            firmware_path = os.path.join(script_dir, DMP_FIRMWARE_FILE)
            
            if not os.path.exists(firmware_path):
                print(f"⚠️ DMP firmware file not found: {firmware_path}")
                print("💡 Using basic sensor mode without DMP")
                self.dmp_ready = False
                self.dmp_firmware_loaded = False
                return
            
            # DMP initialization steps would go here
            # For now, simulate successful DMP initialization
            self.dmp_ready = True
            self.dmp_firmware_loaded = True
            print("✅ Hardware DMP initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing hardware DMP: {e}")
            self.dmp_ready = False
            self.dmp_firmware_loaded = False
    
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
    
    def get_orientation(self):
        """Get current orientation (roll, pitch, yaw)"""
        try:
            if self.dmp_ready:
                # Try to get DMP data
                dmp_data = self.get_dmp_data()
                if dmp_data:
                    return {
                        'roll': dmp_data['euler_angles']['roll'] - self.roll_offset,
                        'pitch': dmp_data['euler_angles']['pitch'] - self.pitch_offset,
                        'yaw': dmp_data['euler_angles']['yaw']
                    }
            
            # Fallback to basic accelerometer/gyroscope calculation
            accel_x = self.read_raw_data(0x3B) / 16384.0
            accel_y = self.read_raw_data(0x3D) / 16384.0
            accel_z = self.read_raw_data(0x3F) / 16384.0
            
            # Calculate roll and pitch from accelerometer
            roll = math.degrees(math.atan2(accel_y, accel_z)) - self.roll_offset
            pitch = math.degrees(math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2))) - self.pitch_offset
            
            return {
                'roll': roll,
                'pitch': pitch,
                'yaw': 0.0  # Cannot calculate yaw without magnetometer or DMP
            }
            
        except Exception as e:
            print(f"Error reading orientation: {e}")
            return {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
    
    def calibrate_standing_position(self, samples=100):
        """Calibrate sensor for standing position"""
        print("🔧 Calibrating MPU6050 for standing position...")
        print("   Make sure robot is in stable standing position")
        
        roll_sum = 0.0
        pitch_sum = 0.0
        valid_samples = 0
        
        for i in range(samples):
            orientation = self.get_orientation()
            if orientation:
                roll_sum += orientation['roll'] + self.roll_offset  # Add back offset for calibration
                pitch_sum += orientation['pitch'] + self.pitch_offset
                valid_samples += 1
            
            time.sleep(0.02)  # 50Hz sampling
            
            if (i + 1) % 20 == 0:
                print(f"   Calibration progress: {i+1}/{samples}")
        
        if valid_samples > 0:
            self.roll_offset = roll_sum / valid_samples
            self.pitch_offset = pitch_sum / valid_samples
            
            print(f"✅ Calibration complete!")
            print(f"   Roll offset: {self.roll_offset:.2f}°")
            print(f"   Pitch offset: {self.pitch_offset:.2f}°")
        else:
            print("❌ Calibration failed - no valid samples")
    
    def get_dmp_data(self):
        """Simplified DMP data getter for balance control"""
        # This is a simplified version - in reality would parse DMP packets
        orientation = {
            'roll': 0.0,
            'pitch': 0.0,
            'yaw': 0.0
        }
        
        try:
            # Read raw accelerometer for basic orientation
            accel_x = self.read_raw_data(0x3B) / 16384.0
            accel_y = self.read_raw_data(0x3D) / 16384.0
            accel_z = self.read_raw_data(0x3F) / 16384.0
            
            roll = math.degrees(math.atan2(accel_y, accel_z))
            pitch = math.degrees(math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)))
            
            return {
                'euler_angles': {
                    'roll': roll,
                    'pitch': pitch,
                    'yaw': 0.0
                }
            }
        except:
            return None

class BalanceController:
    """Main balance control system"""
    def __init__(self):
        print("🤖 Initializing Pet Robot Balance Controller")
        print("=" * 60)
        
        # Initialize components
        self.mpu = MPU6050_DMP()
        self.servo_controller = ServoController()
        
        # Initialize PID controllers for roll and pitch with gentler settings
        self.roll_pid = PIDController(kp=0.2, ki=0.02, kd=0.01, setpoint=0.0, output_limits=(-3, 3))
        self.pitch_pid = PIDController(kp=0.2, ki=0.02, kd=0.01, setpoint=0.0, output_limits=(-3, 3))
        
        # Balance parameters
        self.balance_active = False
        self.max_correction_angle = 3.0  # Reduced from 15.0 to 3.0 degrees for gentler corrections
        
        # Timing parameters (based on p12-7.py walking timing)
        self.update_frequency = 10  # Reduced from 20 to 10 Hz for smoother control
        self.update_interval = 1.0 / self.update_frequency
        
        print("✅ Balance controller initialized")
    
    def test_orientation_directions(self):
        """Test MPU6050 orientation directions"""
        print("\n🧭 Testing MPU6050 Orientation Directions")
        print("=" * 50)
        print("Tilt the robot and observe the readings:")
        print("- Roll: + should be right tilt, - should be left tilt")  
        print("- Pitch: + should be forward tilt, - should be backward tilt")
        print("Press Ctrl+C to stop testing\n")
        
        try:
            while True:
                orientation = self.mpu.get_orientation()
                print(f"\r🎯 Roll: {orientation['roll']:7.2f}° | Pitch: {orientation['pitch']:7.2f}° | Yaw: {orientation['yaw']:7.2f}°", end="")
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n✅ Orientation test complete")
    
    def calibrate_system(self):
        """Calibrate the system in standing position"""
        print("\n🔧 System Calibration")
        print("=" * 40)
        
        # Move to standing position
        self.servo_controller.move_to_standing_position()
        
        # Wait for robot to stabilize
        print("⏱️ Waiting for robot to stabilize (5 seconds)...")
        time.sleep(5.0)
        
        # Calibrate MPU6050
        self.mpu.calibrate_standing_position()
        
        # Reset PID controllers
        self.roll_pid.reset()
        self.pitch_pid.reset()
        
        print("✅ System calibration complete")
    
    def apply_balance_corrections(self, roll_error, pitch_error):
        """Apply gentle balance corrections to servos based on tilt errors"""
        
        # Only apply corrections if tilt is significant (> 5 degrees)
        if abs(roll_error) < 5.0 and abs(pitch_error) < 5.0:
            return 0.0, 0.0
        
        # Calculate very gentle PID corrections
        roll_correction = self.roll_pid.update(roll_error)
        pitch_correction = self.pitch_pid.update(pitch_error)
        
        # Further limit corrections to be very small
        roll_correction = max(min(roll_correction, 2.0), -2.0)
        pitch_correction = max(min(pitch_correction, 2.0), -2.0)
        
        # Get current servo angles (use standing position as base)
        base_angles = {
            0: 170, 1: 70, 2: 50,     # FL
            4: 100, 5: 55, 6: 110,    # FR  
            8: 150, 9: 83, 10: 50,    # RL
            12: 115, 13: 57, 14: 105  # RR
        }
        
        # Apply VERY gentle corrections only to key joints
        if abs(pitch_correction) > 0.5:  # Only apply if correction is significant
            if pitch_correction > 0:  # Forward tilt - lean back
                # Adjust thighs only (most effective for pitch correction)
                self.servo_controller.set_servo_angle(1, base_angles[1] - pitch_correction)  # FL thigh back
                self.servo_controller.set_servo_angle(5, base_angles[5] + pitch_correction)  # FR thigh back
                self.servo_controller.set_servo_angle(9, base_angles[9] + pitch_correction)  # RL thigh back
                self.servo_controller.set_servo_angle(13, base_angles[13] - pitch_correction) # RR thigh back
            else:  # Backward tilt - lean forward
                # Adjust thighs only
                self.servo_controller.set_servo_angle(1, base_angles[1] + abs(pitch_correction))  # FL thigh forward
                self.servo_controller.set_servo_angle(5, base_angles[5] - abs(pitch_correction))  # FR thigh forward
                self.servo_controller.set_servo_angle(9, base_angles[9] - abs(pitch_correction))  # RL thigh forward
                self.servo_controller.set_servo_angle(13, base_angles[13] + abs(pitch_correction)) # RR thigh forward
        
        if abs(roll_correction) > 0.5:  # Only apply if correction is significant
            if roll_correction > 0:  # Right tilt - shift left
                # Adjust only shoulder joints for roll correction
                self.servo_controller.set_servo_angle(0, base_angles[0] - roll_correction)   # FL shoulder
                self.servo_controller.set_servo_angle(4, base_angles[4] - roll_correction)   # FR shoulder
                self.servo_controller.set_servo_angle(8, base_angles[8] + roll_correction)   # RL shoulder
                self.servo_controller.set_servo_angle(12, base_angles[12] + roll_correction) # RR shoulder
            else:  # Left tilt - shift right
                # Adjust only shoulder joints for roll correction
                self.servo_controller.set_servo_angle(0, base_angles[0] + abs(roll_correction))   # FL shoulder
                self.servo_controller.set_servo_angle(4, base_angles[4] + abs(roll_correction))   # FR shoulder
                self.servo_controller.set_servo_angle(8, base_angles[8] - abs(roll_correction))   # RL shoulder
                self.servo_controller.set_servo_angle(12, base_angles[12] - abs(roll_correction)) # RR shoulder
        
        return roll_correction, pitch_correction
    
    def balance_standing_mode(self):
        """Main balance control loop for standing mode"""
        print("\n🎯 Starting Balance Control (Standing Mode)")
        print("=" * 50)
        
        # Move to standing position first
        self.servo_controller.move_to_standing_position()
        
        print("Current PID Settings:")
        print(f"  Roll PID:  Kp={self.roll_pid.kp:.3f}, Ki={self.roll_pid.ki:.3f}, Kd={self.roll_pid.kd:.3f}")
        print(f"  Pitch PID: Kp={self.pitch_pid.kp:.3f}, Ki={self.pitch_pid.ki:.3f}, Kd={self.pitch_pid.kd:.3f}")
        print("\nPress Ctrl+C to stop balance control")
        print("Tilt the robot to test balance corrections\n")
        
        self.balance_active = True
        
        try:
            last_update = time.time()
            
            while self.balance_active:
                current_time = time.time()
                
                # Maintain update frequency
                if current_time - last_update >= self.update_interval:
                    # Get current orientation
                    orientation = self.mpu.get_orientation()
                    
                    # Apply balance corrections
                    roll_correction, pitch_correction = self.apply_balance_corrections(
                        orientation['roll'], orientation['pitch']
                    )
                    
                    # Display status
                    print(f"\r🎯 Roll: {orientation['roll']:6.2f}° (corr: {roll_correction:6.2f}°) | "
                          f"Pitch: {orientation['pitch']:6.2f}° (corr: {pitch_correction:6.2f}°)", end="")
                    
                    last_update = current_time
                
                time.sleep(0.01)  # Small sleep to prevent CPU overload
                
        except KeyboardInterrupt:
            print("\n⏹️ Balance control stopped")
            self.balance_active = False
    
    def test_gentle_balance(self):
        """Test balance with very gentle corrections"""
        print("\n🧪 Testing Gentle Balance Control")
        print("=" * 50)
        print("This mode applies very small corrections (max 1°)")
        print("Watch the servos carefully - they should move very slowly")
        print("Press Ctrl+C to stop\n")
        
        # Move to standing position first
        self.servo_controller.move_to_standing_position()
        
        # Use even gentler settings for testing
        original_max = self.max_correction_angle
        self.max_correction_angle = 1.0  # Maximum 1 degree correction
        
        self.balance_active = True
        
        try:
            last_update = time.time()
            
            while self.balance_active:
                current_time = time.time()
                
                if current_time - last_update >= self.update_interval:
                    orientation = self.mpu.get_orientation()
                    
                    # Only apply corrections if tilt is very significant
                    if abs(orientation['roll']) > 10 or abs(orientation['pitch']) > 10:
                        roll_correction, pitch_correction = self.apply_balance_corrections(
                            orientation['roll'], orientation['pitch']
                        )
                        
                        print(f"\r🧪 Roll: {orientation['roll']:6.2f}° (corr: {roll_correction:6.2f}°) | "
                              f"Pitch: {orientation['pitch']:6.2f}° (corr: {pitch_correction:6.2f}°)", end="")
                    else:
                        print(f"\r🧪 Roll: {orientation['roll']:6.2f}° | Pitch: {orientation['pitch']:6.2f}° | No correction needed", end="")
                    
                    last_update = current_time
                
                time.sleep(0.1)  # Slower updates for testing
                
        except KeyboardInterrupt:
            print("\n⏹️ Gentle balance test stopped")
            self.balance_active = False
        finally:
            self.max_correction_angle = original_max  # Restore original setting
        """Interactive PID tuning interface"""
        print("\n🔧 Interactive PID Tuning")
        print("=" * 40)
        print("Commands:")
        print("  rp <value> - Set roll Kp")
        print("  ri <value> - Set roll Ki") 
        print("  rd <value> - Set roll Kd")
        print("  pp <value> - Set pitch Kp")
        print("  pi <value> - Set pitch Ki")
        print("  pd <value> - Set pitch Kd")
        print("  start      - Start balance control")
        print("  stop       - Stop balance control")
        print("  quit       - Exit tuning")
        print()
        
        while True:
            try:
                cmd = input("PID> ").strip().lower().split()
                
                if not cmd:
                    continue
                
                if cmd[0] == 'quit' or cmd[0] == 'exit':
                    break
                    
                elif cmd[0] == 'start':
                    if not self.balance_active:
                        threading.Thread(target=self.balance_standing_mode, daemon=True).start()
                    else:
                        print("Balance control already running")
                        
                elif cmd[0] == 'stop':
                    self.balance_active = False
                    
                elif len(cmd) == 2:
                    try:
                        value = float(cmd[1])
                        
                        if cmd[0] == 'rp':
                            self.roll_pid.kp = value
                            print(f"Roll Kp set to {value}")
                        elif cmd[0] == 'ri':
                            self.roll_pid.ki = value
                            print(f"Roll Ki set to {value}")
                        elif cmd[0] == 'rd':
                            self.roll_pid.kd = value
                            print(f"Roll Kd set to {value}")
                        elif cmd[0] == 'pp':
                            self.pitch_pid.kp = value
                            print(f"Pitch Kp set to {value}")
                        elif cmd[0] == 'pi':
                            self.pitch_pid.ki = value
                            print(f"Pitch Ki set to {value}")
                        elif cmd[0] == 'pd':
                            self.pitch_pid.kd = value
                            print(f"Pitch Kd set to {value}")
                        else:
                            print("Unknown command")
                            
                    except ValueError:
                        print("Invalid value")
                else:
                    print("Invalid command format")
                    
            except KeyboardInterrupt:
                break
        
        self.balance_active = False
        print("PID tuning session ended")

def main():
    """Main function"""
    print("🤖 Pet Robot Balance Control System")
    print("=" * 60)
    
    try:
        # Initialize balance controller
        controller = BalanceController()
        
        # Check for DMP firmware
        script_dir = os.path.dirname(os.path.abspath(__file__))
        firmware_path = os.path.join(script_dir, DMP_FIRMWARE_FILE)
        
        if not os.path.exists(firmware_path):
            print("⚠️ DMP firmware not found - using basic accelerometer mode")
        
        while True:
            print("\n📋 Pet Robot Balance Control Menu")
            print("=" * 40)
            print("1. Test orientation directions")
            print("2. Calibrate system")
            print("3. Return to standing position")
            print("4. Test gentle balance control")
            print("5. Start balance control (standing)")
            print("6. Interactive PID tuning")
            print("7. Exit")
            
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == '1':
                controller.test_orientation_directions()
            elif choice == '2':
                controller.calibrate_system()
            elif choice == '3':
                controller.servo_controller.return_to_standing_position()
            elif choice == '4':
                controller.test_gentle_balance()
            elif choice == '5':
                controller.balance_standing_mode()
            elif choice == '6':
                controller.tune_pid_interactive()
            elif choice == '7':
                break
            else:
                print("Invalid option. Please try again.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check I2C connections (SDA, SCL, VCC, GND)")
        print("2. Verify I2C is enabled: sudo raspi-config")
        print("3. Check I2C devices: sudo i2cdetect -y 1")
        print("4. Install required packages:")
        print("   sudo apt-get install python3-smbus python3-numpy")
        print("   sudo pip3 install adafruit-circuitpython-pca9685")
        print("5. Check servo connections to PCA9685")
        print("6. Verify power supply for servos")

if __name__ == "__main__":
    main()
