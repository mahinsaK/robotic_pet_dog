#!/usr/bin/env python3
import board
import busio
from adafruit_pca9685 import PCA9685
import time
import os
import sys

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

# Servo configuration with names, specifications, and rotation directions
servo_config = {
    # Front Left Leg
    0: {"name": "FL Shoulder", "type": "270", "default": 200, "leg": "FL", "direction": "- outwards"},
    1: {"name": "FL Thigh", "type": "270", "default": 10, "leg": "FL", "direction": "+ backwards"},
    2: {"name": "FL Knee", "type": "270", "default": 145, "leg": "FL", "direction": "- bending"},
    
    # Front Right Leg
    4: {"name": "FR Shoulder", "type": "270", "default": 100, "leg": "FR", "direction": "+ outwards"},
    5: {"name": "FR Thigh", "type": "270", "default": 115, "leg": "FR", "direction": "- backwards"},
    6: {"name": "FR Knee", "type": "180", "default": 10, "leg": "FR", "direction": "+ bending"},
    
    # Rear Left Leg
    8: {"name": "RL Shoulder", "type": "180", "default": 150, "leg": "RL", "direction": "- outwards"},
    9: {"name": "RL Thigh", "type": "270", "default": 19, "leg": "RL", "direction": "+ backwards"},
    10: {"name": "RL Knee", "type": "180", "default": 150, "leg": "RL", "direction": "- bending"},
    
    # Rear Right Leg
    12: {"name": "RR Shoulder", "type": "180", "default": 120, "leg": "RR", "direction": "+ outwards"},
    13: {"name": "RR Thigh", "type": "270", "default": 110, "leg": "RR", "direction": "- backwards"},
    14: {"name": "RR Knee", "type": "180", "default": 5, "leg": "RR", "direction": "+ bending"}
}

# Current angles (initialize to default standing position)
current_angles = {ch: servo_config[ch]["default"] for ch in servo_config}

def angle_to_pwm(angle, servo_type):
    """Convert angle to PWM duty cycle value"""
    if servo_type == "180":
        min_angle, max_angle = 0, 180
    else:
        min_angle, max_angle = 0, 270
    min_pwm, max_pwm = 100, 500
    angle = max(min(angle, max_angle), min_angle)
    return int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))

def set_servo_angle(channel, angle):
    """Set a specific servo to a specific angle"""
    if channel not in servo_config:
        print(f"Error: Channel {channel} not configured")
        return False
    
    servo_type = servo_config[channel]["type"]
    max_angle = 180 if servo_type == "180" else 270
    
    # Validate angle range
    if angle < 0 or angle > max_angle:
        print(f"Error: Angle {angle} is out of range for {servo_config[channel]['name']} (0-{max_angle}°)")
        return False
    
    try:
        pwm_value = angle_to_pwm(angle, servo_type)
        pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
        current_angles[channel] = angle
        return True
    except Exception as e:
        print(f"Error setting servo {channel}: {e}")
        return False

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def display_servo_status():
    """Display current status of all servos organized by legs"""
    clear_screen()
    
    print("=" * 100)
    print("🤖 QUADRUPED ROBOT SERVO CONTROL INTERFACE 🤖")
    print("=" * 100)
    print()
    
    # Display rotation direction legend first
    print("🔄 ROTATION DIRECTIONS:")
    print("   + = Angle increasing | - = Angle decreasing")
    print()
    
    # Organize legs in a 2x2 grid layout
    legs = ["FL", "FR", "RL", "RR"]
    leg_names = {
        "FL": "Front Left",
        "FR": "Front Right", 
        "RL": "Rear Left",
        "RR": "Rear Right"
    }
    
    # Top row: FL and FR
    print("┌───────────────────────────────────────────────────────┬───────────────────────────────────────────────────────┐")
    
    for row in [["FL", "FR"], ["RL", "RR"]]:
        for i, leg in enumerate(row):
            if i == 0:
                print("│", end="")
            else:
                print("│", end="")
            
            print(f" {leg_names[leg]:^55} ", end="")
            if i == 1:
                print("│")
        
        # Print servo details for this row
        max_servos = max(len([ch for ch in servo_config if servo_config[ch]["leg"] == leg]) for leg in row)
        
        for servo_idx in range(max_servos):
            print("│", end="")
            for i, leg in enumerate(row):
                leg_servos = [ch for ch in servo_config if servo_config[ch]["leg"] == leg]
                leg_servos.sort()
                
                if servo_idx < len(leg_servos):
                    ch = leg_servos[servo_idx]
                    config = servo_config[ch]
                    current = current_angles[ch]
                    default = config["default"]
                    max_angle = 180 if config["type"] == "180" else 270
                    direction = config["direction"]
                    
                    # Color coding for current vs default
                    if current == default:
                        status = "✅"
                    elif abs(current - default) <= 5:
                        status = "🟡"
                    else:
                        status = "🔴"
                    
                    # Format the servo information
                    servo_line = f" {status} Ch{ch:2d} {config['name']:12s} {direction:13s}"
                    angle_line = f"    Cur:{current:3d}° Def:{default:3d}° Max:{max_angle:3d}°"
                    combined_line = f"{servo_line} {angle_line}"
                    
                    print(f"{combined_line:<55} ", end="")
                else:
                    print(" " * 56, end="")
                
                if i == 1:
                    print("│")
        
        if row == ["FL", "FR"]:
            print("├───────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┤")
        else:
            print("└───────────────────────────────────────────────────────┴───────────────────────────────────────────────────────┘")
    
    print()
    print("Legend: ✅ Default position | 🟡 Close to default (±5°) | 🔴 Away from default")
    print()

