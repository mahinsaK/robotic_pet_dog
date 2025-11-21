#!/usr/bin/env python3
"""
Interactive Video Robot Pet Eyes
Control robot pet eyes with keyboard commands and integration support
"""

import time
import threading
import sys
from video_robot_eyes import VideoRobotEyes, VideoEyeConfig, VideoMood

class InteractiveRobotEyes:
    """Interactive control for video-style robot eyes"""
    
    def __init__(self):
        # Initialize video eyes with optimal settings
        config = VideoEyeConfig(
            eye_width=120,
            eye_height=140,
            spacing=95,
            pupil_size=45,
            iris_size=80,
            highlight_size=18,
            frame_rate=25  # Balanced for smooth animation and performance
        )
        
        self.eyes = VideoRobotEyes(config)
        self.running = False
        self.current_mode = "manual"
        
        # Available commands
        self.mood_commands = {
            '1': VideoMood.NEUTRAL,
            '2': VideoMood.HAPPY,
            '3': VideoMood.SLEEPY,
            '4': VideoMood.ALERT,
            '5': VideoMood.CURIOUS,
            '6': VideoMood.PLAYFUL,
            '7': VideoMood.LOVE,
            '8': VideoMood.SURPRISED,
            '9': VideoMood.THINKING
        }
    
    def show_menu(self):
        """Display the control menu"""
        print("\n🎮 Interactive Robot Pet Eyes Control")
        print("=" * 50)
        print("MOOD CONTROLS:")
        print("  1 - Neutral      6 - Playful")
        print("  2 - Happy        7 - Love ❤️")
        print("  3 - Sleepy       8 - Surprised")
        print("  4 - Alert        9 - Thinking")
        print("  5 - Curious")
        print()
        print("ANIMATION CONTROLS:")
        print("  b - Blink        w - Wink")
        print("  l - Look around  a - Auto mode")
        print("  m - Manual mode")
        print()
        print("SPECIAL COMMANDS:")
        print("  d - Demo mode    s - Status")
        print("  h - Help         q - Quit")
        print("=" * 50)
    
    def start_animation_thread(self):
        """Start the animation rendering thread"""
        def animation_loop():
            while self.running:
                self.eyes.render_frame()
                time.sleep(1.0 / self.eyes.config.frame_rate)
        
        self.animation_thread = threading.Thread(target=animation_loop, daemon=True)
        self.animation_thread.start()
    
    def auto_mode(self):
        """Run automatic mood changes"""
        print("🤖 Auto mode activated - robot will change expressions automatically")
        auto_moods = [
            VideoMood.NEUTRAL, VideoMood.CURIOUS, VideoMood.HAPPY,
            VideoMood.PLAYFUL, VideoMood.ALERT, VideoMood.THINKING
        ]
        
        mood_index = 0
        last_change = time.time()
        
        while self.current_mode == "auto" and self.running:
            if time.time() - last_change > 8:  # Change every 8 seconds
                self.eyes.set_mood(auto_moods[mood_index])
                mood_index = (mood_index + 1) % len(auto_moods)
                last_change = time.time()
            
            time.sleep(0.5)
    
    def demo_mode(self):
        """Run the full video demo"""
        print("🎬 Starting full demo mode...")
        self.current_mode = "demo"
        
        # Stop current animation thread
        old_running = self.running
        self.running = False
        time.sleep(0.2)
        
        # Run demo
        self.eyes.run_video_demo(duration=30)
        
        # Restart
        self.running = old_running
        if self.running:
            self.start_animation_thread()
        self.current_mode = "manual"
    
    def show_status(self):
        """Show current status"""
        print(f"\n📊 Current Status:")
        print(f"   Mood: {self.eyes.state.mood.value.title()}")
        print(f"   Mode: {self.current_mode}")
        print(f"   Running: {self.running}")
        print(f"   Frame Rate: {self.eyes.config.frame_rate} FPS")
    
    def run_interactive(self):
        """Run the interactive control system"""
        print("🐕 Video Robot Pet Eyes - Interactive Mode")
        self.show_menu()
        
        # Start with neutral mood
        self.eyes.set_mood(VideoMood.NEUTRAL)
        
        # Start animation thread
        self.running = True
        self.start_animation_thread()
        
        try:
            while True:
                try:
                    command = input("\nEnter command: ").strip().lower()
                    
                    if command == 'q':
                        break
                    elif command == 'h':
                        self.show_menu()
                    elif command == 's':
                        self.show_status()
                    elif command == 'b':
                        print("😉 Blinking...")
                        self.eyes.play_blink_sequence()
                    elif command == 'w':
                        print("😉 Winking...")
                        self.eyes.play_wink_sequence()
                    elif command == 'l':
                        print("👀 Looking around...")
                        self.eyes.play_look_around_sequence()
                    elif command == 'a':
                        self.current_mode = "auto"
                        auto_thread = threading.Thread(target=self.auto_mode, daemon=True)
                        auto_thread.start()
                    elif command == 'm':
                        self.current_mode = "manual"
                        print("✋ Manual mode activated")
                    elif command == 'd':
                        self.demo_mode()
                    elif command in self.mood_commands:
                        mood = self.mood_commands[command]
                        self.eyes.set_mood(mood)
                        print(f"🎭 Mood set to: {mood.value.title()}")
                    elif command == 'reset':
                        # Hidden reset command
                        self.eyes.state.pupil_x = 0
                        self.eyes.state.pupil_y = 0
                        self.eyes.state.blink_state = 1.0
                        self.eyes.state.left_blink = 1.0
                        self.eyes.state.right_blink = 1.0
                        print("🔄 Eyes reset to center")
                    else:
                        print("❌ Unknown command. Type 'h' for help.")
                        
                except EOFError:
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        finally:
            self.running = False
            print("🧹 Shutting down interactive mode...")
            
            # Clear display
            self.eyes.draw.rectangle([(0, 0), (self.eyes.device.width, self.eyes.device.height)], fill="black")
            self.eyes.device.display(self.eyes.image)

