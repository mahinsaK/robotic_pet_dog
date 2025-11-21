#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685
import time
import numpy as np
import RPi.GPIO as GPIO
import json
import threading
from smbus2 import SMBus
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
    pwm.frequency = 50  # 50 Hz for servos
except Exception as e:
    print(f"Error initializing PCA9685: {e}")
    exit(1)

# Clear all PWM outputs at startup
for i in range(16):
    pwm.channels[i].duty_cycle = 0

# Ultrasonic sensor configuration
TRIG = 23  # GPIO23
ECHO = 24  # GPIO24

# MPU-6050 Configuration
MPU6050_ADDR = 0x68
bus = SMBus(1)

# MPU-6050 Registers
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F

# Balance control variables
balance_enabled = False
calibrated_pitch = 0.0
calibrated_roll = 0.0
balance_thread = None
balance_running = False

# DEADZONE CONFIGURATION - Edit this value to change the deadzone
DEADZONE_DEGREES = 10.0  # Deadzone of ±10 degrees from calibrated position

def setup_mpu6050():
    """Initialize MPU-6050 sensor"""
    try:
        # Wake up the MPU-6050
        bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
        print("MPU-6050 initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing MPU-6050: {e}")
        return False

def read_mpu6050():
    """Read accelerometer data and calculate pitch and roll"""
    try:
        # Read accelerometer data
        accel_x = read_word_2c(ACCEL_XOUT_H)
        accel_y = read_word_2c(ACCEL_YOUT_H)
        accel_z = read_word_2c(ACCEL_ZOUT_H)
        
        # Convert to g-force
        accel_x = accel_x / 16384.0
        accel_y = accel_y / 16384.0
        accel_z = accel_z / 16384.0
        
        # Calculate pitch and roll in degrees
        pitch = math.degrees(math.atan2(accel_y, math.sqrt(accel_x**2 + accel_z**2)))
        roll = math.degrees(math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)))
        
        return pitch, roll
    except Exception as e:
        print(f"Error reading MPU-6050: {e}")
        return None, None

def read_word_2c(addr):
    """Read 16-bit signed value from MPU-6050"""
    high = bus.read_byte_data(MPU6050_ADDR, addr)
    low = bus.read_byte_data(MPU6050_ADDR, addr + 1)
    val = (high << 8) + low
    if val >= 0x8000:
        return -((65535 - val) + 1)
    else:
        return val

def calibrate_mpu6050():
    """Calibrate MPU-6050 when robot is in standing position"""
    global calibrated_pitch, calibrated_roll
    
    print("Calibrating MPU-6050...")
    print("Make sure the robot is in standing position on a level surface.")
    input("Press Enter when ready to calibrate...")
    
    # Take multiple readings and average them
    pitch_sum = 0
    roll_sum = 0
    num_readings = 50
    
    print(f"Taking {num_readings} readings...")
    for i in range(num_readings):
        pitch, roll = read_mpu6050()
        if pitch is not None and roll is not None:
            pitch_sum += pitch
            roll_sum += roll
        time.sleep(0.02)  # 20ms between readings
    
    calibrated_pitch = pitch_sum / num_readings
    calibrated_roll = roll_sum / num_readings
    
    print(f"Calibration complete!")
    print(f"Calibrated Pitch: {calibrated_pitch:.2f}°")
    print(f"Calibrated Roll: {calibrated_roll:.2f}°")
    
    # Save calibration to file
    calibration_data = {
        "calibrated_pitch": calibrated_pitch,
        "calibrated_roll": calibrated_roll
    }
    
    try:
        with open("mpu6050_calibration.json", "w") as f:
            json.dump(calibration_data, f, indent=2)
        print("Calibration saved to mpu6050_calibration.json")
    except Exception as e:
        print(f"Warning: Could not save calibration: {e}")

def load_calibration():
    """Load calibration from file if it exists"""
    global calibrated_pitch, calibrated_roll
    
    try:
        with open("mpu6050_calibration.json", "r") as f:
            calibration_data = json.load(f)
            calibrated_pitch = calibration_data["calibrated_pitch"]
            calibrated_roll = calibration_data["calibrated_roll"]
        print(f"Calibration loaded: Pitch={calibrated_pitch:.2f}°, Roll={calibrated_roll:.2f}°")
        return True
    except FileNotFoundError:
        print("No calibration file found. Please calibrate first.")
        return False
    except Exception as e:
        print(f"Error loading calibration: {e}")
        return False

