#!/usr/bin/env python3
"""
Test script for robotic dog walk with all 4 legs in the same phase.
This creates a gallop-style movement where all legs move together synchronously.
"""

import board
import busio
from adafruit_pca9685 import PCA9685
import time
import numpy as np

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

# Servo types and channels (from p12-7.py)
servo_types = {
    0: "270", 1: "270", 2: "270", 4: "270", 5: "270",
    6: "180", 8: "180", 9: "270", 10: "180", 12: "180",
    13: "270", 14: "180"
}

# Stand mode angles as baseline (from p12-7.py)
stand_angles = {
    0: 170, 1: 70, 2: 50,    # Front left leg
    4: 100, 5: 55, 6: 110,   # Front right leg  
    8: 150, 9: 83, 10: 50,   # Rear left leg
    12: 115, 13: 57, 14: 105 # Rear right leg
}

# Same-phase walking gait - all legs move together
# Based on the walking_phases from p12-7.py but synchronized
same_phase_walk = {
    "phase_1": {  # All legs on ground, ready to push
        1: 70, 2: 50,    # Front left: lower leg
        5: 55, 6: 110,   # Front right: lower leg
        9: 83, 10: 50,   # Rear left: lower leg
        13: 57, 14: 105  # Rear right: lower leg
    },
    "phase_2": {  # All legs push back
        1: 90, 2: 50,    # Front left: push back
        5: 35, 6: 110,   # Front right: push back
        9: 103, 10: 50,  # Rear left: push back
        13: 37, 14: 105  # Rear right: push back
    },
    "phase_3": {  # All legs lift up
        1: 90, 2: 35,    # Front left: lift leg
        5: 35, 6: 125,   # Front right: lift leg
        9: 103, 10: 35,  # Rear left: lift leg
        13: 37, 14: 120  # Rear right: lift leg
    },
    "phase_4": {  # All legs move forward
        1: 60, 2: 40,    # Front left: move forward
        5: 65, 6: 120,   # Front right: move forward
        9: 73, 10: 40,   # Rear left: move forward
        13: 67, 14: 115  # Rear right: move forward
    }
}

def angle_to_pwm(angle, servo_type):
    """Convert angle to PWM value based on servo type"""
    if servo_type == "180":
        min_angle, max_angle = 0, 180
    else:
        min_angle, max_angle = 0, 270
    min_pwm, max_pwm = 100, 500
    angle = max(min(angle, max_angle), min_angle)
    return int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))

def set_pose(target_angles, transition_time=0.3, steps=50):
    """Smoothly transition to target pose"""
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

def walk_same_phase(cycles=20, step_delay=0.1):
    """
    Execute walk with all 4 legs in the same phase
    
    Args:
        cycles (int): Number of complete walk cycles to perform
        step_delay (float): Delay between each phase step (seconds)
    """
    print(f"🚶 Starting same-phase walk for {cycles} cycles...")
    print("📝 All 4 legs will move synchronously in the same phase")
    
    # Start from standing position
    print("🏃 Moving to standing position...")
    set_pose(stand_angles, transition_time=0.5)
    time.sleep(0.5)
    
    print("🎯 Beginning same-phase walk pattern...")
    
    for cycle in range(cycles):
        print(f"📍 Cycle {cycle + 1}/{cycles}")
        
        # Phase 1: All legs ready position
        print("  Phase 1: All legs on ground")
        angles = stand_angles.copy()
        angles.update(same_phase_walk["phase_1"])
        set_pose(angles, transition_time=0.05)
        time.sleep(step_delay)
        
        # Phase 2: All legs push back
        print("  Phase 2: All legs push back")
        angles = stand_angles.copy()
        angles.update(same_phase_walk["phase_2"])
        set_pose(angles, transition_time=0.05)
        time.sleep(step_delay)
        
        # Phase 3: All legs lift up
        print("  Phase 3: All legs lift up")
        angles = stand_angles.copy()
        angles.update(same_phase_walk["phase_3"])
        set_pose(angles, transition_time=0.05)
        time.sleep(step_delay)
        
        # Phase 4: All legs move forward
        print("  Phase 4: All legs move forward")
        angles = stand_angles.copy()
        angles.update(same_phase_walk["phase_4"])
        set_pose(angles, transition_time=0.05)
        time.sleep(step_delay)
        
        print(f"  ✅ Cycle {cycle + 1} complete")
    
    # Return to standing position
    print("🏁 Returning to standing position...")
    set_pose(stand_angles, transition_time=0.5)
    time.sleep(0.5)
    
    print("✅ Same-phase walk test complete!")

