#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685
import time
import numpy as np
import RPi.GPIO as GPIO
import json
import os
import threading

# MPU6050 imports
try:
    import adafruit_mpu6050
    MPU6050_AVAILABLE = True
except ImportError:
    print("Warning: adafruit_mpu6050 not available. Install with: pip install adafruit-circuitpython-mpu6050")
    MPU6050_AVAILABLE = False

# Initialize I2C bus
try:
    i2c = busio.I2C(board.SCL, board.SDA)
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit(1)

# Initialize PCA9685
try:
    pwm = PCA9685(i2c)
    pwm.frequency = 50  # 50 Hz for servos
except Exception as e:
    print(f"Error initializing PCA9685: {e}")
    exit(1)

# Initialize MPU6050
mpu = None
if MPU6050_AVAILABLE:
    try:
        mpu = adafruit_mpu6050.MPU6050(i2c)
        print("MPU6050 sensor initialized successfully")
    except Exception as e:
        print(f"Error initializing MPU6050: {e}")
        print("Balance control will be disabled")
        mpu = None
else:
    print("MPU6050 library not available. Balance control disabled.")

# Clear all PWM outputs at startup
for i in range(16):
    pwm.channels[i].duty_cycle = 0

# Ultrasonic sensor configuration
TRIG = 23  # GPIO23
ECHO = 24  # GPIO24