def calculate_balance_corrections(current_pitch, current_roll):
    """Calculate servo angle corrections based on pitch and roll"""
    corrections = {}
    
    # Calculate deviations from calibrated position
    pitch_error = current_pitch - calibrated_pitch
    roll_error = current_roll - calibrated_roll
    
    # Apply deadzone
    if abs(pitch_error) < DEADZONE_DEGREES:
        pitch_error = 0
    if abs(roll_error) < DEADZONE_DEGREES:
        roll_error = 0
    
    # Pitch corrections
    if pitch_error != 0:
        if pitch_error < 0:  # Negative pitch
            corrections[1] = -2 * abs(pitch_error)  # FL thigh
            corrections[2] = +2 * abs(pitch_error)  # FL knee
            corrections[5] = +2 * abs(pitch_error)  # FR thigh
            corrections[6] = -2 * abs(pitch_error)  # FR knee
            corrections[9] = +2 * abs(pitch_error)  # RL thigh
            corrections[10] = -2 * abs(pitch_error) # RL knee
            corrections[13] = -2 * abs(pitch_error) # RR thigh
            corrections[14] = +2 * abs(pitch_error) # RR knee
        else:  # Positive pitch
            corrections[1] = +2 * abs(pitch_error)  # FL thigh
            corrections[2] = -2 * abs(pitch_error)  # FL knee
            corrections[5] = -2 * abs(pitch_error)  # FR thigh
            corrections[6] = +2 * abs(pitch_error)  # FR knee
            corrections[9] = -2 * abs(pitch_error)  # RL thigh
            corrections[10] = +2 * abs(pitch_error) # RL knee
            corrections[13] = +2 * abs(pitch_error) # RR thigh
            corrections[14] = -2 * abs(pitch_error) # RR knee
    
    # Roll corrections
    if roll_error != 0:
        if roll_error < 0:  # Negative roll
            corrections[0] = corrections.get(0, 0) - 2 * abs(roll_error)   # FL shoulder
            corrections[1] = corrections.get(1, 0) + 2 * abs(roll_error)   # FL thigh
            corrections[2] = corrections.get(2, 0) - 2 * abs(roll_error)   # FL knee
            corrections[4] = corrections.get(4, 0) - 2 * abs(roll_error)   # FR shoulder
            corrections[5] = corrections.get(5, 0) + 2 * abs(roll_error)   # FR thigh
            corrections[6] = corrections.get(6, 0) - 2 * abs(roll_error)   # FR knee
            corrections[8] = corrections.get(8, 0) - 2 * abs(roll_error)   # RL shoulder
            corrections[9] = corrections.get(9, 0) + 2 * abs(roll_error)   # RL thigh
            corrections[10] = corrections.get(10, 0) - 2 * abs(roll_error) # RL knee
            corrections[12] = corrections.get(12, 0) - 2 * abs(roll_error) # RR shoulder
            corrections[13] = corrections.get(13, 0) + 2 * abs(roll_error) # RR thigh
            corrections[14] = corrections.get(14, 0) - 2 * abs(roll_error) # RR knee
        else:  # Positive roll
            corrections[0] = corrections.get(0, 0) + 2 * abs(roll_error)   # FL shoulder
            corrections[1] = corrections.get(1, 0) - 2 * abs(roll_error)   # FL thigh
            corrections[2] = corrections.get(2, 0) + 2 * abs(roll_error)   # FL knee
            corrections[4] = corrections.get(4, 0) + 2 * abs(roll_error)   # FR shoulder
            corrections[5] = corrections.get(5, 0) - 2 * abs(roll_error)   # FR thigh
            corrections[6] = corrections.get(6, 0) + 2 * abs(roll_error)   # FR knee
            corrections[8] = corrections.get(8, 0) + 2 * abs(roll_error)   # RL shoulder
            corrections[9] = corrections.get(9, 0) - 2 * abs(roll_error)   # RL thigh
            corrections[10] = corrections.get(10, 0) + 2 * abs(roll_error) # RL knee
            corrections[12] = corrections.get(12, 0) + 2 * abs(roll_error) # RR shoulder
            corrections[13] = corrections.get(13, 0) - 2 * abs(roll_error) # RR thigh
            corrections[14] = corrections.get(14, 0) + 2 * abs(roll_error) # RR knee
    
    return corrections

def balance_control_loop():
    """Background thread for continuous balance control"""
    global balance_running
    
    print("Balance control started")
    while balance_running:
        try:
            pitch, roll = read_mpu6050()
            if pitch is not None and roll is not None:
                corrections = calculate_balance_corrections(pitch, roll)
                
                # Apply corrections to current standing angles
                if corrections:
                    corrected_angles = stand_angles.copy()
                    for channel, correction in corrections.items():
                        if channel in corrected_angles:
                            corrected_angles[channel] += correction
                            # Ensure angles stay within servo limits
                            if servo_types[channel] == "180":
                                corrected_angles[channel] = max(0, min(180, corrected_angles[channel]))
                            else:
                                corrected_angles[channel] = max(0, min(270, corrected_angles[channel]))
                    
                    # Apply corrections immediately
                    apply_angles_directly(corrected_angles)
            
        except Exception as e:
            print(f"Balance control error: {e}")
        
        time.sleep(0.1)  # 100ms update rate
    
    print("Balance control stopped")

