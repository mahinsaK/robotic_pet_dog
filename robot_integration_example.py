#!/usr/bin/env python3
"""
Example integration of robot pet eyes with existing p12-7.py robot control
This shows how to add animated eyes to your robotic pet dog

To integrate with your existing p12-7.py:
1. Copy the import and initialization sections
2. Add eye control calls to your existing functions
3. Start the eyes system before your main robot loop
"""

# Add these imports to the top of your p12-7.py file
from robot_eyes_launcher import (
    init_robot_eyes, stop_robot_eyes, set_robot_mood, 
    set_robot_walking, robot_react_distance, robot_react_touch,
    robot_blink
)

# Example of modified functions from p12-7.py with eyes integration
def enhanced_walk_trot(cycles=50, enable_obstacle_avoidance=True, speed=None):
    """
    Enhanced walk function with eye animations
    (This would replace your existing walk_trot function)
    """
    print("🐕 Starting enhanced walk with animated eyes...")
    
    # Set eyes to walking mode and happy mood
    set_robot_walking(True)
    set_robot_mood('excited')
    
    # Your existing walk_trot code here...
    # (Copy the contents of your walk_trot function from p12-7.py)
    
    # For this example, we'll simulate the walking
    import time
    for cycle in range(cycles):
        # Simulate obstacle detection with eyes reaction
        if enable_obstacle_avoidance:
            # Get distance (using your existing get_distance function)
            distance = get_distance()  # Your existing function
            
            if distance != -1 and distance < 30:
                print(f"🚨 Obstacle at {distance}cm - Eyes react!")
                robot_react_distance(distance)  # Eyes react to distance
                
                # Your existing obstacle avoidance code...
                break
        
        # Simulate walking cycle
        print(f"Walking cycle {cycle+1}/{cycles}")
        time.sleep(0.1)  # Replace with your actual servo movements
        
        # Occasional random blink during walking
        if cycle % 20 == 0:
            robot_blink()
    
    # Stop walking mode
    set_robot_walking(False)
    set_robot_mood('happy')
    print("✅ Enhanced walk complete with eyes!")

def enhanced_touch_toggle_mode():
    """
    Enhanced touch mode with eye reactions
    (This would replace your existing touch_toggle_mode function)
    """
    print("\n🤖 ENHANCED TOUCH TOGGLE MODE WITH EYES 🤖")
    print("=" * 60)
    
    # Set curious mood for touch mode
    set_robot_mood('curious')
    
    # Your existing touch toggle code here...
    import RPi.GPIO as GPIO
    import time
    
    TOUCH_PIN = 26  # Your touch pin
    is_standing = True
    last_touch_state = False
    toggle_count = 0
    
    try:
        while True:
            current_touch_state = GPIO.input(TOUCH_PIN)
            
            if current_touch_state and not last_touch_state:
                toggle_count += 1
                is_standing = not is_standing
                
                # Eyes react to touch
                robot_react_touch()
                
                if is_standing:
                    print(f"\n👆 Touch #{toggle_count} - STANDING MODE")
                    set_robot_mood('happy')
                    # Your existing set_pose(standing_angles) code
                else:
                    print(f"\n👆 Touch #{toggle_count} - SITTING MODE") 
                    set_robot_mood('sleepy')
                    # Your existing set_pose(sitting_angles) code
                
                time.sleep(0.5)
            
            last_touch_state = current_touch_state
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        set_robot_mood('default')
        print("\n🔄 Enhanced touch mode finished.")

def enhanced_main():
    """
    Enhanced main function with eyes integration
    (This shows how to modify your main() function)
    """
    print("🐕 Enhanced SpotMicro Pet Robot with Animated Eyes 🐕")
    print("=" * 70)
    
    # Initialize robot eyes first
    if init_robot_eyes():
        print("✅ Robot eyes system started successfully!")
    else:
        print("⚠️ Robot eyes not available - continuing without display")
    
    try:
        # Your existing robot initialization code here...
        # setup_sensors(), signal handlers, etc.
        
        print("\nAvailable enhanced modes:")
        print("• standing  - Ready position with happy eyes")
        print("• sitting   - Relaxed position with sleepy eyes") 
        print("• walk      - Walking with animated eyes and reactions")
        print("• right     - Turn right with focused eyes")
        print("• left      - Turn left with focused eyes")
        print("• toggle    - Touch mode with eye reactions")
        print("• happy     - Set happy mood")
        print("• excited   - Set excited mood")
        print("• curious   - Set curious mood")
        print("• sleepy    - Set sleepy mood")
        print("• blink     - Manual blink")
        print("• q         - Quit")
        print("=" * 70)
        
        while True:
            cmd = input("\nEnter enhanced mode: ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'standing':
                print("Moving to standing with happy eyes...")
                set_robot_mood('happy')
                # Your existing set_pose(standing_angles) code
                print("✅ Standing pose set with happy eyes!")
                
            elif cmd == 'sitting':
                print("Moving to sitting with sleepy eyes...")
                set_robot_mood('sleepy')
                # Your existing set_pose(sitting_angles) code
                print("✅ Sitting pose set with sleepy eyes!")
                
            elif cmd == 'walk':
                enhanced_walk_trot(cycles=50, enable_obstacle_avoidance=True)
                
            elif cmd == 'right':
                print("Turning right with focused eyes...")
                set_robot_mood('curious')
                # Your existing turn_right() code
                set_robot_mood('default')
                print("✅ Right turn complete!")
                
            elif cmd == 'left':
                print("Turning left with focused eyes...")
                set_robot_mood('curious')
                # Your existing turn_left() code
                set_robot_mood('default')
                print("✅ Left turn complete!")
                
            elif cmd == 'toggle':
                enhanced_touch_toggle_mode()
                
            # Eye-specific commands
            elif cmd == 'happy':
                set_robot_mood('happy')
                print("😊 Eyes set to happy mood!")
                
            elif cmd == 'excited':
                set_robot_mood('excited')
                print("🤩 Eyes set to excited mood!")
                
            elif cmd == 'curious':
                set_robot_mood('curious')
                print("🤔 Eyes set to curious mood!")
                
            elif cmd == 'sleepy':
                set_robot_mood('sleepy')
                print("😴 Eyes set to sleepy mood!")
                
            elif cmd == 'blink':
                robot_blink()
                print("😉 Robot blinked!")
                
            else:
                print("Invalid command!")
                
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up both robot and eyes
        stop_robot_eyes()
        # Your existing cleanup_gpio() code

# Simulate some existing functions from p12-7.py for this example
def get_distance():
    """Simulate your existing distance function"""
    import random
    return random.uniform(10, 100)

if __name__ == "__main__":
    # Run the enhanced robot system
    enhanced_main()