def setup_ultrasonic():
    """Initialize GPIO pins for ultrasonic sensor"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("Ultrasonic sensor initialized")

def get_distance():
    """
    Get distance measurement from HC-SR04 sensor
    Returns distance in centimeters, -1 if timeout
    """
    # Send 10us pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIG, False)
    
    # Wait for echo to start
    pulse_start = time.time()
    timeout_start = pulse_start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        # Timeout protection (max ~0.1 second for faster response)
        if pulse_start - timeout_start > 0.1:
            return -1  # Timeout error
    
    # Wait for echo to end
    pulse_end = time.time()
    timeout_start = pulse_end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        # Timeout protection (max ~0.1 second for faster response)
        if pulse_end - timeout_start > 0.1:
            return -1  # Timeout error
    
    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound = 343m/s, divide by 2 for round trip
    distance = round(distance, 2)
    
    return distance

def check_obstacle():
    """
    Check if there's an obstacle within 30cm
    Returns True if obstacle detected, False otherwise
    """
    distance = get_distance()
    if distance == -1:  # Sensor timeout
        return False  # Assume no obstacle if sensor fails
    return distance <= 30  # Return True if obstacle within 30cm

# ============================================================================
# BALANCE CONTROL SYSTEM WITH CONTINUOUS MONITORING
# ============================================================================

# PID Controller Parameters - EDIT THESE VALUES TO TUNE THE BALANCE CONTROL
# Start with all values at 0 and gradually increase
PITCH_PID_PARAMS = {
    'kp': 0.8,  # Proportional gain for pitch correction
    'ki': 0.0,  # Integral gain for pitch correction  
    'kd': 0.2   # Derivative gain for pitch correction
}

ROLL_PID_PARAMS = {
    'kp': 0.0,  # Proportional gain for roll correction
    'ki': 0.0,  # Integral gain for roll correction
    'kd': 0.0   # Derivative gain for roll correction
}

# DEADZONE CONFIGURATION - EDIT THIS TO CHANGE THE DEADZONE
BALANCE_DEADZONE = 0  # Degrees - no correction applied within this range from calibrated position

# Calibration file path
CALIBRATION_FILE = "/home/ubuntu/without_ros/mpu6050_calibration.json"

# Balance correction limits (max degrees to adjust servos)
MAX_BALANCE_CORRECTION = 100.0  # Maximum degrees to adjust any servo for balance

# Global variables for continuous balance monitoring
continuous_balance_active = False
continuous_balance_thread = None
current_static_mode = None
balance_lock = threading.Lock()

class PIDController:
    def __init__(self, kp, ki, kd, max_output=MAX_BALANCE_CORRECTION):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.max_output = max_output
        
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()
    
    def update(self, error):
        current_time = time.time()
        dt = current_time - self.last_time
        
        if dt <= 0.0:
            dt = 0.01  # Prevent division by zero
        
        # Proportional term
        proportional = self.kp * error
        
        # Integral term (with windup protection)
        self.integral += error * dt
        # Limit integral to prevent windup
        if self.max_output > 0:
            integral_limit = self.max_output / max(abs(self.ki), 0.001)
            self.integral = max(min(self.integral, integral_limit), -integral_limit)
        integral = self.ki * self.integral
        
        # Derivative term
        derivative = self.kd * (error - self.prev_error) / dt
        
        # Calculate output
        output = proportional + integral + derivative
        
        # Limit output
        if self.max_output > 0:
            output = max(min(output, self.max_output), -self.max_output)
        
        # Update for next iteration
        self.prev_error = error
        self.last_time = current_time
        
        return output
    
    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()

# Initialize PID controllers
pitch_pid = PIDController(PITCH_PID_PARAMS['kp'], PITCH_PID_PARAMS['ki'], PITCH_PID_PARAMS['kd'])
roll_pid = PIDController(ROLL_PID_PARAMS['kp'], ROLL_PID_PARAMS['ki'], ROLL_PID_PARAMS['kd'])

# Calibration data storage
calibration_data = {
    'pitch_offset': 5.0,
    'roll_offset': -10.0,
    'calibrated': True
}

def load_calibration():
    """Load calibration data from file"""
    global calibration_data
    try:
        if os.path.exists(CALIBRATION_FILE):
            with open(CALIBRATION_FILE, 'r') as f:
                calibration_data = json.load(f)
            print(f"✅ Calibration loaded: Pitch offset = {calibration_data['pitch_offset']:.2f}°, Roll offset = {calibration_data['roll_offset']:.2f}°")
        else:
            print("⚠️ No calibration file found. Please calibrate the sensor.")
    except Exception as e:
        print(f"Error loading calibration: {e}")

def save_calibration():
    """Save calibration data to file"""
    try:
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(calibration_data, f, indent=2)
        print(f"✅ Calibration saved to {CALIBRATION_FILE}")
    except Exception as e:
        print(f"Error saving calibration: {e}")

def get_mpu_readings():
    """Get pitch and roll from MPU6050"""
    if mpu is None:
        return 0.0, 0.0
    
    try:
        # Get accelerometer data
        accel_x, accel_y, accel_z = mpu.acceleration
        
        # Calculate pitch and roll from accelerometer
        # Pitch: rotation around Y-axis (forward/backward tilt)
        pitch = np.degrees(np.arctan2(-accel_x, np.sqrt(accel_y**2 + accel_z**2)))
        
        # Roll: rotation around X-axis (left/right tilt)  
        roll = np.degrees(np.arctan2(accel_y, np.sqrt(accel_x**2 + accel_z**2)))
        
        return pitch, roll
    except Exception as e:
        print(f"Error reading MPU6050: {e}")
        return 0.0, 0.0

def calibrate_mpu():
    """Calibrate MPU6050 when robot is in standing position"""
    if mpu is None:
        print("❌ MPU6050 not available for calibration")
        return False
    
    print("🔧 Starting MPU6050 calibration...")
    print("Moving robot to STANDING position for calibration...")
    
    # Move robot to standing position first
    set_pose(stand_angles.copy(), transition_time=1.0, enable_balance=False)
    time.sleep(1.0)  # Allow robot to settle
    
    print("Robot is now in standing position on level surface.")
    input("Press Enter when ready to calibrate...")
    
    # Take multiple readings for averaging
    pitch_readings = []
    roll_readings = []
    num_samples = 100
    
    print(f"Taking {num_samples} calibration readings...")
    for i in range(num_samples):
        pitch, roll = get_mpu_readings()
        pitch_readings.append(pitch)
        roll_readings.append(roll)
        time.sleep(0.05)  # 50ms between readings
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i + 1}/{num_samples}")
    
    # Calculate average offsets
    calibration_data['pitch_offset'] = np.mean(pitch_readings)
    calibration_data['roll_offset'] = np.mean(roll_readings)
    calibration_data['calibrated'] = True
    
    # Save calibration
    save_calibration()
    
    print(f"✅ Calibration complete!")
    print(f"   Pitch offset: {calibration_data['pitch_offset']:.2f}°")
    print(f"   Roll offset: {calibration_data['roll_offset']:.2f}°")
    print(f"   Deadzone: ±{BALANCE_DEADZONE}°")
    
    return True

def get_balance_corrections():
    """Calculate balance correction angles based on current tilt"""
    if mpu is None or not calibration_data['calibrated']:
        return {}, 0.0, 0.0, 0.0, 0.0
    
    # Get current readings
    current_pitch, current_roll = get_mpu_readings()
    
    # Calculate errors from calibrated position
    pitch_error = current_pitch - calibration_data['pitch_offset']
    roll_error = current_roll - calibration_data['roll_offset']
    
    # Apply deadzone
    if abs(pitch_error) < BALANCE_DEADZONE:
        pitch_error = 0.0
    if abs(roll_error) < BALANCE_DEADZONE:
        roll_error = 0.0
    
    # Calculate PID corrections
    pitch_correction = pitch_pid.update(pitch_error) if pitch_error != 0 else 0.0
    roll_correction = roll_pid.update(roll_error) if roll_error != 0 else 0.0
    
    # Generate servo corrections based on tilt direction
    corrections = {}
    
    # PITCH CORRECTIONS
    if pitch_correction != 0:
        # For negative pitch (forward tilt), apply corrections to bring robot back
        # For positive pitch (backward tilt), apply opposite corrections
        
        # Front legs
        corrections[1] = -pitch_correction  # FL thigh: negative pitch -> decrease, positive pitch -> increase
        corrections[2] = pitch_correction   # FL knee: negative pitch -> increase, positive pitch -> decrease
        corrections[5] = pitch_correction   # FR thigh: negative pitch -> increase, positive pitch -> decrease  
        corrections[6] = -pitch_correction  # FR knee: negative pitch -> decrease, positive pitch -> increase
        
        # Rear legs
        corrections[9] = pitch_correction   # RL thigh: negative pitch -> increase, positive pitch -> decrease
        corrections[10] = -pitch_correction # RL knee: negative pitch -> decrease, positive pitch -> increase
        corrections[13] = -pitch_correction # RR thigh: negative pitch -> decrease, positive pitch -> increase
        corrections[14] = pitch_correction  # RR knee: negative pitch -> increase, positive pitch -> decrease
    
    # ROLL CORRECTIONS  
    if roll_correction != 0:
        # For negative roll (left tilt), apply corrections to bring robot back
        # For positive roll (right tilt), apply opposite corrections
        
        # All legs affected by roll
        corrections[0] = corrections.get(0, 0) - roll_correction   # FL shoulder
        corrections[1] = corrections.get(1, 0) + roll_correction   # FL thigh
        corrections[2] = corrections.get(2, 0) - roll_correction   # FL knee
        
        corrections[4] = corrections.get(4, 0) - roll_correction   # FR shoulder
        corrections[5] = corrections.get(5, 0) + roll_correction   # FR thigh
        corrections[6] = corrections.get(6, 0) - roll_correction   # FR knee
        
        corrections[8] = corrections.get(8, 0) - roll_correction   # RL shoulder
        corrections[9] = corrections.get(9, 0) + roll_correction   # RL thigh
        corrections[10] = corrections.get(10, 0) - roll_correction # RL knee
        
        corrections[12] = corrections.get(12, 0) - roll_correction # RR shoulder
        corrections[13] = corrections.get(13, 0) + roll_correction # RR thigh
        corrections[14] = corrections.get(14, 0) - roll_correction # RR knee
    
    return corrections, pitch_error, roll_error, current_pitch, current_roll

def continuous_balance_monitor():
    """
    Continuous balance monitoring thread that runs every 100ms
    Applies balance corrections for static modes (stand, sit, straight)
    """
    global continuous_balance_active, current_static_mode
    
    print("🔄 Continuous balance monitoring started (100ms intervals)")
    update_count = 0
    
    while continuous_balance_active:
        try:
            with balance_lock:
                if current_static_mode is None:
                    break
                
                # Get base angles for current static mode
                if current_static_mode == 'stand':
                    base_angles = stand_angles.copy()
                elif current_static_mode == 'sit':
                    base_angles = sit_angles.copy()
                elif current_static_mode == 'straight':
                    base_angles = straight_angles.copy()
                else:
                    break
                
                # Get balance corrections
                corrections, pitch_error, roll_error, current_pitch, current_roll = get_balance_corrections()
                
                if corrections:
                    # Apply corrections to base angles
                    corrected_angles = base_angles.copy()
                    for ch in corrected_angles:
                        if ch in corrections:
                            corrected_angles[ch] += corrections[ch]
                            # Ensure angles stay within servo limits
                            if servo_types[ch] == "180":
                                corrected_angles[ch] = max(0, min(180, corrected_angles[ch]))
                            else:
                                corrected_angles[ch] = max(0, min(270, corrected_angles[ch]))
                    
                    # Apply corrected angles to servos
                    for ch in corrected_angles:
                        angle = corrected_angles[ch]
                        pwm_value = angle_to_pwm(angle, servo_types[ch])
                        try:
                            pwm.channels[ch].duty_cycle = int(pwm_value * 65535 / 4096)
                        except Exception as e:
                            print(f"Error setting PWM on channel {ch}: {e}")
                    
                    # Print status every 10 updates (about every 1 second)
                    update_count += 1
                    if update_count % 10 == 0:
                        print(f"⚖️ [{current_static_mode.upper()}] Pitch={current_pitch:.1f}° (err={pitch_error:.1f}°), Roll={current_roll:.1f}° (err={roll_error:.1f}°)")
                        
                        # Show active corrections
                        active_corrections = {ch: corr for ch, corr in corrections.items() if abs(corr) > 0.1}
                        if active_corrections:
                            corrections_str = ", ".join([f"Ch{ch}:{corr:+.1f}°" for ch, corr in active_corrections.items()])
                            print(f"   Active corrections: {corrections_str}")
                        else:
                            print("   No significant corrections needed")
            
            time.sleep(0.1)  # 100ms interval
            
        except Exception as e:
            print(f"Error in continuous balance monitor: {e}")
            time.sleep(0.1)
    
    print("🛑 Continuous balance monitoring stopped")

def start_continuous_balance(mode):
    """Start continuous balance monitoring for a static mode"""
    global continuous_balance_active, continuous_balance_thread, current_static_mode
    
    if mpu is None or not calibration_data['calibrated']:
        print("⚠️ Cannot start continuous balance: MPU6050 not available or not calibrated")
        return False
    
    # Stop any existing monitoring
    stop_continuous_balance()
    
    # Reset PID controllers
    pitch_pid.reset()
    roll_pid.reset()
    
    # Start new monitoring
    current_static_mode = mode
    continuous_balance_active = True
    continuous_balance_thread = threading.Thread(target=continuous_balance_monitor, daemon=True)
    continuous_balance_thread.start()
    
    return True

def stop_continuous_balance():
    """Stop continuous balance monitoring"""
    global continuous_balance_active, continuous_balance_thread, current_static_mode
    
    if continuous_balance_active:
        continuous_balance_active = False
        current_static_mode = None
        
        if continuous_balance_thread and continuous_balance_thread.is_alive():
            continuous_balance_thread.join(timeout=1.0)
        
        print("🛑 Continuous balance monitoring stopped")

def continuous_balance_stand():
    """Stand with continuous balance control for PID tuning"""
    if mpu is None:
        print("❌ MPU6050 not available for balance control")
        return
    
    if not calibration_data['calibrated']:
        print("⚠️ MPU6050 not calibrated. Please run 'calibrate' command first.")
        return
    
    print("🔧 Starting continuous balance control in standing position")
    print("📊 This mode is perfect for tuning PID values!")
    print("💡 Tips for tuning:")
    print("   - Start with Kp values (0.5-2.0)")
    print("   - Add Ki for steady-state error (0.1-0.5)")
    print("   - Add Kd for stability (0.1-0.5)")
    print("   - Manually tilt the robot to test response")
    print("   - Press Ctrl+C to stop and return to menu")
    print()
    print(f"🎛️ Current PID settings:")
    print(f"   Pitch: Kp={PITCH_PID_PARAMS['kp']}, Ki={PITCH_PID_PARAMS['ki']}, Kd={PITCH_PID_PARAMS['kd']}")
    print(f"   Roll:  Kp={ROLL_PID_PARAMS['kp']}, Ki={ROLL_PID_PARAMS['ki']}, Kd={ROLL_PID_PARAMS['kd']}")
    print(f"   Deadzone: ±{BALANCE_DEADZONE}°")
    print()
    
    # Move to standing position first
    print("Moving to standing position...")
    set_pose(stand_angles.copy(), transition_time=1.0, enable_balance=False)
    time.sleep(1.0)
    
    # Start continuous balance monitoring
    if start_continuous_balance('stand'):
        print("✅ Continuous balance monitoring started for STAND mode")
        print("   (Manually tilt robot to see balance corrections in action)")
        
        try:
            while True:
                time.sleep(1.0)  # Keep main thread alive
        except KeyboardInterrupt:
            print("\n🛑 Stopping continuous balance monitoring...")
            stop_continuous_balance()
            print("Returning to standing position...")
            set_pose(stand_angles.copy(), transition_time=0.5, enable_balance=False)
            time.sleep(0.5)

# ============================================================================
# ORIGINAL ROBOT CONTROL CODE (from p12-7.py)
# ============================================================================

# Servo types and channels
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "180", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Straight mode angles (previously standing mode)
straight_angles = {
    0: 170, 1: 10, 2: 150,    
    4: 100, 5: 115, 6: 10,    
    8: 150, 9: 23, 10: 150,  
    12: 115, 13: 117, 14: 5   
}

# Stand mode angles (previously sitting mode)
stand_angles = {
    0: 170, 1: 70, 2: 50,    
    4: 100, 5: 55, 6: 110,    
    8: 150, 9: 83, 10: 50,   
    12: 115, 13: 57, 14: 105  
}

# New sitting mode angles
sit_angles = {
    0: 170, 1: 110, 2: 10,    
    4: 100, 5: 15, 6: 150,    
    8: 150, 9: 123, 10: 10,   
    12: 115, 13: 17, 14: 145  
}

# Walking gait angles (using stand_angles as base, previously sitting_angles)
walking_phases = {
    "front_right": [
        {5: 55, 6: 110},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 65, 6: 120}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 70, 2: 50},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 60, 2: 40}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 57, 14: 105},  # Phase 1: Lower leg
        {13: 37, 14: 105},  # Phase 2: Push back
        {13: 37, 14: 120}, # Phase 3: Lift leg
        {13: 67, 14: 115}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 83, 10: 50},  # Phase 1: Lower leg
        {9: 103, 10: 50},  # Phase 2: Push back
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 73, 10: 40}   # Phase 4: Move forward
    ]
}

# Turn right gait angles
turn_right_phases = {
    "front_right": [
        {5: 50, 6: 105},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 60, 6: 115}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 65, 2: 45},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 55, 2: 35}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 52, 14: 100},  # Phase 1: Lower leg
        {13: 37, 14: 105},  # Phase 2: Push back
        {13: 37, 14: 120}, # Phase 3: Lift leg
        {13: 62, 14: 110}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 78, 10: 45},  # Phase 1: Lower leg
        {9: 103, 10: 50},  # Phase 2: Push back
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 68, 10: 35}   # Phase 4: Move forward
    ]
}

# Turn left gait angles
turn_left_phases = {
    "front_right": [
        {5: 65, 6: 120},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 75, 6: 130}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 80, 2: 60},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 70, 2: 50}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 67, 14: 115},  # Phase 1: Lower leg
        {13: 37, 14: 105},  # Phase 2: Push back
        {13: 37, 14: 120}, # Phase 3: Lift leg
        {13: 77, 14: 125}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 93, 10: 60},  # Phase 1: Lower leg
        {9: 103, 10: 50},  # Phase 2: Push back
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 83, 10: 50}   # Phase 4: Move forward
    ]
}

def angle_to_pwm(angle, servo_type):
    if servo_type == "180":
        min_angle, max_angle = 0, 180
    else:
        min_angle, max_angle = 0, 270
    min_pwm, max_pwm = 100, 500
    angle = max(min(angle, max_angle), min_angle)
    return int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))

def set_pose(target_angles, transition_time=1.0, steps=5, deactivate_after_move=False, enable_balance=False):
    """
    MODIFIED VERSION: Applies balance corrections during servo movement execution
    instead of at the beginning. This provides continuous balance correction
    throughout the entire movement.
    """
    global current_angles
    
    # Create step interpolation arrays for target movement
    step_angles = {}
    for ch in target_angles:
        start = current_angles.get(ch, 90 if servo_types[ch] == "180" else 135)
        end = target_angles[ch]
        step_angles[ch] = np.linspace(start, end, steps)

    # Execute movement with real-time balance corrections
    for i in range(steps):
        # Get the planned angles for this step
        planned_angles = {}
        for ch in target_angles:
            planned_angles[ch] = step_angles[ch][i]
        
        # Apply balance corrections if enabled
        final_angles = planned_angles.copy()
        if enable_balance:
            corrections, pitch_error, roll_error, current_pitch, current_roll = get_balance_corrections()
            if corrections:
                # Apply corrections to the current step angles
                for ch in planned_angles:
                    if ch in corrections:
                        final_angles[ch] += corrections[ch]
                        # Ensure angles stay within servo limits
                        if servo_types[ch] == "180":
                            final_angles[ch] = max(0, min(180, final_angles[ch]))
                        else:
                            final_angles[ch] = max(0, min(270, final_angles[ch]))
                
                # Print balance info every few steps (only if corrections are being applied)
                if i % 5 == 0 and any(abs(c) > 0.1 for c in corrections.values()):
                    print(f"⚖️ Step {i+1}/{steps}: Pitch={current_pitch:.1f}° (err={pitch_error:.1f}°), Roll={current_roll:.1f}° (err={roll_error:.1f}°)")
        
        # Apply the final angles (planned + balance corrections) to servos
        for ch in final_angles:
            angle = final_angles[ch]
            pwm_value = angle_to_pwm(angle, servo_types[ch])
            try:
                pwm.channels[ch].duty_cycle = int(pwm_value * 65535 / 4096)
            except Exception as e:
                print(f"Error setting PWM on channel {ch}: {e}")
        
        time.sleep(transition_time / steps)

    # Update current angles with the original target (not balance-corrected)
    current_angles.update(target_angles)

    if deactivate_after_move:
        time.sleep(0.1)
        for ch in target_angles:
            pwm.channels[ch].duty_cycle = 0

def walk_trot(cycles=50, enable_obstacle_avoidance=True, enable_balance=False):
    print("Starting trot walk...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will turn right if obstacle detected within 30cm")
    if enable_balance:
        print("🔧 Balance control enabled - robot will adjust for tilt DURING movement")
        if not calibration_data['calibrated']:
            print("⚠️ Warning: MPU6050 not calibrated! Please calibrate first for optimal balance.")
    
    # Stop any continuous balance monitoring during movement
    stop_continuous_balance()
    
    set_pose(stand_angles.copy(), transition_time=0.25, enable_balance=enable_balance)

    for cycle in range(cycles):
        # Check for obstacles before each cycle if avoidance is enabled
        if enable_obstacle_avoidance and check_obstacle():
            distance = get_distance()
            print(f"🚨 Obstacle detected at {distance:.1f}cm! Stopping forward walk and turning right...")
            
            # Stop current walk and start turning right until obstacle is cleared
            obstacle_turn_cycles = 0
            max_turn_cycles = 100  # Prevent infinite turning
            
            while check_obstacle() and obstacle_turn_cycles < max_turn_cycles:
                # Execute one turn right cycle
                for phase_idx in range(4):
                    fr_rl = phase_idx
                    fl_rr = (phase_idx + 2) % 4

                    angles = stand_angles.copy()
                    angles.update(turn_right_phases["front_right"][fr_rl])
                    angles.update(turn_right_phases["rear_left"][fr_rl])
                    angles.update(turn_right_phases["front_left"][fl_rr])
                    angles.update(turn_right_phases["rear_right"][fl_rr])

                    set_pose(angles, transition_time=0.25, enable_balance=enable_balance)
                    #time.sleep(0.0025)
                
                obstacle_turn_cycles += 1
                
                # Brief pause to check obstacle status
                time.sleep(0.1)
            
            if obstacle_turn_cycles >= max_turn_cycles:
                print("⚠️ Maximum turn cycles reached. Stopping for safety.")
                break
            else:
                distance = get_distance()
                print(f"✅ Obstacle cleared! Distance now: {distance:.1f}cm. Resuming forward walk...")
                continue  # Continue with remaining walk cycles
        
        # Execute normal walk cycle
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4

            angles = stand_angles.copy()
            angles.update(walking_phases["rear_left"][rl_fr])
            angles.update(walking_phases["front_right"][rl_fr])
            angles.update(walking_phases["rear_right"][rr_fl])
            angles.update(walking_phases["front_left"][rr_fl])

            set_pose(angles, transition_time=0.25, enable_balance=enable_balance)
           #time.sleep(0.0025)

    set_pose(stand_angles.copy(), transition_time=0.25, enable_balance=enable_balance)
    print("Trot walk complete.")

def turn_right(cycles=30, enable_obstacle_avoidance=False, enable_balance=False):
    print("Starting right turn...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will stop if obstacle detected within 30cm")
    if enable_balance:
        print("🔧 Balance control enabled - robot will adjust for tilt DURING movement")
    
    # Stop any continuous balance monitoring during movement
    stop_continuous_balance()
    
    set_pose(stand_angles.copy(), transition_time=0.25, enable_balance=enable_balance)

    for cycle in range(cycles):
        # Check for obstacles before each cycle if avoidance is enabled
        if enable_obstacle_avoidance and check_obstacle():
            distance = get_distance()
            print(f"🚨 Obstacle detected at {distance:.1f}cm! Stopping right turn...")
            break
        
        for phase_idx in range(4):
            # Diagonal pairs: FR-RL and FL-RR with 2 phase difference
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4

            angles = stand_angles.copy()
            angles.update(turn_right_phases["front_right"][fr_rl])
            angles.update(turn_right_phases["rear_left"][fr_rl])
            angles.update(turn_right_phases["front_left"][fl_rr])
            angles.update(turn_right_phases["rear_right"][fl_rr])

            set_pose(angles, transition_time=0.25, enable_balance=enable_balance)
            #time.sleep(0.0025)

    set_pose(stand_angles.copy(), transition_time=0.25, enable_balance=enable_balance)
    print("Right turn complete.")

def turn_left(cycles=30, enable_obstacle_avoidance=False, enable_balance=False):
    print("Starting left turn...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will stop if obstacle detected within 30cm")
    if enable_balance:
        print("🔧 Balance control enabled - robot will adjust for tilt DURING movement")
    
    # Stop any continuous balance monitoring during movement
    stop_continuous_balance()
    
    set_pose(stand_angles.copy(), transition_time=0.25, enable_balance=enable_balance)

    for cycle in range(cycles):
        # Check for obstacles before each cycle if avoidance is enabled
        if enable_obstacle_avoidance and check_obstacle():
            distance = get_distance()
            print(f"🚨 Obstacle detected at {distance:.1f}cm! Stopping left turn...")
            break
        
        for phase_idx in range(4):
            # Diagonal pairs: FR-RL and FL-RR with 2 phase difference
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4

            angles = stand_angles.copy()
            angles.update(turn_left_phases["front_right"][fr_rl])
            angles.update(turn_left_phases["rear_left"][fr_rl])
            angles.update(turn_left_phases["front_left"][fl_rr])
            angles.update(turn_left_phases["rear_right"][fl_rr])

            set_pose(angles, transition_time=0.25, enable_balance=enable_balance)
            time.sleep(0.0025)

    set_pose(stand_angles.copy(), transition_time=0.25, enable_balance=enable_balance)
    print("Left turn complete.")

# Initialize current angles
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}

# Initialize ultrasonic sensor
setup_ultrasonic()

# Load existing calibration
load_calibration()

# Main program
print("🤖 Quadruped Robot with CONTINUOUS Balance Control (Version 3)")
print("🔄 NEW: Automatic continuous balance monitoring for static modes!")
print("Commands: straight/stand/sit/walk/right/left/distance/calibrate/balance/q")
print("🔧 Balance features:")
print("   - 'calibrate': Calibrate MPU6050 when robot is in standing position")
print("   - 'balance': Test current pitch/roll readings and balance corrections")
print("   - Static modes (stand/sit/straight) now have automatic continuous balance!")
print("   - Choose (a)utomatic continuous balance when setting static poses")
print(f"📊 Current PID settings:")
print(f"   Pitch: Kp={PITCH_PID_PARAMS['kp']}, Ki={PITCH_PID_PARAMS['ki']}, Kd={PITCH_PID_PARAMS['kd']}")
print(f"   Roll:  Kp={ROLL_PID_PARAMS['kp']}, Ki={ROLL_PID_PARAMS['ki']}, Kd={ROLL_PID_PARAMS['kd']}")
print(f"   Deadzone: ±{BALANCE_DEADZONE}°")

try:
    while True:
        cmd = input("\nEnter command: ").strip().lower()
        if cmd == 'q':
            break
        elif cmd == 'straight':
            print("Moving to straight mode...")
            balance_choice = input("Balance control - (n)one/(s)ingle/(a)utomatic continuous, default=n: ").strip().lower()
            
            if balance_choice == 'a':
                # Move to straight pose first
                set_pose(straight_angles.copy(), enable_balance=False)
                # Start automatic continuous balance monitoring
                if start_continuous_balance('straight'):
                    print("✅ Straight pose set with AUTOMATIC continuous balance monitoring!")
                    print("   Robot will automatically correct for surface tilt every 100ms")
                    print("   Tilt the surface to see automatic corrections in action")
                else:
                    print("❌ Could not start automatic balance - MPU6050 not available or not calibrated")
            else:
                enable_balance = balance_choice == 's'
                set_pose(straight_angles.copy(), enable_balance=enable_balance)
                if enable_balance:
                    print("Straight pose set with single balance correction applied during movement.")
                else:
                    print("Straight pose set without balance control.")
            
            input("Press Enter to continue.")
            
        elif cmd == 'stand':
            print("Moving to stand mode...")
            balance_choice = input("Balance control - (n)one/(s)ingle/(a)utomatic continuous/(c)ontinuous tuning, default=n: ").strip().lower()
            
            if balance_choice == 'c':
                continuous_balance_stand()
            elif balance_choice == 'a':
                # Move to stand pose first
                set_pose(stand_angles.copy(), enable_balance=False)
                # Start automatic continuous balance monitoring
                if start_continuous_balance('stand'):
                    print("✅ Stand pose set with AUTOMATIC continuous balance monitoring!")
                    print("   Robot will automatically correct for surface tilt every 100ms")
                    print("   Tilt the surface to see automatic corrections in action")
                else:
                    print("❌ Could not start automatic balance - MPU6050 not available or not calibrated")
            else:
                enable_balance = balance_choice == 's'
                set_pose(stand_angles.copy(), enable_balance=enable_balance)
                if enable_balance:
                    print("Stand pose set with single balance correction applied during movement.")
                else:
                    print("Stand pose set without balance control.")
            
            input("Press Enter to continue.")
            
        elif cmd == 'sit':
            print("Moving to sit mode...")
            balance_choice = input("Balance control - (n)one/(s)ingle/(a)utomatic continuous, default=n: ").strip().lower()
            
            if balance_choice == 'a':
                # Move to sit pose first
                set_pose(sit_angles.copy(), enable_balance=False)
                # Start automatic continuous balance monitoring
                if start_continuous_balance('sit'):
                    print("✅ Sit pose set with AUTOMATIC continuous balance monitoring!")
                    print("   Robot will automatically correct for surface tilt every 100ms")
                    print("   Tilt the surface to see automatic corrections in action")
                else:
                    print("❌ Could not start automatic balance - MPU6050 not available or not calibrated")
            else:
                enable_balance = balance_choice == 's'
                set_pose(sit_angles.copy(), enable_balance=enable_balance)
                if enable_balance:
                    print("Sit pose set with single balance correction applied during movement.")
                else:
                    print("Sit pose set without balance control.")
                    
            input("Press Enter to continue.")
            
        elif cmd == 'walk':
            # Stop any continuous balance monitoring before movement
            stop_continuous_balance()
            
            obstacle_choice = input("Enable obstacle avoidance? (y/n, default=y): ").strip().lower()
            enable_avoidance = obstacle_choice != 'n'
            balance_choice = input("Enable balance control? (y/n, default=n): ").strip().lower()
            enable_balance = balance_choice == 'y'
            
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED - robot will turn right if obstacle detected within 30cm")
            else:
                print("⚠️ Obstacle avoidance DISABLED - robot will walk forward regardless of obstacles")
            
            if enable_balance:
                print("🔄 CONTINUOUS balance control enabled - corrections applied during each step!")
            
            walk_trot(cycles=50, enable_obstacle_avoidance=enable_avoidance, enable_balance=enable_balance)
            input("Walk finished. Press Enter to continue.")
            
        elif cmd == 'right':
            # Stop any continuous balance monitoring before movement
            stop_continuous_balance()
            
            obstacle_choice = input("Enable obstacle avoidance during turn? (y/n, default=n): ").strip().lower()
            enable_avoidance = obstacle_choice == 'y'
            balance_choice = input("Enable balance control? (y/n, default=n): ").strip().lower()
            enable_balance = balance_choice == 'y'
            
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED during right turn")
            else:
                print("⚠️ Obstacle avoidance DISABLED during right turn")
            
            if enable_balance:
                print("🔄 CONTINUOUS balance control enabled during turn!")
            
            turn_right(cycles=30, enable_obstacle_avoidance=enable_avoidance, enable_balance=enable_balance)
            input("Right turn finished. Press Enter to continue.")
            
        elif cmd == 'left':
            # Stop any continuous balance monitoring before movement
            stop_continuous_balance()
            
            obstacle_choice = input("Enable obstacle avoidance during turn? (y/n, default=n): ").strip().lower()
            enable_avoidance = obstacle_choice == 'y'
            balance_choice = input("Enable balance control? (y/n, default=n): ").strip().lower()
            enable_balance = balance_choice == 'y'
            
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED during left turn")
            else:
                print("⚠️ Obstacle avoidance DISABLED during left turn")
            
            if enable_balance:
                print("🔄 CONTINUOUS balance control enabled during turn!")
            
            turn_left(cycles=30, enable_obstacle_avoidance=enable_avoidance, enable_balance=enable_balance)
            input("Left turn finished. Press Enter to continue.")
            
        elif cmd == 'distance':
            distance = get_distance()
            if distance == -1:
                print("Sensor timeout - check ultrasonic sensor connections")
            else:
                status = "🚨 OBSTACLE!" if distance <= 30 else "✅ Clear"
                print(f"Distance: {distance:.2f} cm | {status}")
                
        elif cmd == 'calibrate':
            # Stop any continuous balance monitoring during calibration
            stop_continuous_balance()
            
            if calibrate_mpu():
                # Reset PID controllers after calibration
                pitch_pid.reset()
                roll_pid.reset()
                print("PID controllers reset after calibration.")
                
        elif cmd == 'balance':
            if mpu is None:
                print("❌ MPU6050 not available")
            elif not calibration_data['calibrated']:
                print("⚠️ MPU6050 not calibrated. Please run 'calibrate' command first.")
            else:
                print("📊 Current balance readings:")
                current_pitch, current_roll = get_mpu_readings()
                pitch_error = current_pitch - calibration_data['pitch_offset']
                roll_error = current_roll - calibration_data['roll_offset']
                
                print(f"   Raw: Pitch={current_pitch:.2f}°, Roll={current_roll:.2f}°")
                print(f"   Calibrated offsets: Pitch={calibration_data['pitch_offset']:.2f}°, Roll={calibration_data['roll_offset']:.2f}°")
                print(f"   Errors: Pitch={pitch_error:.2f}°, Roll={roll_error:.2f}°")
                print(f"   Deadzone: ±{BALANCE_DEADZONE}°")
                
                # Show if corrections would be applied
                if abs(pitch_error) < BALANCE_DEADZONE and abs(roll_error) < BALANCE_DEADZONE:
                    print("   Status: ✅ Within deadzone - no corrections needed")
                else:
                    print("   Status: ⚖️ Outside deadzone - corrections would be applied")
                    corrections, _, _, _, _ = get_balance_corrections()
                    if corrections:
                        print("   Servo corrections that would be applied:")
                        for ch, correction in corrections.items():
                            if abs(correction) > 0.1:
                                print(f"     Channel {ch}: {correction:+.1f}°")
                                
                # Show continuous balance status
                if continuous_balance_active:
                    print(f"   Continuous Balance: 🔄 ACTIVE for {current_static_mode.upper()} mode")
                else:
                    print("   Continuous Balance: 🛑 INACTIVE")
                    
        else:
            print("Invalid command. Use: straight/stand/sit/walk/right/left/distance/calibrate/balance/q")
            
finally:
    print("Shutting down...")
    
    # Stop continuous balance monitoring
    stop_continuous_balance()
    
    print("Resetting all servos to neutral...")
    for channel, servo_type in servo_types.items():
        neutral_angle = 90 if servo_type == "180" else 135
        pwm_value = angle_to_pwm(neutral_angle, servo_type)
        pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
        time.sleep(0.01)
    time.sleep(0.5)
    for i in range(16):
        pwm.channels[i].duty_cycle = 0
    pwm.deinit()
    
    # Cleanup GPIO
    GPIO.cleanup()
    print("Shutdown complete - servos and GPIO cleaned up.")