def apply_angles_directly(angles):
    """Apply servo angles directly without transition animation"""
    for ch, angle in angles.items():
        if ch in servo_types:
            pwm_value = angle_to_pwm(angle, servo_types[ch])
            try:
                pwm.channels[ch].duty_cycle = int(pwm_value * 65535 / 4096)
            except Exception as e:
                print(f"Error setting PWM on channel {ch}: {e}")

def start_balance_control():
    """Start the balance control system"""
    global balance_enabled, balance_thread, balance_running
    
    if not balance_enabled:
        print("Balance control is not enabled. Enable it first.")
        return
    
    if balance_running:
        print("Balance control is already running.")
        return
    
    balance_running = True
    balance_thread = threading.Thread(target=balance_control_loop, daemon=True)
    balance_thread.start()

def stop_balance_control():
    """Stop the balance control system"""
    global balance_running
    
    balance_running = False
    if balance_thread is not None:
        balance_thread.join(timeout=1.0)
    print("Balance control stopped")

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

def set_pose(target_angles, transition_time=1.0, steps=5, deactivate_after_move=False):
    global current_angles
    
    # Temporarily stop balance control during pose transitions
    was_balancing = balance_running
    if was_balancing:
        stop_balance_control()
    
    step_angles = {}
    for ch in target_angles:
        start = current_angles.get(ch, 90 if servo_types[ch] == "180" else 135)
        end = target_angles[ch]
        step_angles[ch] = np.linspace(start, end, steps)

    for i in range(steps):
        for ch in target_angles:
            angle = step_angles[ch][i]
            pwm_value = angle_to_pwm(angle, servo_types[ch])
            try:
                pwm.channels[ch].duty_cycle = int(pwm_value * 65535 / 4096)
            except Exception as e:
                print(f"Error setting PWM on channel {ch}: {e}")
        time.sleep(transition_time / steps)

    current_angles.update(target_angles)

    if deactivate_after_move:
        time.sleep(0.1)
        for ch in target_angles:
            pwm.channels[ch].duty_cycle = 0
    
    # Restart balance control if it was running
    if was_balancing and balance_enabled:
        start_balance_control()

def walk_trot(cycles=50, enable_obstacle_avoidance=True):
    print("Starting trot walk...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will turn right if obstacle detected within 30cm")
    
    # Temporarily stop balance control during walking
    was_balancing = balance_running
    if was_balancing:
        stop_balance_control()
    
    set_pose(stand_angles, transition_time=0.25)

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

                    set_pose(angles, transition_time=0.25)
                
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

            set_pose(angles, transition_time=0.25)

    set_pose(stand_angles, transition_time=0.25)
    
    # Restart balance control if it was running
    if was_balancing and balance_enabled:
        start_balance_control()
    
    print("Trot walk complete.")

def turn_right(cycles=30, enable_obstacle_avoidance=False):
    print("Starting right turn...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will stop if obstacle detected within 30cm")
    
    # Temporarily stop balance control during turning
    was_balancing = balance_running
    if was_balancing:
        stop_balance_control()
    
    set_pose(stand_angles, transition_time=0.25)

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

            set_pose(angles, transition_time=0.25)

    set_pose(stand_angles, transition_time=0.25)
    
    # Restart balance control if it was running
    if was_balancing and balance_enabled:
        start_balance_control()
    
    print("Right turn complete.")

def turn_left(cycles=30, enable_obstacle_avoidance=False):
    print("Starting left turn...")
    if enable_obstacle_avoidance:
        print("Obstacle avoidance enabled - will stop if obstacle detected within 30cm")
    
    # Temporarily stop balance control during turning
    was_balancing = balance_running
    if was_balancing:
        stop_balance_control()
    
    set_pose(stand_angles, transition_time=0.25)

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

            set_pose(angles, transition_time=0.25)

    set_pose(stand_angles, transition_time=0.25)
    
    # Restart balance control if it was running
    if was_balancing and balance_enabled:
        start_balance_control()
    
    print("Left turn complete.")

# Initialize current angles
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}

# Initialize sensors
setup_ultrasonic()
if setup_mpu6050():
    print("MPU-6050 ready for use")
else:
    print("Warning: MPU-6050 not available")

# Main program
print("=" * 60)
print("🤖 BALANCED QUADRUPED ROBOT CONTROL SYSTEM")
print("=" * 60)
print("Commands:")
print("  straight/stand/sit/walk/right/left - Robot movements")
print("  distance - Check ultrasonic sensor")
print("  calibrate - Calibrate MPU-6050 (robot must be in standing position)")
print("  balance_on/balance_off - Enable/disable balance control")
print("  balance_status - Show balance system status")
print("  mpu_test - Test MPU-6050 readings")
print("  q - Quit")
print()
print("⚙️ Balance System Configuration:")
print(f"   Deadzone: ±{DEADZONE_DEGREES}° (edit DEADZONE_DEGREES variable to change)")
print("   Update rate: 100ms (0.1 seconds)")
print()

