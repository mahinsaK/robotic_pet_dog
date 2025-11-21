import numpy as np
import time
from kinematics import Kinematics

# Import servo control libraries
try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    SERVO_AVAILABLE = True
except ImportError:
    print("Warning: Servo control libraries not available. Running in simulation mode.")
    SERVO_AVAILABLE = False


class SpotMicroController:
    def __init__(self, enable_servos=True):
        """
        Initialize the Spot Micro controller with kinematics solver
        
        Args:
            enable_servos: Whether to enable actual servo control (default: True)
        """
        self.kinematics = Kinematics()
        
        # Servo control setup
        self.enable_servos = enable_servos and SERVO_AVAILABLE
        self.pwm = None
        
        if self.enable_servos:
            try:
                # Initialize I2C bus and PCA9685
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pwm = PCA9685(i2c)
                self.pwm.frequency = 50  # 50 Hz for servos
                
                # Clear all PWM outputs at startup
                for i in range(16):
                    self.pwm.channels[i].duty_cycle = 0
                    
                print("Servo control initialized successfully!")
                
            except Exception as e:
                print(f"Failed to initialize servo control: {e}")
                print("Running in simulation mode.")
                self.enable_servos = False
        else:
            print("Running in simulation mode (no servo control).")
        
        # Servo channel mapping (matching the balance control files)
        self.servo_channels = {
            'FL': [0, 1, 2],    # FL_shoulder, FL_thigh, FL_knee
            'FR': [4, 5, 6],    # FR_shoulder, FR_thigh, FR_knee  
            'RL': [8, 9, 10],   # RL_shoulder, RL_thigh, RL_knee
            'RR': [12, 13, 14]  # RR_shoulder, RR_thigh, RR_knee
        }
        
        # Servo types: True for 180° servos, False for 270° servos
        self.servo_types = {
            0: False, 1: False, 2: False,    # FL: 270°, 270°, 270°
            4: False, 5: False, 6: True,     # FR: 270°, 270°, 180°
            8: False, 9: False, 10: True,    # RL: 270°, 270°, 180°
            12: True, 13: False, 14: True    # RR: 180°, 270°, 180°
        }
        
        # Default servo positions (neutral/home position)
        self.standing_angles = {
            0: 200, 1: 10, 2: 145,
            4: 100, 5: 115, 6: 10,
            8: 150, 9: 19, 10: 150,
            12: 120, 13: 110, 14: 5
        }
        self.sitting_angles = {
            0: 207, 1: 70, 2: 50,
            4: 90, 5: 55, 6: 110,
            8: 150, 9: 79, 10: 50,
            12: 115, 13: 45, 14: 105
        }
        self.default_servo_angles = self.sitting_angles.copy()
        # For reset/home, use sitting pose
        
        # Current robot state
        self.current_position = np.array([0.0, 0.0, 0.0])  # x, y, z
        self.current_orientation = np.array([0.0, 0.0, 0.0])  # roll, pitch, yaw
        
        # Default standing position for feet (relative to body center)
        self.default_foot_positions = np.array([
            [0.115, -0.0925, -0.2],   # front right
            [0.115, 0.0925, -0.2],    # front left  
            [-0.115, -0.0925, -0.2],  # rear right
            [-0.115, 0.0925, -0.2]    # rear left
        ])
        
        # Current foot positions
        self.current_foot_positions = self.default_foot_positions.copy()
        
        # Movement limits for safety
        self.max_step_size = 0.05  # 5cm max step
        self.min_height = -0.25    # minimum foot height
        self.max_height = -0.1     # maximum foot height
        
    def angle_to_pwm(self, angle, is_180_servo):
        """Convert angle to PWM value based on servo type"""
        if is_180_servo:
            min_angle, max_angle = 0, 180
        else:
            min_angle, max_angle = 0, 270
            
        min_pwm, max_pwm = 100, 500
        
        # Clamp angle to valid range
        angle = max(min(angle, max_angle), min_angle)
        pwm_value = int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))
        return pwm_value
    
    def set_servo_angle(self, channel, angle):
        """Set servo to specified angle"""
        if not self.enable_servos or channel not in self.servo_types:
            return
            
        is_180_servo = self.servo_types[channel]
        max_angle = 180 if is_180_servo else 270
        
        # Clamp angle to servo limits
        angle = max(0, min(angle, max_angle))
        
        try:
            pwm_value = self.angle_to_pwm(angle, is_180_servo)
            self.pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
        except Exception as e:
            print(f"Error setting servo {channel} to {angle}°: {e}")
    
    def send_to_servos(self, fr_angles, fl_angles, rr_angles, rl_angles):
        """Send joint angles to physical servos"""
        if not self.enable_servos:
            return
            
        # Convert radians to degrees
        fr_deg = np.degrees(fr_angles).flatten()
        fl_deg = np.degrees(fl_angles).flatten()
        rr_deg = np.degrees(rr_angles).flatten()
        rl_deg = np.degrees(rl_angles).flatten()
        
        # Map joint angles to servo channels and apply offsets
        # Note: You may need to adjust these mappings and offsets based on your robot's configuration
        try:
            # Front Right leg: [hip, shoulder, knee]
            if len(fr_deg) >= 3:
                self.set_servo_angle(4, self.default_servo_angles[4] + fr_deg[0])  # FR shoulder
                self.set_servo_angle(5, self.default_servo_angles[5] + fr_deg[1])  # FR thigh  
                self.set_servo_angle(6, self.default_servo_angles[6] + fr_deg[2])  # FR knee
            
            # Front Left leg: [hip, shoulder, knee]
            if len(fl_deg) >= 3:
                self.set_servo_angle(0, self.default_servo_angles[0] - fl_deg[0])  # FL shoulder (mirrored)
                self.set_servo_angle(1, self.default_servo_angles[1] - fl_deg[1])  # FL thigh (mirrored)
                self.set_servo_angle(2, self.default_servo_angles[2] - fl_deg[2])  # FL knee (mirrored)
            
            # Rear Right leg: [hip, shoulder, knee]  
            if len(rr_deg) >= 3:
                self.set_servo_angle(12, self.default_servo_angles[12] - rr_deg[0])  # RR shoulder
                self.set_servo_angle(13, self.default_servo_angles[13] - rr_deg[1])  # RR thigh
                self.set_servo_angle(14, self.default_servo_angles[14] - rr_deg[2])  # RR knee
            
            # Rear Left leg: [hip, shoulder, knee]
            if len(rl_deg) >= 3:
                self.set_servo_angle(8, self.default_servo_angles[8] + rl_deg[0])   # RL shoulder  
                self.set_servo_angle(9, self.default_servo_angles[9] + rl_deg[1])   # RL thigh
                self.set_servo_angle(10, self.default_servo_angles[10] + rl_deg[2]) # RL knee
                
        except Exception as e:
            print(f"Error sending angles to servos: {e}")
    
    def reset_servos_to_home(self):
        """Reset all servos to their home/neutral positions (sitting pose)"""
        if not self.enable_servos:
            return
        print("Resetting servos to home position (sitting)...")
        for channel, angle in self.sitting_angles.items():
            self.set_servo_angle(channel, angle)
            time.sleep(0.05)
        
    def set_pose(self, pose='stand'):
        """
        Set the robot to a named pose: 'stand' or 'sit'
        """
        if not self.enable_servos:
            print(f"Simulated pose: {pose}")
            return
        if pose == 'stand':
            print("Moving to standing mode...")
            for channel, angle in self.standing_angles.items():
                self.set_servo_angle(channel, angle)
                time.sleep(0.05)
        elif pose == 'sit':
            print("Moving to sitting mode...")
            for channel, angle in self.sitting_angles.items():
                self.set_servo_angle(channel, angle)
                time.sleep(0.05)
        else:
            print(f"Unknown pose: {pose}")
    
    def set_body_pose(self, position=None, orientation=None):
        """
        Set the body position and orientation
        
        Args:
            position: [x, y, z] body position in meters
            orientation: [roll, pitch, yaw] body orientation in radians
        """
        if position is not None:
            self.current_position = np.array(position)
            
        if orientation is not None:
            self.current_orientation = np.array(orientation)
            
        print(f"Body pose set - Position: {self.current_position}, Orientation: {self.current_orientation}")
    
    def move_single_leg(self, leg_index, target_position):
        """
        Move a single leg to target position
        
        Args:
            leg_index: 0=front_right, 1=front_left, 2=rear_right, 3=rear_left
            target_position: [x, y, z] target foot position relative to body
        """
        leg_names = ["Front Right", "Front Left", "Rear Right", "Rear Left"]
        
        # Safety checks
        target_position = np.array(target_position)
        
        # Limit step size
        current_pos = self.current_foot_positions[leg_index]
        step_vector = target_position - current_pos
        step_size = np.linalg.norm(step_vector)
        
        if step_size > self.max_step_size:
            # Scale down the step
            step_vector = step_vector * (self.max_step_size / step_size)
            target_position = current_pos + step_vector
            print(f"Step size limited for {leg_names[leg_index]}")
        
        # Limit height
        if target_position[2] < self.min_height:
            target_position[2] = self.min_height
        elif target_position[2] > self.max_height:
            target_position[2] = self.max_height
            
        # Update foot position
        self.current_foot_positions[leg_index] = target_position
        
        print(f"{leg_names[leg_index]} leg moved to: {target_position}")
        
    def move_all_legs(self, target_positions):
        """
        Move all legs to target positions
        
        Args:
            target_positions: 4x3 array of [x, y, z] positions for each leg
        """
        for i, target_pos in enumerate(target_positions):
            self.move_single_leg(i, target_pos)
    
    def calculate_joint_angles(self):
        """
        Calculate joint angles for current foot positions and body pose
        
        Returns:
            Tuple of (front_right, front_left, rear_right, rear_left) joint angles
        """
        try:
            # Create frames matrix from current foot positions
            frames = np.asmatrix(self.current_foot_positions)
            
            # Solve inverse kinematics
            fr_angles, fl_angles, rr_angles, rl_angles, t_frames = self.kinematics.solve(
                self.current_orientation,
                self.current_position,
                frames
            )
            
            return fr_angles, fl_angles, rr_angles, rl_angles
            
        except Exception as e:
            print(f"Error calculating joint angles: {e}")
            return None
    
    def walk_trot(self, cycles=50):
        """
        Perform a trot walking gait using the same phases as the working script
        """
        print("Starting trot walk...")
        self.reset_servos_to_home()
        walking_phases = {
            "front_right":[
                {5: 55, 6: 110},
                {5: 35, 6: 110},
                {5: 35, 6: 125},
                {5: 65, 6: 120}
            ],
            "front_left": [
                {1: 70, 2: 50},
                {1: 90, 2: 50},
                {1: 90, 2: 35},
                {1: 60, 2: 40}
            ],
            "rear_right": [
                {13: 45, 14: 105},
                {13: 25, 14: 105},
                {13: 25, 14: 120},
                {13: 55, 14: 115}
            ],
            "rear_left": [
                {9: 79, 10: 50},
                {9: 99, 10: 50},
                {9: 99, 10: 35},
                {9: 69, 10: 40}
            ]
        }
        for _ in range(cycles):
            for phase_idx in range(4):
                rl_fr = phase_idx
                rr_fl = (phase_idx + 2) % 4
                angles = self.sitting_angles.copy()
                angles.update(walking_phases["rear_left"][rl_fr])
                angles.update(walking_phases["front_right"][rl_fr])
                angles.update(walking_phases["rear_right"][rr_fl])
                angles.update(walking_phases["front_left"][rr_fl])
                for ch, angle in angles.items():
                    self.set_servo_angle(ch, angle)
                time.sleep(0.015)
        self.reset_servos_to_home()
        print("Trot walk complete.")
    
    def walk_forward(self, step_length=0.03, step_height=0.05, num_steps=4):
        """
        Simple walking gait - move forward
        
        Args:
            step_length: Length of each step in meters 
            step_height: Height to lift feet during step
            num_steps: Number of steps to take
        """
        print(f"Walking forward - {num_steps} steps")
        
        for step in range(num_steps):
            print(f"Step {step + 1}/{num_steps}")
            
            # Lift and move front right and rear left legs (diagonal pair)
            self._move_leg_trajectory(0, step_length, 0, step_height)  # front right
            self._move_leg_trajectory(3, step_length, 0, step_height)  # rear left
            
            time.sleep(0.5)  # Pause between leg movements
            
            # Lift and move front left and rear right legs (diagonal pair)
            self._move_leg_trajectory(1, step_length, 0, step_height)  # front left
            self._move_leg_trajectory(2, step_length, 0, step_height)  # rear right
            
            time.sleep(0.5)
    
    def walk_sideways(self, step_length=0.03, step_height=0.05, direction='left', num_steps=4):
        """
        Walk sideways
        
        Args:
            step_length: Length of each step in meters
            step_height: Height to lift feet during step
            direction: 'left' or 'right'
            num_steps: Number of steps to take
        """
        y_step = step_length if direction == 'left' else -step_length
        print(f"Walking {direction} - {num_steps} steps")
        
        for step in range(num_steps):
            print(f"Step {step + 1}/{num_steps}")
            
            # Move legs in pairs
            self._move_leg_trajectory(0, 0, y_step, step_height)  # front right
            self._move_leg_trajectory(3, 0, y_step, step_height)  # rear left
            
            time.sleep(0.5)
            
            self._move_leg_trajectory(1, 0, y_step, step_height)  # front left
            self._move_leg_trajectory(2, 0, y_step, step_height)  # rear right
            
            time.sleep(0.5)
    
    def turn(self, angle_step=0.1, step_height=0.05, direction='left', num_steps=4):
        """
        Turn in place
        
        Args:
            angle_step: Angle to turn each step (radians)
            step_height: Height to lift feet during step
            direction: 'left' or 'right'
            num_steps: Number of steps to take
        """
        turn_radius = 0.1  # Distance from center to move feet
        angle_direction = 1 if direction == 'left' else -1
        
        print(f"Turning {direction} - {num_steps} steps")
        
        for step in range(num_steps):
            current_angle = angle_step * angle_direction * step
            
            # Calculate foot positions for turning
            for leg_idx in range(4):
                # Get default position
                default_pos = self.default_foot_positions[leg_idx].copy()
                
                # Apply rotation for turning
                x_new = default_pos[0] * np.cos(current_angle) - default_pos[1] * np.sin(current_angle)
                y_new = default_pos[0] * np.sin(current_angle) + default_pos[1] * np.cos(current_angle)
                
                target_pos = [x_new, y_new, default_pos[2]]
                
                # Lift and place leg
                self._move_leg_trajectory_absolute(leg_idx, target_pos, step_height)
                
            time.sleep(0.5)
    
    def _move_leg_trajectory(self, leg_index, dx, dy, lift_height):
        """
        Move a leg in a trajectory (lift, move, place)
        
        Args:
            leg_index: Index of the leg to move
            dx, dy: Distance to move in x and y
            lift_height: Height to lift the leg
        """
        current_pos = self.current_foot_positions[leg_index].copy()
        
        # Lift leg
        lift_pos = current_pos.copy()
        lift_pos[2] += lift_height
        self.move_single_leg(leg_index, lift_pos)
        self._execute_movement()
        
        # Move to new position while lifted
        target_pos = current_pos.copy()
        target_pos[0] += dx
        target_pos[1] += dy
        target_pos[2] += lift_height
        self.move_single_leg(leg_index, target_pos)
        self._execute_movement()
        
        # Lower leg to ground
        target_pos[2] = current_pos[2]
        self.move_single_leg(leg_index, target_pos)
        self._execute_movement()
    
    def _move_leg_trajectory_absolute(self, leg_index, target_position, lift_height):
        """
        Move leg to absolute position with trajectory
        """
        current_pos = self.current_foot_positions[leg_index].copy()
        
        # Lift leg
        lift_pos = current_pos.copy()
        lift_pos[2] += lift_height
        self.move_single_leg(leg_index, lift_pos)
        self._execute_movement()
        
        # Move to target while lifted
        target_lifted = np.array(target_position).copy()
        target_lifted[2] += lift_height
        self.move_single_leg(leg_index, target_lifted)
        self._execute_movement()
        
        # Lower to target
        self.move_single_leg(leg_index, target_position)
        self._execute_movement()
    
    def _execute_movement(self):
        """
        Execute the movement by calculating and displaying joint angles, then sending to servos
        """
        angles = self.calculate_joint_angles()
        if angles:
            fr_angles, fl_angles, rr_angles, rl_angles = angles
            print(f"Joint angles calculated:")
            
            # Convert numpy arrays to lists for proper formatting
            fr_deg = np.degrees(fr_angles).flatten()
            fl_deg = np.degrees(fl_angles).flatten()
            rr_deg = np.degrees(rr_angles).flatten()
            rl_deg = np.degrees(rl_angles).flatten()
            
            print(f"  Front Right: [{', '.join([f'{angle:.1f}' for angle in fr_deg])}]°")
            print(f"  Front Left:  [{', '.join([f'{angle:.1f}' for angle in fl_deg])}]°")
            print(f"  Rear Right:  [{', '.join([f'{angle:.1f}' for angle in rr_deg])}]°")
            print(f"  Rear Left:   [{', '.join([f'{angle:.1f}' for angle in rl_deg])}]°")
            
            # Send angles to physical servos
            self.send_to_servos(fr_angles, fl_angles, rr_angles, rl_angles)
        
        time.sleep(0.1)  # Small delay for movement execution
    
    def reset_to_default_stance(self):
        """
        Reset robot to default standing position and servo home positions
        """
        print("Resetting to default stance...")
        self.current_foot_positions = self.default_foot_positions.copy()
        self.current_position = np.array([0.0, 0.0, 0.0])
        self.current_orientation = np.array([0.0, 0.0, 0.0])
        
        # Reset servos to home position first
        self.reset_servos_to_home()
        time.sleep(0.5)
        
        # Then execute the kinematic calculation
        self._execute_movement()

    def cleanup(self):
        """Clean up servo control and reset servos"""
        if self.enable_servos and self.pwm:
            print("Cleaning up servo control...")
            try:
                # Reset all servos to home position
                self.reset_servos_to_home()
                
                # Clear all PWM signals
                for i in range(16):
                    self.pwm.channels[i].duty_cycle = 0
                    
                # Deinitialize PWM controller
                self.pwm.deinit()
            except Exception as e:
                print(f"Error during cleanup: {e}")
    
    def demonstrate_movements(self):
        """
        Demonstrate various movements using safe, proven servo angles
        """
        print("=== Spot Micro Safe Movement Demonstration ===")
        
        # Reset to sitting pose
        self.reset_to_default_stance()
        time.sleep(2)
        
        # Standing/Sitting poses using proven angles
        print("\n1. Standing pose")
        self.set_pose('stand')
        time.sleep(3)
        
        print("\n2. Sitting pose")
        self.set_pose('sit')
        time.sleep(3)
        
        print("\n3. Proven walking gait")
        print("Starting short walk demonstration...")
        self.walk_trot(cycles=5)  # Short demo walk
        
        # Reset
        print("\n4. Reset to sitting")
        self.reset_to_default_stance()
        
        print("\n=== Safe Demonstration complete ===")
        print("Note: Kinematic-based movements disabled for safety.")

    def control_individual_leg_xyz(self, leg_index, x, y, z):
        """
        Control individual leg position in X, Y, Z coordinates
        
        Args:
            leg_index: 0=front_right, 1=front_left, 2=rear_right, 3=rear_left
            x, y, z: Target coordinates relative to body center
        """
        leg_names = ["Front Right", "Front Left", "Rear Right", "Rear Left"]
        print(f"Moving {leg_names[leg_index]} to position: X={x:.3f}, Y={y:.3f}, Z={z:.3f}")
        
        self.move_single_leg(leg_index, [x, y, z])
        self._execute_movement()

    def control_all_legs_xyz(self, positions):
        """
        Control all legs with individual X, Y, Z coordinates
        
        Args:
            positions: List of [x, y, z] positions for each leg
                      [[fr_x, fr_y, fr_z], [fl_x, fl_y, fl_z], [rr_x, rr_y, rr_z], [rl_x, rl_y, rl_z]]
        """
        print("Moving all legs to specified positions:")
        leg_names = ["Front Right", "Front Left", "Rear Right", "Rear Left"]
        
        for i, pos in enumerate(positions):
            print(f"  {leg_names[i]}: X={pos[0]:.3f}, Y={pos[1]:.3f}, Z={pos[2]:.3f}")
            self.move_single_leg(i, pos)
        
        self._execute_movement()