def test_individual_phases():
    """Test each phase individually for debugging"""
    print("🔍 Testing individual phases...")
    
    # Start from standing position
    set_pose(stand_angles, transition_time=0.5)
    time.sleep(1)
    
    phases = ["phase_1", "phase_2", "phase_3", "phase_4"]
    
    for i, phase_name in enumerate(phases, 1):
        print(f"\n🎯 Testing {phase_name} (Phase {i})")
        input(f"Press Enter to execute {phase_name}...")
        
        angles = stand_angles.copy()
        angles.update(same_phase_walk[phase_name])
        set_pose(angles, transition_time=0.3)
        time.sleep(1)
        
        print(f"✅ {phase_name} executed")
    
    # Return to standing
    print("\n🏁 Returning to standing position...")
    set_pose(stand_angles, transition_time=0.5)
    print("✅ Individual phase testing complete!")

def display_leg_mapping():
    """Display the leg and servo mapping for reference"""
    print("\n📋 ROBOT LEG AND SERVO MAPPING:")
    print("=" * 40)
    print("Front Left Leg  (FL): Channels 0, 1, 2")
    print("  - Channel 0: Hip joint (270° servo)")
    print("  - Channel 1: Upper leg (270° servo)")
    print("  - Channel 2: Lower leg (270° servo)")
    print()
    print("Front Right Leg (FR): Channels 4, 5, 6")
    print("  - Channel 4: Hip joint (270° servo)")
    print("  - Channel 5: Upper leg (270° servo)")
    print("  - Channel 6: Lower leg (180° servo)")
    print()
    print("Rear Left Leg   (RL): Channels 8, 9, 10")
    print("  - Channel 8: Hip joint (180° servo)")
    print("  - Channel 9: Upper leg (270° servo)")
    print("  - Channel 10: Lower leg (180° servo)")
    print()
    print("Rear Right Leg  (RR): Channels 12, 13, 14")
    print("  - Channel 12: Hip joint (180° servo)")
    print("  - Channel 13: Upper leg (270° servo)")
    print("  - Channel 14: Lower leg (180° servo)")
    print("=" * 40)

# Initialize current angles
current_angles = {ch: (90 if servo_types[ch] == "180" else 135) for ch in servo_types}

def main():
    """Main test program"""
    print("🤖 ROBOTIC DOG - SAME PHASE WALK TEST")
    print("=" * 50)
    print("This script tests a walking gait where all 4 legs")
    print("move in the same phase (synchronous movement).")
    print("=" * 50)
    
    try:
        while True:
            print("\n🎮 AVAILABLE TESTS:")
            print("1. 'walk' - Execute same-phase walk (default: 20 cycles)")
            print("2. 'phase' - Test individual phases step-by-step")
            print("3. 'stand' - Move to standing position")
            print("4. 'info' - Display leg and servo mapping")
            print("5. 'custom' - Custom walk with specified cycles and delay")
            print("6. 'q' - Quit")
            
            cmd = input("\nEnter command: ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'walk':
                walk_same_phase()
            elif cmd == 'phase':
                test_individual_phases()
            elif cmd == 'stand':
                print("🏃 Moving to standing position...")
                set_pose(stand_angles, transition_time=0.5)
                print("✅ Standing position set")
            elif cmd == 'info':
                display_leg_mapping()
            elif cmd == 'custom':
                try:
                    cycles = int(input("Enter number of cycles (default 20): ") or "20")
                    delay = float(input("Enter step delay in seconds (default 0.1): ") or "0.1")
                    walk_same_phase(cycles=cycles, step_delay=delay)
                except ValueError:
                    print("❌ Invalid input. Please enter numbers only.")
            else:
                print("❌ Invalid command. Please try again.")
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    
    finally:
        print("\n🔄 Resetting all servos to neutral...")
        # Reset to neutral positions
        for channel, servo_type in servo_types.items():
            neutral_angle = 90 if servo_type == "180" else 135
            pwm_value = angle_to_pwm(neutral_angle, servo_type)
            pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
            time.sleep(0.01)
        
        time.sleep(0.5)
        
        # Turn off all PWM channels
        for i in range(16):
            pwm.channels[i].duty_cycle = 0
        
        pwm.deinit()
        print("✅ Shutdown complete - all servos reset and PWM disabled")

if __name__ == "__main__":
    main()