def reset_to_standing():
    """Reset all servos to standing position"""
    print("🏠 Resetting to standing position...")
    for channel in servo_config:
        default_angle = servo_config[channel]["default"]
        set_servo_angle(channel, default_angle)
        time.sleep(0.05)  # Small delay between servo movements
    print("✅ Standing position set!")

def set_all_servos_to_angle():
    """Set all servos to the same angle"""
    try:
        angle = int(input("Enter angle for all servos (will respect individual max limits): "))
        
        print("Setting all servos...")
        for channel in servo_config:
            max_angle = 180 if servo_config[channel]["type"] == "180" else 270
            safe_angle = min(max(angle, 0), max_angle)
            
            if safe_angle != angle:
                print(f"⚠️  {servo_config[channel]['name']}: Adjusted to {safe_angle}° (max: {max_angle}°)")
            
            set_servo_angle(channel, safe_angle)
            time.sleep(0.05)
        
        print("✅ All servos set!")
        
    except ValueError:
        print("❌ Invalid angle. Please enter a number.")

def show_rotation_directions():
    """Display detailed rotation direction information"""
    clear_screen()
    
    print("=" * 80)
    print("🔄 SERVO ROTATION DIRECTIONS REFERENCE")
    print("=" * 80)
    print()
    print("📖 Understanding the rotation directions:")
    print("   + (Plus)  = Angle INCREASING causes this movement")
    print("   - (Minus) = Angle DECREASING causes this movement")
    print()
    
    # Group by legs for better readability
    legs = ["FL", "FR", "RL", "RR"]
    leg_names = {
        "FL": "🦵 Front Left Leg",
        "FR": "🦵 Front Right Leg", 
        "RL": "🦵 Rear Left Leg",
        "RR": "🦵 Rear Right Leg"
    }
    
    for leg in legs:
        print(f"{leg_names[leg]}:")
        leg_servos = [ch for ch in servo_config if servo_config[ch]["leg"] == leg]
        leg_servos.sort()
        
        for ch in leg_servos:
            config = servo_config[ch]
            direction = config["direction"]
            max_angle = 180 if config["type"] == "180" else 270
            
            print(f"   Ch{ch:2d} {config['name']:12s} → {direction:15s} (0-{max_angle}°)")
        print()
    
    print("💡 Tips:")
    print("   • Start with small angle changes (±10°) to see the movement")
    print("   • Use the 'stand' command to return to safe default position")
    print("   • Each servo has different angle limits (180° or 270°)")
    print()

def interactive_servo_control():
    """Main interactive control loop"""
    
    while True:
        display_servo_status()
        
        print("📋 CONTROL OPTIONS:")
        print("1. Set individual servo (enter channel number: 0-14)")
        print("2. Reset to standing position (type: 'stand')")
        print("3. Set all servos to same angle (type: 'all')")
        print("4. Show rotation directions (type: 'help')")
        print("5. Quit (type: 'q')")
        print()
        
        cmd = input("Enter command: ").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd == 'stand':
            reset_to_standing()
            input("Press Enter to continue...")
        elif cmd == 'all':
            set_all_servos_to_angle()
            input("Press Enter to continue...")
        elif cmd == 'help':
            show_rotation_directions()
            input("Press Enter to continue...")
        else:
            try:
                channel = int(cmd)
                if channel in servo_config:
                    config = servo_config[channel]
                    max_angle = 180 if config["type"] == "180" else 270
                    current = current_angles[channel]
                    direction = config["direction"]
                    
                    print(f"\n🎯 Controlling: {config['name']} (Channel {channel})")
                    print(f"   Current: {current}° | Default: {config['default']}° | Max: {max_angle}°")
                    print(f"   Direction: {direction}")
                    
                    try:
                        new_angle = int(input(f"Enter new angle (0-{max_angle}): "))
                        if set_servo_angle(channel, new_angle):
                            print(f"✅ {config['name']} set to {new_angle}°")
                        input("Press Enter to continue...")
                    except ValueError:
                        print("❌ Invalid angle. Please enter a number.")
                        input("Press Enter to continue...")
                else:
                    print(f"❌ Invalid channel. Available channels: {', '.join(map(str, sorted(servo_config.keys())))}")
                    input("Press Enter to continue...")
            except ValueError:
                print("❌ Invalid command. Use channel number, 'stand', 'all', or 'q'")
                input("Press Enter to continue...")

def main():
    """Main program"""
    print("🤖 Initializing Quadruped Robot Servo Control...")
    
    # Initialize servos to standing position
    reset_to_standing()
    time.sleep(1)
    
    try:
        interactive_servo_control()
    except KeyboardInterrupt:
        print("\n\n🛑 Program interrupted by user")
    finally:
        print("\n🔧 Cleaning up...")
        # Stop all servos
        for i in range(16):
            pwm.channels[i].duty_cycle = 0
        pwm.deinit()
        print("✅ Cleanup complete. Goodbye!")

if __name__ == "__main__":
    main()
