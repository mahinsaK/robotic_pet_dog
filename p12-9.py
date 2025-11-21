#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685
import time
import numpy as np
import RPi.GPIO as GPIO

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

# Obstacle avoidance parameters
OBSTACLE_AVOIDANCE_ENABLED = True  # Enable/disable obstacle avoidance - adjustable
OBSTACLE_DISTANCE_THRESHOLD = 40.0  # cm - adjustable (max detection range)
OBSTACLE_COOLDOWN_TIME = 5.0  # seconds - adjustable
last_obstacle_reaction_time = 0

# Avoidance sequence cycle counts - adjustable
STEP1_RIGHT_CYCLES = 1    # Step 1: Turn right cycles
# Step 2: Move forward cycles - AUTO-CALCULATED based on obstacle distance
STEP3_LEFT_CYCLES = 2     # Step 3: Turn left cycles
# Step 4: Move forward cycles - AUTO-CALCULATED based on obstacle distance  
STEP5_RIGHT_CYCLES = 1    # Step 5: Turn right cycles

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
    Check if there's an obstacle within threshold distance
    Returns True if obstacle detected, False otherwise
    """
    distance = get_distance()
    if distance == -1:  # Sensor timeout
        return False  # Assume no obstacle if sensor fails
    return distance <= OBSTACLE_DISTANCE_THRESHOLD

def can_react_to_obstacle():
    """
    Check if enough time has passed since last obstacle reaction
    """
    global last_obstacle_reaction_time
    current_time = time.time()
    return (current_time - last_obstacle_reaction_time) >= OBSTACLE_COOLDOWN_TIME

def execute_obstacle_avoidance_sequence(obstacle_distance):
    """
    Execute the 5-step obstacle avoidance sequence with distance-based cycles:
    1. Turn right (configurable cycles)
    2. Move forward (distance-based cycles)  
    3. Turn left (configurable cycles)
    4. Move forward (distance-based cycles)
    5. Turn right (configurable cycles)
    """
    global last_obstacle_reaction_time
    
    # Validate distance before proceeding
    if obstacle_distance == -1:
        print("⚠️ Invalid distance reading, skipping avoidance sequence")
        return
    
    print("🚨 OBSTACLE DETECTED! Executing avoidance sequence...")
    print(f"Sequence: R{STEP1_RIGHT_CYCLES} → F(auto) → L{STEP3_LEFT_CYCLES} → F(auto) → R{STEP5_RIGHT_CYCLES}")
    last_obstacle_reaction_time = time.time()
    
    # Calculate forward cycles based on obstacle distance
    if obstacle_distance < 10:
        forward_cycles = 1
    elif obstacle_distance < 20:
        forward_cycles = 2
    elif obstacle_distance < 30:
        forward_cycles = 3
    elif obstacle_distance <= 40:  # Only react up to 40cm
        forward_cycles = 4
    else:
        # This shouldn't happen since we only detect up to 40cm
        forward_cycles = 4
    
    print(f"Distance: {obstacle_distance:.1f}cm → Forward cycles: {forward_cycles}")
    
    # Step 1: Turn right (configurable cycles)
    print(f"Step 1/5: Turn right {STEP1_RIGHT_CYCLES} cycle(s)")
    for cycle in range(STEP1_RIGHT_CYCLES):
        for phase_idx in range(4):
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4
            angles = stand_angles.copy()
            angles.update(turn_right_phases["front_right"][fr_rl])
            angles.update(turn_right_phases["rear_left"][fr_rl])
            angles.update(turn_right_phases["front_left"][fl_rr])
            angles.update(turn_right_phases["rear_right"][fl_rr])
            set_pose(angles, transition_time=0.015)
    
    # Step 2: Move forward (distance-based cycles)
    print(f"Step 2/5: Move forward {forward_cycles} cycle(s)")
    for cycle in range(forward_cycles):
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4
            angles = stand_angles.copy()
            angles.update(walking_phases["rear_left"][rl_fr])
            angles.update(walking_phases["front_right"][rl_fr])
            angles.update(walking_phases["rear_right"][rr_fl])
            angles.update(walking_phases["front_left"][rr_fl])
            set_pose(angles, transition_time=0.015)
    
    # Step 3: Turn left (configurable cycles)
    print(f"Step 3/5: Turn left {STEP3_LEFT_CYCLES} cycle(s)")
    for cycle in range(STEP3_LEFT_CYCLES):
        for phase_idx in range(4):
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4
            angles = stand_angles.copy()
            angles.update(turn_left_phases["front_right"][fr_rl])
            angles.update(turn_left_phases["rear_left"][fr_rl])
            angles.update(turn_left_phases["front_left"][fl_rr])
            angles.update(turn_left_phases["rear_right"][fl_rr])
            set_pose(angles, transition_time=0.015)
    
    # Step 4: Move forward (distance-based cycles)
    print(f"Step 4/5: Move forward {forward_cycles} cycle(s)")
    for cycle in range(forward_cycles):
        for phase_idx in range(4):
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4
            angles = stand_angles.copy()
            angles.update(walking_phases["rear_left"][rl_fr])
            angles.update(walking_phases["front_right"][rl_fr])
            angles.update(walking_phases["rear_right"][rr_fl])
            angles.update(walking_phases["front_left"][rr_fl])
            set_pose(angles, transition_time=0.015)
    
    # Step 5: Turn right (configurable cycles)
    print(f"Step 5/5: Turn right {STEP5_RIGHT_CYCLES} cycle(s)")
    for cycle in range(STEP5_RIGHT_CYCLES):
        for phase_idx in range(4):
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4
            angles = stand_angles.copy()
            angles.update(turn_right_phases["front_right"][fr_rl])
            angles.update(turn_right_phases["rear_left"][fr_rl])
            angles.update(turn_right_phases["front_left"][fl_rr])
            angles.update(turn_right_phases["rear_right"][fl_rr])
            set_pose(angles, transition_time=0.015)
    
    set_pose(stand_angles, transition_time=0.015)
    print("✅ Obstacle avoidance sequence completed!")

# Servo types and channels
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "180", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Straight mode angles (previously standing mode)
straight_angles = {
    0: 160, 1: 10, 2: 150,    
    4: 100, 5: 115, 6: 10,    
    8: 143.5, 9: 23, 10: 150,  
    12: 120, 13: 105, 14: 5   
}

# Stand mode angles (previously sitting mode)
stand_angles = {
    0: 160, 1: 70, 2: 50,    
    4: 100, 5: 55, 6: 110,    
    8: 143.5, 9: 83, 10: 50,   
    12: 120, 13: 45, 14: 105  
}

# New sitting mode angles
sit_angles = {
    0: 160, 1: 110, 2: 10,    
    4: 100, 5: 15, 6: 150,    
    8: 143.5, 9: 123, 10: 10,   
    12: 120, 13: 5, 14: 145  
}

# Walking gait angles (using stand_angles as base) -> walk 2
walking_phases = {
    "front_right": [
        {5: 45, 6: 115},  # Phase 1: Lower leg {5: 55, 6: 110}
        {5: 35, 6: 115},  # Phase 2: Push back {5: 35, 6: 110}
        {5: 35, 6: 125},  # Phase 3: Lift leg
        {5: 65, 6: 120}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 80, 2: 45},   # Phase 1: Lower leg {1: 70, 2: 50}
        {1: 90, 2: 45},   # Phase 2: Push back {1: 90, 2: 50}
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 60, 2: 40}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 35, 14: 110},  # Phase 1: Lower leg {13: 57, 14: 105}
        {13: 25, 14: 110},  # Phase 2: Push back {13: 37, 14: 105}
        {13: 25, 14: 120}, # Phase 3: Lift leg
        {13: 55, 14: 115}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 93, 10: 45},  # Phase 1: Lower leg {9: 83, 10: 50}
        {9: 103, 10: 45},  # Phase 2: Push back {9: 103, 10: 50}
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 73, 10: 40}   # Phase 4: Move forward
    ]
}

# Turn right gait angles -> turn right 3
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
        {13: 40, 14: 100},  # Phase 1: Lower leg
        {13: 25, 14: 105},  # Phase 2: Push back
        {13: 25, 14: 120}, # Phase 3: Lift leg
        {13: 50, 14: 110}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 78, 10: 45},  # Phase 1: Lower leg
        {9: 103, 10: 50},  # Phase 2: Push back
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 68, 10: 35}   # Phase 4: Move forward
    ]
}

# Turn left gait angles -> turn left 3
turn_left_phases = {
    "front_right": [
        {5: 60, 6: 115},  # Phase 1: Lower leg 
        {5: 35, 6: 110},  # Phase 2: Push back
        {5: 35, 6: 125},  # Phase 3: Lift leg 
        {5: 70, 6: 125}   # Phase 4: Move forward
    ],
    "front_left": [
        {1: 75, 2: 55},   # Phase 1: Lower leg
        {1: 90, 2: 50},   # Phase 2: Push back
        {1: 90, 2: 35},  # Phase 3: Lift leg
        {1: 65, 2: 45}    # Phase 4: Move forward
    ],
    "rear_right": [
        {13: 62, 14: 110},  # Phase 1: Lower leg
        {13: 37, 14: 105},  # Phase 2: Push back
        {13: 37, 14: 120}, # Phase 3: Lift leg
        {13: 72, 14: 120}  # Phase 4: Move forward
    ],
    "rear_left": [
        {9: 88, 10: 55},  # Phase 1: Lower leg
        {9: 103, 10: 50},  # Phase 2: Push back
        {9: 103, 10: 35},  # Phase 3: Lift leg
        {9: 78, 10: 45}   # Phase 4: Move forward
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

def set_pose(target_angles, transition_time=1.0, steps=15, deactivate_after_move=False):
    global current_angles
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

def walk_trot(cycles=50):
    print("Starting trot walk...")
    if OBSTACLE_AVOIDANCE_ENABLED:
        print("🚨 Obstacle avoidance ENABLED - will execute avoidance sequence if obstacle detected")
        print(f"📏 Detection threshold: {OBSTACLE_DISTANCE_THRESHOLD}cm")
    else:
        print("⚠️ Obstacle avoidance DISABLED - robot will walk forward regardless of obstacles")
    
    set_pose(stand_angles, transition_time=0.015)

    for cycle in range(cycles):
        # Check for obstacles only if avoidance is enabled and cooldown period has passed
        if OBSTACLE_AVOIDANCE_ENABLED and can_react_to_obstacle():
            distance = get_distance()
            
            # Show distance every 10th cycle for debugging
            if cycle % 10 == 0:
                if distance == -1:
                    print(f"Cycle {cycle}: Sensor timeout")
                else:
                    status = "🚨 OBSTACLE!" if distance <= OBSTACLE_DISTANCE_THRESHOLD else "✅ Clear"
                    print(f"Cycle {cycle}: {distance:.1f}cm | {status}")
            
            if distance != -1 and distance <= OBSTACLE_DISTANCE_THRESHOLD:
                print(f"🚨 Obstacle detected at {distance:.1f}cm!")
                execute_obstacle_avoidance_sequence(distance)
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

            set_pose(angles, transition_time=0.015)

    set_pose(stand_angles, transition_time=0.015)
    print("Trot walk complete.")

def turn_right(cycles=30):
    print("Starting right turn...")
    
    set_pose(stand_angles, transition_time=0.015)

    for cycle in range(cycles):
        for phase_idx in range(4):
            # Diagonal pairs: FR-RL and FL-RR with 2 phase difference
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4

            angles = stand_angles.copy()
            angles.update(turn_right_phases["front_right"][fr_rl])
            angles.update(turn_right_phases["rear_left"][fr_rl])
            angles.update(turn_right_phases["front_left"][fl_rr])
            angles.update(turn_right_phases["rear_right"][fl_rr])

            set_pose(angles, transition_time=0.015)

    set_pose(stand_angles, transition_time=0.015)
    print("Right turn complete.")

def turn_left(cycles=30):
    print("Starting left turn...")
    
    set_pose(stand_angles, transition_time=0.015)

    for cycle in range(cycles):
        for phase_idx in range(4):
            # Diagonal pairs: FR-RL and FL-RR with 2 phase difference
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4

            angles = stand_angles.copy()
            angles.update(turn_left_phases["front_right"][fr_rl])
            angles.update(turn_left_phases["rear_left"][fr_rl])
            angles.update(turn_left_phases["front_left"][fl_rr])
            angles.update(turn_left_phases["rear_right"][fl_rr])

            set_pose(angles, transition_time=0.015)

    set_pose(stand_angles, transition_time=0.015)
    print("Left turn complete.")

# Initialize current angles
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}

# Initialize ultrasonic sensor
setup_ultrasonic()

# Main program
print("Quadruped Robot: Straight / Stand / Sit / Walk / Turn Right / Turn Left / Distance / Monitor / Quit")
avoidance_status = "🚨 ENABLED" if OBSTACLE_AVOIDANCE_ENABLED else "⚠️ DISABLED"
print(f"🤖 Obstacle avoidance: {avoidance_status}")
print(f"📏 Obstacle detection threshold: {OBSTACLE_DISTANCE_THRESHOLD}cm")
print(f"⏱️ Cooldown period between reactions: {OBSTACLE_COOLDOWN_TIME}s")
print(f"🔄 Avoidance sequence: R{STEP1_RIGHT_CYCLES} → F(auto) → L{STEP3_LEFT_CYCLES} → F(auto) → R{STEP5_RIGHT_CYCLES}")
print("📐 Forward cycles auto-calculated: <10cm=1, <20cm=2, <30cm=3, ≤40cm=4")
print("⚠️ No reaction to obstacles >40cm")
print("🔧 Use 'config' command to adjust parameters")
print("🔍 Use 'monitor' command for continuous distance monitoring")

try:
    while True:
        cmd = input("Enter mode (straight/stand/sit/walk/right/left/distance/monitor/config/toggle/q): ").strip().lower()
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
            avoidance_choice = input("Enable obstacle avoidance for this walk? (y/n, default=y): ").strip().lower()
            temp_avoidance_enabled = avoidance_choice != 'n'
            
            # Temporarily store the global setting
            original_setting = OBSTACLE_AVOIDANCE_ENABLED
            OBSTACLE_AVOIDANCE_ENABLED = temp_avoidance_enabled
            
            print("🚶 Starting forward walk...")
            walk_trot(cycles=50)
            
            # Restore the original setting
            OBSTACLE_AVOIDANCE_ENABLED = original_setting
            input("Walk finished. Press Enter to continue.")
        elif cmd == 'right':
            print("↩️ Starting right turn...")
            turn_right(cycles=30)
            input("Right turn finished. Press Enter to continue.")
        elif cmd == 'left':
            print("↪️ Starting left turn...")
            turn_left(cycles=30)
            input("Left turn finished. Press Enter to continue.")
        elif cmd == 'distance':
            distance = get_distance()
            if distance == -1:
                print("Sensor timeout - check ultrasonic sensor connections")
            else:
                status = "🚨 OBSTACLE!" if distance <= OBSTACLE_DISTANCE_THRESHOLD else "✅ Clear"
                print(f"Distance: {distance:.2f} cm | {status}")
        elif cmd == 'monitor':
            print("🔍 Continuous distance monitoring mode - Press Ctrl+C to stop")
            print(f"📏 Threshold: {OBSTACLE_DISTANCE_THRESHOLD}cm")
            try:
                while True:
                    distance = get_distance()
                    if distance == -1:
                        print("⚠️ Sensor timeout", end='\r')
                    else:
                        status = "🚨 OBSTACLE!" if distance <= OBSTACLE_DISTANCE_THRESHOLD else "✅ Clear"
                        print(f"Distance: {distance:6.2f} cm | {status}    ", end='\r')
                    time.sleep(0.2)  # Update 5 times per second
            except KeyboardInterrupt:
                print("\n✅ Distance monitoring stopped")
        elif cmd == 'toggle':
            OBSTACLE_AVOIDANCE_ENABLED = not OBSTACLE_AVOIDANCE_ENABLED
            new_status = "🚨 ENABLED" if OBSTACLE_AVOIDANCE_ENABLED else "⚠️ DISABLED"
            print(f"✅ Obstacle avoidance toggled to: {new_status}")
        elif cmd == 'config':
            avoidance_status = "🚨 ENABLED" if OBSTACLE_AVOIDANCE_ENABLED else "⚠️ DISABLED"
            print(f"\nCurrent settings:")
            print(f"🤖 Obstacle avoidance: {avoidance_status}")
            print(f"📏 Obstacle distance threshold: {OBSTACLE_DISTANCE_THRESHOLD}cm")
            print(f"⏱️ Cooldown time: {OBSTACLE_COOLDOWN_TIME}s")
            print(f"\n🔄 Avoidance sequence cycles:")
            print(f"  Step 1 - Turn right: {STEP1_RIGHT_CYCLES} cycles")
            print(f"  Step 2 - Move forward: AUTO (distance-based)")
            print(f"  Step 3 - Turn left: {STEP3_LEFT_CYCLES} cycles")
            print(f"  Step 4 - Move forward: AUTO (distance-based)")
            print(f"  Step 5 - Turn right: {STEP5_RIGHT_CYCLES} cycles")
            print(f"  📐 Forward cycle rules: <10cm=1, <20cm=2, <30cm=3, ≤40cm=4")
            print(f"  ⚠️ No reaction to obstacles >40cm")
            
            config_choice = input("\nWhat to configure? (0=enable/disable, 1=distance/cooldown, 2=cycles, Enter=exit): ").strip()
            
            if config_choice == '0':
                current_status = "enabled" if OBSTACLE_AVOIDANCE_ENABLED else "disabled"
                toggle_choice = input(f"Obstacle avoidance is currently {current_status}. Toggle? (y/n): ").strip().lower()
                if toggle_choice == 'y':
                    OBSTACLE_AVOIDANCE_ENABLED = not OBSTACLE_AVOIDANCE_ENABLED
                    new_status = "🚨 ENABLED" if OBSTACLE_AVOIDANCE_ENABLED else "⚠️ DISABLED"
                    print(f"✅ Obstacle avoidance is now {new_status}")
            
            elif config_choice == '1':
                try:
                    new_threshold = input(f"Enter new distance threshold (current: {OBSTACLE_DISTANCE_THRESHOLD}cm, press Enter to keep): ").strip()
                    if new_threshold:
                        OBSTACLE_DISTANCE_THRESHOLD = float(new_threshold)
                        print(f"✅ Distance threshold updated to {OBSTACLE_DISTANCE_THRESHOLD}cm")
                    
                    new_cooldown = input(f"Enter new cooldown time (current: {OBSTACLE_COOLDOWN_TIME}s, press Enter to keep): ").strip()
                    if new_cooldown:
                        OBSTACLE_COOLDOWN_TIME = float(new_cooldown)
                        print(f"✅ Cooldown time updated to {OBSTACLE_COOLDOWN_TIME}s")
                except ValueError:
                    print("❌ Invalid input. Settings unchanged.")
            
            elif config_choice == '2':
                try:
                    print("\n🔄 Configure avoidance sequence cycles:")
                    print("Note: Steps 2 & 4 (forward) are auto-calculated based on distance")
                    
                    step1 = input(f"Step 1 - Turn right cycles (current: {STEP1_RIGHT_CYCLES}, press Enter to keep): ").strip()
                    if step1:
                        STEP1_RIGHT_CYCLES = int(step1)
                        print(f"✅ Step 1 updated to {STEP1_RIGHT_CYCLES} cycles")
                    
                    step3 = input(f"Step 3 - Turn left cycles (current: {STEP3_LEFT_CYCLES}, press Enter to keep): ").strip()
                    if step3:
                        STEP3_LEFT_CYCLES = int(step3)
                        print(f"✅ Step 3 updated to {STEP3_LEFT_CYCLES} cycles")
                    
                    step5 = input(f"Step 5 - Turn right cycles (current: {STEP5_RIGHT_CYCLES}, press Enter to keep): ").strip()
                    if step5:
                        STEP5_RIGHT_CYCLES = int(step5)
                        print(f"✅ Step 5 updated to {STEP5_RIGHT_CYCLES} cycles")
                    
                    print(f"\n🎯 New sequence: R{STEP1_RIGHT_CYCLES} → F(auto) → L{STEP3_LEFT_CYCLES} → F(auto) → R{STEP5_RIGHT_CYCLES}")
                    
                except ValueError:
                    print("❌ Invalid input. Cycle settings unchanged.")
        else:
            print("Invalid command. Use: straight/stand/sit/walk/right/left/distance/monitor/config/toggle/q")
finally:
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
