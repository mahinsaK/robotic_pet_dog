#!/usr/bin/env python3
"""
Pet Robot Controller for Raspberry Pi 4 with DS3240 servos and PCA9685 driver
Supports: straight, stand, sit, walk, turn_right, turn_left modes
"""

import time
import threading
from adafruit_servokit import ServoKit

class PetRobotController:
    def __init__(self):
        # Initialize PCA9685 servo driver
        self.kit = ServoKit(channels=16)
        
        # Servo channel mapping
        self.servo_channels = {
            # Front Left leg
            'FL_shoulder': 0,  # 270 degree servo
            'FL_thigh': 1,     # 270 degree servo
            'FL_knee': 2,      # 270 degree servo
            
            # Front Right leg
            'FR_shoulder': 4,  # 270 degree servo
            'FR_thigh': 5,     # 270 degree servo
            'FR_knee': 6,      # 180 degree servo
            
            # Rear Left leg
            'RL_shoulder': 8,  # 180 degree servo
            'RL_thigh': 9,     # 270 degree servo
            'RL_knee': 10,     # 180 degree servo
            
            # Rear Right leg
            'RR_shoulder': 12, # 180 degree servo
            'RR_thigh': 13,    # 270 degree servo
            'RR_knee': 14      # 180 degree servo
        }
        
        # Position definitions for each mode
        self.straight_angles = {
            0: 170, 1: 10, 2: 150,    # FL
            4: 100, 5: 115, 6: 10,    # FR
            8: 150, 9: 23, 10: 150,   # RL
            12: 115, 13: 117, 14: 5   # RR
        }
        
        self.stand_angles = {
            0: 170, 1: 70, 2: 50,     # FL
            4: 100, 5: 55, 6: 110,    # FR
            8: 150, 9: 83, 10: 50,    # RL
            12: 115, 13: 57, 14: 105  # RR
        }
        
        self.sit_angles = {
            0: 170, 1: 110, 2: 10,    # FL
            4: 100, 5: 15, 6: 150,    # FR
            8: 150, 9: 123, 10: 10,   # RL
            12: 115, 13: 17, 14: 145  # RR
        }
        
        # Walking phases for forward movement
        self.walking_phases = {
            "front_right": [
                {5: 55, 6: 110},  # Phase 1: Lower leg 
                {5: 35, 6: 110},  # Phase 2: Push back
                {5: 35, 6: 125},  # Phase 3: Lift leg 
                {5: 65, 6: 120}   # Phase 4: Move forward
            ],
            "front_left": [
                {1: 70, 2: 50},   # Phase 1: Lower leg
                {1: 90, 2: 50},   # Phase 2: Push back
                {1: 90, 2: 35},   # Phase 3: Lift leg
                {1: 60, 2: 40}    # Phase 4: Move forward
            ],
            "rear_right": [
                {13: 57, 14: 105},  # Phase 1: Lower leg
                {13: 37, 14: 105},  # Phase 2: Push back
                {13: 37, 14: 120},  # Phase 3: Lift leg
                {13: 67, 14: 115}   # Phase 4: Move forward
            ],
            "rear_left": [
                {9: 83, 10: 50},  # Phase 1: Lower leg
                {9: 103, 10: 50}, # Phase 2: Push back
                {9: 103, 10: 35}, # Phase 3: Lift leg
                {9: 73, 10: 40}   # Phase 4: Move forward
            ]
        }
        
        # Turn right phases
        self.turn_right_phases = {
            "front_right": [
                {5: 40, 6: 100},  # Phase 1: Lower leg 
                {5: 35, 6: 110},  # Phase 2: Push back
                {5: 35, 6: 125},  # Phase 3: Lift leg
                {5: 50, 6: 110}   # Phase 4: Move forward
            ],
            "front_left": [
                {1: 55, 2: 40},   # Phase 1: Lower leg
                {1: 90, 2: 50},   # Phase 2: Push back
                {1: 90, 2: 35},   # Phase 3: Lift leg
                {1: 45, 2: 30}    # Phase 4: Move forward
            ],
            "rear_right": [
                {13: 42, 14: 95},  # Phase 1: Lower leg
                {13: 37, 14: 105}, # Phase 2: Push back
                {13: 37, 14: 120}, # Phase 3: Lift leg
                {13: 52, 14: 105}  # Phase 4: Move forward
            ],
            "rear_left": [
                {9: 67, 10: 40},  # Phase 1: Lower leg
                {9: 103, 10: 50}, # Phase 2: Push back
                {9: 103, 10: 35}, # Phase 3: Lift leg
                {9: 58, 10: 30}   # Phase 4: Move forward
            ]
        }
        
        # Turn left phases
        self.turn_left_phases = {
            "front_right": [
                {5: 70, 6: 120},  # Phase 1: Lower leg 
                {5: 35, 6: 110},  # Phase 2: Push back
                {5: 35, 6: 125},  # Phase 3: Lift leg 
                {5: 80, 6: 130}   # Phase 4: Move forward
            ],
            "front_left": [
                {1: 85, 2: 60},   # Phase 1: Lower leg
                {1: 90, 2: 50},   # Phase 2: Push back
                {1: 90, 2: 35},   # Phase 3: Lift leg
                {1: 75, 2: 50}    # Phase 4: Move forward
            ],
            "rear_right": [
                {13: 72, 14: 115}, # Phase 1: Lower leg
                {13: 37, 14: 105}, # Phase 2: Push back
                {13: 37, 14: 120}, # Phase 3: Lift leg
                {13: 82, 14: 125}  # Phase 4: Move forward
            ],
            "rear_left": [
                {9: 98, 10: 60},  # Phase 1: Lower leg
                {9: 103, 10: 50}, # Phase 2: Push back
                {9: 103, 10: 35}, # Phase 3: Lift leg
                {9: 88, 10: 50}   # Phase 4: Move forward
            ]
        }
        
        # Current mode and state
        self.current_mode = "stand"
        self.is_walking = False
        self.walking_thread = None
        
        # Initialize robot to stand position
        print("Initializing robot to stand position...")
        self.set_position_mode("stand")
    
    def set_servo_angle(self, channel, angle):
        """Set servo angle with safety checks"""
        try:
            # Clamp angle to valid range
            angle = max(0, min(180, angle))
            self.kit.servo[channel].angle = angle
            time.sleep(0.01)  # Small delay for servo movement
        except Exception as e:
            print(f"Error setting servo {channel} to {angle}: {e}")
    
    def set_multiple_servos(self, servo_dict, smooth=True):
        """Set multiple servos simultaneously"""
        if smooth:
            # Smooth transition by interpolating between current and target positions
            steps = 20
            current_angles = {}
            
            # Get current angles (approximate - use stand position as reference)
            for channel in servo_dict.keys():
                current_angles[channel] = self.stand_angles.get(channel, 90)
            
            # Interpolate and move
            for step in range(steps + 1):
                for channel, target_angle in servo_dict.items():
                    current = current_angles[channel]
                    interpolated = current + (target_angle - current) * (step / steps)
                    self.set_servo_angle(channel, interpolated)
                time.sleep(0.02)
        else:
            # Direct movement
            for channel, angle in servo_dict.items():
                self.set_servo_angle(channel, angle)
    
    def set_position_mode(self, mode):
        """Set robot to a specific position mode"""
        self.stop_walking()  # Stop any walking motion
        
        if mode == "straight":
            print("Setting robot to STRAIGHT position")
            self.set_multiple_servos(self.straight_angles)
        elif mode == "stand":
            print("Setting robot to STAND position")
            self.set_multiple_servos(self.stand_angles)
        elif mode == "sit":
            print("Setting robot to SIT position")
            self.set_multiple_servos(self.sit_angles)
        else:
            print(f"Unknown position mode: {mode}")
            return
        
        self.current_mode = mode
        print(f"Robot is now in {mode.upper()} position")
    
    def execute_walking_cycle(self, phases, cycle_duration=2.0):
        """Execute one complete walking cycle with proper diagonal coordination"""
        phase_duration = cycle_duration / 4
        
        # Diagonal pairs: FR+RL and FL+RR
        # FR+RL start at phase 0, FL+RR start at phase 2 (2-phase offset)
        
        for phase in range(4):
            if not self.is_walking:
                break
                
            # Calculate phases for each diagonal pair
            fr_rl_phase = phase
            fl_rr_phase = (phase + 2) % 4
            
            # Combine angles for this step
            step_angles = {}
            
            # Front Right + Rear Left (diagonal pair 1)
            step_angles.update(phases["front_right"][fr_rl_phase])
            step_angles.update(phases["rear_left"][fr_rl_phase])
            
            # Front Left + Rear Right (diagonal pair 2)
            step_angles.update(phases["front_left"][fl_rr_phase])
            step_angles.update(phases["rear_right"][fl_rr_phase])
            
            # Apply shoulder positions from stand_angles (keep shoulders stable)
            step_angles.update({
                0: self.stand_angles[0],   # FL shoulder
                4: self.stand_angles[4],   # FR shoulder
                8: self.stand_angles[8],   # RL shoulder
                12: self.stand_angles[12]  # RR shoulder
            })
            
            print(f"Walking phase {phase + 1}/4 - FR+RL: phase {fr_rl_phase + 1}, FL+RR: phase {fl_rr_phase + 1}")
            self.set_multiple_servos(step_angles, smooth=False)
            time.sleep(phase_duration)
    
    def start_walking(self, direction="forward"):
        """Start walking in specified direction"""
        if self.is_walking:
            print("Already walking")
            return
        
        self.is_walking = True
        
        # Select appropriate phase set
        if direction == "forward":
            phases = self.walking_phases
            print("Starting FORWARD walk")
        elif direction == "turn_right":
            phases = self.turn_right_phases
            print("Starting TURN RIGHT")
        elif direction == "turn_left":
            phases = self.turn_left_phases
            print("Starting TURN LEFT")
        else:
            print(f"Unknown walking direction: {direction}")
            self.is_walking = False
            return
        
        def walk_loop():
            while self.is_walking:
                self.execute_walking_cycle(phases, cycle_duration=2.0)
        
        self.walking_thread = threading.Thread(target=walk_loop)
        self.walking_thread.daemon = True
        self.walking_thread.start()
        
        self.current_mode = f"walking_{direction}"
    
    def stop_walking(self):
        """Stop walking and return to stand position"""
        if self.is_walking:
            print("Stopping walk")
            self.is_walking = False
            if self.walking_thread:
                self.walking_thread.join(timeout=3.0)
            time.sleep(0.5)
            # Return to stand position
            print("Returning to stand position")
            self.set_multiple_servos(self.stand_angles, smooth=True)
            self.current_mode = "stand"
    
    def walk_forward(self, duration=None):
        """Walk forward for specified duration (None = indefinite)"""
        self.start_walking("forward")
        if duration:
            time.sleep(duration)
            self.stop_walking()
    
    def turn_right(self, duration=None):
        """Turn right for specified duration (None = indefinite)"""
        self.start_walking("turn_right")
        if duration:
            time.sleep(duration)
            self.stop_walking()
    
    def turn_left(self, duration=None):
        """Turn left for specified duration (None = indefinite)"""
        self.start_walking("turn_left")
        if duration:
            time.sleep(duration)
            self.stop_walking()
    
    def get_status(self):
        """Get current robot status"""
        return {
            "mode": self.current_mode,
            "is_walking": self.is_walking
        }
    
    def emergency_stop(self):
        """Emergency stop - immediately stop all movement"""
        print("EMERGENCY STOP")
        self.is_walking = False
        if self.walking_thread:
            self.walking_thread.join(timeout=1.0)