# Try to load existing calibration
if load_calibration():
    balance_enabled = True
    print("🎯 Balance system ready! Calibration loaded successfully.")
else:
    print("⚠️ Balance system disabled. Please calibrate first.")

try:
    while True:
        if balance_enabled and balance_running:
            status_indicator = "🟢 BALANCE ON"
        elif balance_enabled:
            status_indicator = "🟡 BALANCE READY"
        else:
            status_indicator = "🔴 BALANCE OFF"
        
        cmd = input(f"\n[{status_indicator}] Enter command: ").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd == 'straight':
            print("Moving to straight mode...")
            set_pose(straight_angles)
            input("Straight pose set. Press Enter to continue.")
        elif cmd == 'stand':
            print("Moving to stand mode...")
            set_pose(stand_angles)
            input("Stand pose set. Press Enter to continue.")
        elif cmd == 'sit':
            print("Moving to sit mode...")
            set_pose(sit_angles)
            input("Sit pose set. Press Enter to continue.")
        elif cmd == 'walk':
            obstacle_choice = input("Enable obstacle avoidance? (y/n, default=y): ").strip().lower()
            enable_avoidance = obstacle_choice != 'n'
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED - robot will turn right if obstacle detected within 30cm")
            else:
                print("⚠️ Obstacle avoidance DISABLED - robot will walk forward regardless of obstacles")
            walk_trot(cycles=50, enable_obstacle_avoidance=enable_avoidance)
            input("Walk finished. Press Enter to continue.")
        elif cmd == 'right':
            obstacle_choice = input("Enable obstacle avoidance during turn? (y/n, default=n): ").strip().lower()
            enable_avoidance = obstacle_choice == 'y'
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED during right turn")
            else:
                print("⚠️ Obstacle avoidance DISABLED during right turn")
            turn_right(cycles=30, enable_obstacle_avoidance=enable_avoidance)
            input("Right turn finished. Press Enter to continue.")
        elif cmd == 'left':
            obstacle_choice = input("Enable obstacle avoidance during turn? (y/n, default=n): ").strip().lower()
            enable_avoidance = obstacle_choice == 'y'
            if enable_avoidance:
                print("🚨 Obstacle avoidance ENABLED during left turn")
            else:
                print("⚠️ Obstacle avoidance DISABLED during left turn")
            turn_left(cycles=30, enable_obstacle_avoidance=enable_avoidance)
            input("Left turn finished. Press Enter to continue.")
        elif cmd == 'distance':
            distance = get_distance()
            if distance == -1:
                print("Sensor timeout - check ultrasonic sensor connections")
            else:
                status = "🚨 OBSTACLE!" if distance <= 30 else "✅ Clear"
                print(f"Distance: {distance:.2f} cm | {status}")
        elif cmd == 'calibrate':
            calibrate_mpu6050()
            balance_enabled = True
            print("✅ Balance system enabled!")
        elif cmd == 'balance_on':
            if not balance_enabled:
                print("❌ Balance system not enabled. Please calibrate first.")
            else:
                start_balance_control()
        elif cmd == 'balance_off':
            stop_balance_control()
        elif cmd == 'balance_status':
            print(f"Balance Enabled: {'✅ Yes' if balance_enabled else '❌ No'}")
            print(f"Balance Running: {'✅ Yes' if balance_running else '❌ No'}")
            print(f"Deadzone: ±{DEADZONE_DEGREES}°")
            if balance_enabled:
                print(f"Calibrated Pitch: {calibrated_pitch:.2f}°")
                print(f"Calibrated Roll: {calibrated_roll:.2f}°")
        elif cmd == 'mpu_test':
            if balance_enabled:
                print("Testing MPU-6050... (Press Ctrl+C to stop)")
                try:
                    while True:
                        pitch, roll = read_mpu6050()
                        if pitch is not None and roll is not None:
                            pitch_error = pitch - calibrated_pitch
                            roll_error = roll - calibrated_roll
                            print(f"Pitch: {pitch:6.2f}° (error: {pitch_error:+6.2f}°) | Roll: {roll:6.2f}° (error: {roll_error:+6.2f}°)")
                        else:
                            print("Error reading MPU-6050")
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    print("\nMPU-6050 test stopped")
            else:
                print("Balance system not enabled. Please calibrate first.")
        else:
            print("Invalid command. Use: straight/stand/sit/walk/right/left/distance/calibrate/balance_on/balance_off/balance_status/mpu_test/q")

finally:
    print("\nShutting down...")
    stop_balance_control()
    
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