def main():
    """
    Main function to demonstrate the Spot Micro controller
    """
    print("Initializing Spot Micro Controller...")
    controller = SpotMicroController()
    
    try:
        # Run demonstration
        controller.demonstrate_movements()
        
        # Interactive mode
        print("\n=== Interactive Mode ===")
        print("Available commands:")
        print("  'walk' - Use proven walking gait (walk_trot)")
        print("  'stand' - Move to standing position")
        print("  'sit' - Move to sitting position")
        print("  'forward' - Walk forward (kinematic - use with caution)")
        print("  'back' - Walk backward (kinematic - use with caution)") 
        print("  'left' - Walk left (kinematic - use with caution)")
        print("  'right' - Walk right (kinematic - use with caution)")
        print("  'turn_left' - Turn left (kinematic - use with caution)")
        print("  'turn_right' - Turn right (kinematic - use with caution)")
        print("  'up' - Move to standing position")
        print("  'down' - Move to sitting position")
        print("  'reset' - Reset to sitting position")
        print("  'quit' - Exit")
        print("\nNote: Kinematic commands use calculated angles - use proven angles when possible!")
        
        while True:
            command = input("\nEnter command: ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'walk':
                cycles = input("Enter number of cycles (default 10): ").strip()
                cycles = int(cycles) if cycles.isdigit() else 10
                controller.walk_trot(cycles=cycles)
            elif command == 'stand':
                controller.set_pose('stand')
            elif command == 'sit':
                controller.set_pose('sit')
            elif command == 'forward':
                controller.walk_forward(num_steps=3)
            elif command == 'back':
                controller.walk_forward(step_length=-0.02, num_steps=3)
            elif command == 'left':
                controller.walk_sideways(direction='left', num_steps=3)
            elif command == 'right':
                controller.walk_sideways(direction='right', num_steps=3)
            elif command == 'turn_left':
                controller.turn(direction='left', num_steps=4)
            elif command == 'turn_right':
                controller.turn(direction='right', num_steps=4)
            elif command == 'up':
                # Use standing pose instead of kinematic calculation
                print("Moving to standing position (up)...")
                self.set_pose('stand')
            elif command == 'down':
                # Use sitting pose instead of kinematic calculation  
                print("Moving to sitting position (down)...")
                self.set_pose('sit')
            elif command == 'tilt':
                print("Tilt command disabled for safety - use kinematic movements could damage robot")
                print("Use 'stand' or 'sit' poses instead")
            elif command == 'leg':
                try:
                    leg_idx = int(input("Enter leg index (0=FR, 1=FL, 2=RR, 3=RL): "))
                    x = float(input("Enter X position: "))
                    y = float(input("Enter Y position: "))
                    z = float(input("Enter Z position: "))
                    controller.control_individual_leg_xyz(leg_idx, x, y, z)
                except ValueError:
                    print("Invalid input. Please enter numbers.")
            elif command == 'all_legs':
                try:
                    positions = []
                    leg_names = ["Front Right", "Front Left", "Rear Right", "Rear Left"]
                    for i, name in enumerate(leg_names):
                        print(f"Enter position for {name}:")
                        x = float(input("  X: "))
                        y = float(input("  Y: "))
                        z = float(input("  Z: "))
                        positions.append([x, y, z])
                    controller.control_all_legs_xyz(positions)
                except ValueError:
                    print("Invalid input. Please enter numbers.")
            elif command == 'reset':
                controller.reset_to_default_stance()
            else:
                print("Unknown command. Try again.")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        controller.reset_to_default_stance()
        controller.cleanup()
        print("Spot Micro Controller stopped.")


if __name__ == "__main__":
    main()