# Integration functions for robot control
def create_robot_eyes_controller():
    """Create a robot eyes controller for integration"""
    config = VideoEyeConfig(
        eye_width=115,
        eye_height=135,
        spacing=90,
        pupil_size=42,
        iris_size=78,
        highlight_size=16,
        frame_rate=20  # Lower frame rate for integration to save CPU
    )
    
    return VideoRobotEyes(config)

def robot_eyes_integration_example():
    """Example of how to integrate with robot control system"""
    print("🤖 Robot Eyes Integration Example")
    print("This shows how to use video eyes with your robot system")
    
    # Create eyes controller
    eyes = create_robot_eyes_controller()
    
    # Start animation in background
    running = True
    
    def animation_loop():
        while running:
            eyes.render_frame()
            time.sleep(1.0 / eyes.config.frame_rate)
    
    animation_thread = threading.Thread(target=animation_loop, daemon=True)
    animation_thread.start()
    
    # Simulate robot behaviors
    behaviors = [
        ("Robot starting up", VideoMood.SLEEPY, 2),
        ("Robot awake and ready", VideoMood.NEUTRAL, 2),
        ("Robot detects person", VideoMood.CURIOUS, 3),
        ("Robot happy to see you", VideoMood.HAPPY, 3),
        ("Robot wants to play", VideoMood.PLAYFUL, 3),
        ("Robot shows affection", VideoMood.LOVE, 3),
        ("Robot hears sound", VideoMood.ALERT, 2),
        ("Robot surprised by movement", VideoMood.SURPRISED, 2),
        ("Robot thinking about command", VideoMood.THINKING, 3),
        ("Robot going to sleep", VideoMood.SLEEPY, 2)
    ]
    
    try:
        for behavior, mood, duration in behaviors:
            print(f"🐕 {behavior}")
            eyes.set_mood(mood)
            
            # Simulate some robot actions
            if mood == VideoMood.CURIOUS:
                time.sleep(1)
                eyes.play_look_around_sequence()
            elif mood == VideoMood.PLAYFUL:
                time.sleep(1.5)
                eyes.play_wink_sequence()
            elif mood == VideoMood.ALERT:
                eyes.play_blink_sequence()
            
            time.sleep(duration)
            
    except KeyboardInterrupt:
        print("\n🛑 Integration example stopped")
    finally:
        running = False
        print("🧹 Integration example complete")
        
        # Clear display
        eyes.draw.rectangle([(0, 0), (eyes.device.width, eyes.device.height)], fill="black")
        eyes.device.display(eyes.image)

def main():
    """Main function with different modes"""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "integration":
            robot_eyes_integration_example()
            return
        elif mode == "demo":
            config = VideoEyeConfig(eye_width=120, eye_height=140, spacing=95)
            eyes = VideoRobotEyes(config)
            eyes.run_video_demo(duration=45)
            return
    
    # Default: interactive mode
    controller = InteractiveRobotEyes()
    controller.run_interactive()

if __name__ == "__main__":
    main()
