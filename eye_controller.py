#!/usr/bin/env python3
"""
Manual Control for Beautiful Robot Eyes
Choose mood and color interactively
"""

from beautiful_mood_eyes import BeautifulRobotEyes
import time

def interactive_eye_control():
    eyes = BeautifulRobotEyes()
    
    print("🎭 Beautiful Robot Eyes - Manual Control")
    print("=" * 50)
    print("Available moods: sad, happy, angry, tired, normal, calm")
    print("Available colors: cyan, blue, green, purple, orange, pink, red, yellow")
    print("Commands: 'mood color' (e.g., 'happy yellow'), 'auto' for cycle, 'quit' to exit")
    print("=" * 50)
    
    try:
        while True:
            command = input("\n🎯 Enter command: ").strip().lower()
            
            if command == 'quit' or command == 'q':
                break
            elif command == 'auto':
                print("🔄 Starting automatic mood cycle...")
                eyes.mood_cycle()
                break
            elif ' ' in command:
                parts = command.split()
                if len(parts) == 2:
                    mood, color = parts
                    if mood in ['sad', 'happy', 'angry', 'tired', 'normal', 'calm']:
                        if color in eyes.colors:
                            print(f"✨ Showing {mood} eyes in {color}")
                            eyes.blink_animation(mood, color, duration=10.0)
                        else:
                            print(f"❌ Unknown color: {color}")
                    else:
                        print(f"❌ Unknown mood: {mood}")
                else:
                    print("❌ Use format: 'mood color'")
            else:
                print("❌ Invalid command. Use 'mood color', 'auto', or 'quit'")
    
    except KeyboardInterrupt:
        pass
    finally:
        # Clear display
        from PIL import Image
        img = Image.new("RGB", (eyes.W, eyes.H), eyes.bg_color)
        eyes.device.display(img)
        print("\n✨ Eye control stopped.")

if __name__ == "__main__":
    interactive_eye_control()
[HTTP] Server started on port 8080
[HTTP] Serving files from: /home/ubuntu/without_ros
^C
[HTTP] Server stopped by user