def main():
    """Main function for testing the robot controller"""
    print("="*60)
    print("Pet Robot Controller - DS3240 Servos with PCA9685")
    print("="*60)
    print("Initializing...")
    
    try:
        robot = PetRobotController()
        
        while True:
            print("\n" + "="*50)
            print("Pet Robot Controller Menu")
            print("="*50)
            print("Static Positions:")
            print("  1. Straight position")
            print("  2. Stand position")
            print("  3. Sit position")
            print("\nTimed Actions:")
            print("  4. Walk forward (5 seconds)")
            print("  5. Turn right (3 seconds)")
            print("  6. Turn left (3 seconds)")
            print("\nContinuous Actions:")
            print("  7. Start continuous walk forward")
            print("  8. Start continuous turn right")
            print("  9. Start continuous turn left")
            print("  10. Stop walking")
            print("\nInfo:")
            print("  11. Get status")
            print("  0. Exit")
            print("-"*50)
            
            choice = input("Enter your choice (0-11): ").strip()
            
            if choice == "1":
                robot.set_position_mode("straight")
            elif choice == "2":
                robot.set_position_mode("stand")
            elif choice == "3":
                robot.set_position_mode("sit")
            elif choice == "4":
                print("Walking forward for 5 seconds...")
                robot.walk_forward(5)
            elif choice == "5":
                print("Turning right for 3 seconds...")
                robot.turn_right(3)
            elif choice == "6":
                print("Turning left for 3 seconds...")
                robot.turn_left(3)
            elif choice == "7":
                robot.start_walking("forward")
            elif choice == "8":
                robot.start_walking("turn_right")
            elif choice == "9":
                robot.start_walking("turn_left")
            elif choice == "10":
                robot.stop_walking()
            elif choice == "11":
                status = robot.get_status()
                print(f"Current mode: {status['mode']}")
                print(f"Is walking: {status['is_walking']}")
            elif choice == "0":
                print("Shutting down robot...")
                robot.emergency_stop()
                break
            else:
                print("Invalid choice. Please try again.")
                
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down...")
        if 'robot' in locals():
            robot.emergency_stop()
    except Exception as e:
        print(f"Error: {e}")
        if 'robot' in locals():
            robot.emergency_stop()


if __name__ == "__main__":
    main()