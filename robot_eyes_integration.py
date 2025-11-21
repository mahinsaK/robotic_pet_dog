#!/usr/bin/env python3
"""
Robot Pet Eyes Integration for p12-7.py
Complete integration of video-style eyes with robot control system
"""

import time
import threading
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from video_robot_eyes import VideoRobotEyes, VideoEyeConfig, VideoMood
    EYES_AVAILABLE = True
    print("✅ Video robot eyes imported successfully")
except ImportError as e:
    print(f"⚠️ Video robot eyes not available: {e}")
    EYES_AVAILABLE = False

class RobotEyesIntegration:
    """Integration class for robot eyes with p12-7.py"""
    
    def __init__(self):
        self.eyes = None
        self.running = False
        self.animation_thread = None
        
        if EYES_AVAILABLE:
            try:
                # Configure eyes for robot integration
                config = VideoEyeConfig(
                    eye_width=100,
                    eye_height=120,
                    spacing=85,
                    pupil_size=38,
                    iris_size=70,
                    highlight_size=14,
                    frame_rate=18  # Lower frame rate to not interfere with robot control
                )
                
                self.eyes = VideoRobotEyes(config)
                print("✅ Robot eyes initialized for integration")
                
            except Exception as e:
                print(f"❌ Failed to initialize robot eyes: {e}")
                EYES_AVAILABLE = False
    
    def start(self):
        """Start the eyes system"""
        if not EYES_AVAILABLE or not self.eyes:
            return False
        
        print("👀 Starting robot pet eyes...")
        
        # Initial startup sequence
        self.eyes.set_mood(VideoMood.SLEEPY)
        
        # Gradual wake up
        for i in range(10):
            self.eyes.state.blink_state = i / 9.0
            self.eyes.render_frame()
            time.sleep(0.1)
        
        self.eyes.set_mood(VideoMood.NEUTRAL)
        
        # Start animation thread
        self.running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        
        print("✅ Robot pet eyes started successfully")
        return True
    
    def stop(self):
        """Stop the eyes system"""
        if self.eyes and self.running:
            print("👀 Stopping robot pet eyes...")
            
            # Sleepy mode before shutdown
            self.eyes.set_mood(VideoMood.SLEEPY)
            time.sleep(1)
            
            # Gradual close
            for i in range(10):
                self.eyes.state.blink_state = 1.0 - (i / 9.0)
                self.eyes.render_frame()
                time.sleep(0.08)
            
            self.running = False
            
            if self.animation_thread:
                self.animation_thread.join(timeout=1)
            
            # Clear display
            self.eyes.draw.rectangle([(0, 0), (self.eyes.device.width, self.eyes.device.height)], fill="black")
            self.eyes.device.display(self.eyes.image)
            
            print("✅ Robot pet eyes stopped")
    
    def _animation_loop(self):
        """Background animation loop"""
        while self.running:
            if self.eyes:
                self.eyes.render_frame()
                time.sleep(1.0 / self.eyes.config.frame_rate)
    
    # Robot integration methods
    def robot_walking_start(self):
        """Called when robot starts walking"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.HAPPY)
            print("👀 Eyes: Happy walking mode")
    
    def robot_walking_stop(self):
        """Called when robot stops walking"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.NEUTRAL)
            print("👀 Eyes: Neutral standing mode")
    
    def robot_obstacle_detected(self, distance: float):
        """Called when robot detects obstacle"""
        if self.eyes:
            if distance < 20:
                self.eyes.set_mood(VideoMood.SURPRISED)
                print(f"👀 Eyes: Surprised by close obstacle ({distance:.1f}cm)")
            elif distance < 40:
                self.eyes.set_mood(VideoMood.ALERT)
                print(f"👀 Eyes: Alert to obstacle ({distance:.1f}cm)")
    
    def robot_obstacle_avoided(self):
        """Called when robot successfully avoids obstacle"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.CURIOUS)
            self.eyes.play_look_around_sequence()
            print("👀 Eyes: Looking around after avoiding obstacle")
    
    def robot_touch_detected(self):
        """Called when touch sensor is activated"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.LOVE)
            self.eyes.play_wink_sequence()
            print("👀 Eyes: Showing love for touch")
    
    def robot_standing_up(self):
        """Called when robot stands up"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.ALERT)
            print("👀 Eyes: Alert standing pose")
    
    def robot_sitting_down(self):
        """Called when robot sits down"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.SLEEPY)
            print("👀 Eyes: Sleepy sitting pose")
    
    def robot_turning_left(self):
        """Called when robot turns left"""
        if self.eyes:
            self.eyes.state.pupil_x = -0.6  # Look left
            self.eyes.set_mood(VideoMood.CURIOUS)
            print("👀 Eyes: Looking left while turning")
    
    def robot_turning_right(self):
        """Called when robot turns right"""
        if self.eyes:
            self.eyes.state.pupil_x = 0.6   # Look right
            self.eyes.set_mood(VideoMood.CURIOUS)
            print("👀 Eyes: Looking right while turning")
    
    def robot_turn_complete(self):
        """Called when robot finishes turning"""
        if self.eyes:
            self.eyes.state.pupil_x = 0     # Look center
            self.eyes.set_mood(VideoMood.NEUTRAL)
            print("👀 Eyes: Centered after turn")
    
    def robot_thinking(self):
        """Called when robot is processing commands"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.THINKING)
            print("👀 Eyes: Thinking mode")
    
    def robot_excited(self):
        """Called when robot is excited (e.g., successful command)"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.PLAYFUL)
            self.eyes.play_blink_sequence()
            print("👀 Eyes: Excited and playful")
    
    def robot_error_state(self):
        """Called when robot encounters an error"""
        if self.eyes:
            self.eyes.set_mood(VideoMood.SURPRISED)
            # Quick double blink to indicate error
            self.eyes.play_blink_sequence()
            time.sleep(0.3)
            self.eyes.play_blink_sequence()
            print("👀 Eyes: Error indication")
    
    def set_custom_mood(self, mood_name: str):
        """Set a specific mood by name"""
        if not self.eyes:
            return
        
        mood_map = {
            'neutral': VideoMood.NEUTRAL,
            'happy': VideoMood.HAPPY,
            'sleepy': VideoMood.SLEEPY,
            'alert': VideoMood.ALERT,
            'curious': VideoMood.CURIOUS,
            'playful': VideoMood.PLAYFUL,
            'love': VideoMood.LOVE,
            'surprised': VideoMood.SURPRISED,
            'thinking': VideoMood.THINKING
        }
        
        mood = mood_map.get(mood_name.lower(), VideoMood.NEUTRAL)
        self.eyes.set_mood(mood)
        print(f"👀 Eyes: Custom mood set to {mood_name}")

# Global instance for easy access
robot_eyes = None

def init_robot_eyes():
    """Initialize robot eyes system"""
    global robot_eyes
    robot_eyes = RobotEyesIntegration()
    return robot_eyes.start()

def stop_robot_eyes():
    """Stop robot eyes system"""
    global robot_eyes
    if robot_eyes:
        robot_eyes.stop()

# Convenience functions for p12-7.py integration
def eyes_walking_start():
    if robot_eyes: robot_eyes.robot_walking_start()

def eyes_walking_stop():
    if robot_eyes: robot_eyes.robot_walking_stop()

def eyes_obstacle_detected(distance):
    if robot_eyes: robot_eyes.robot_obstacle_detected(distance)

def eyes_obstacle_avoided():
    if robot_eyes: robot_eyes.robot_obstacle_avoided()

def eyes_touch_detected():
    if robot_eyes: robot_eyes.robot_touch_detected()

def eyes_standing_up():
    if robot_eyes: robot_eyes.robot_standing_up()

def eyes_sitting_down():
    if robot_eyes: robot_eyes.robot_sitting_down()

def eyes_turning_left():
    if robot_eyes: robot_eyes.robot_turning_left()

def eyes_turning_right():
    if robot_eyes: robot_eyes.robot_turning_right()

def eyes_turn_complete():
    if robot_eyes: robot_eyes.robot_turn_complete()

def eyes_set_mood(mood):
    if robot_eyes: robot_eyes.set_custom_mood(mood)

def eyes_blink():
    if robot_eyes and robot_eyes.eyes: robot_eyes.eyes.play_blink_sequence()

def eyes_wink():
    if robot_eyes and robot_eyes.eyes: robot_eyes.eyes.play_wink_sequence()

# Demo function showing integration
def integration_demo():
    """Demonstrate robot eyes integration"""
    print("🤖 Robot Eyes Integration Demo")
    print("=" * 50)
    
    if not init_robot_eyes():
        print("❌ Could not start robot eyes")
        return
    
    try:
        # Simulate robot behaviors
        demo_sequence = [
            ("Robot powering up", lambda: eyes_set_mood('sleepy'), 2),
            ("Robot ready", lambda: eyes_set_mood('neutral'), 2),
            ("Robot starting to walk", eyes_walking_start, 1),
            ("Robot walking happily", lambda: None, 3),
            ("Robot stops walking", eyes_walking_stop, 1),
            ("Robot detects obstacle", lambda: eyes_obstacle_detected(15), 2),
            ("Robot avoids obstacle", eyes_obstacle_avoided, 2),
            ("Robot turns left", eyes_turning_left, 1.5),
            ("Robot turn complete", eyes_turn_complete, 1),
            ("Human touches robot", eyes_touch_detected, 3),
            ("Robot sits down", eyes_sitting_down, 2),
            ("Robot thinking", lambda: eyes_set_mood('thinking'), 2),
            ("Robot excited", lambda: eyes_set_mood('playful'), 2),
            ("Robot going to sleep", lambda: eyes_set_mood('sleepy'), 2)
        ]
        
        for description, action, duration in demo_sequence:
            print(f"🎬 {description}")
            action()
            time.sleep(duration)
            
        print("✅ Integration demo complete!")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted")
    finally:
        stop_robot_eyes()

if __name__ == "__main__":
    # Run different modes based on command line argument
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            integration_demo()
        elif sys.argv[1] == "test":
            # Simple test
            if init_robot_eyes():
                print("✅ Robot eyes test successful")
                time.sleep(5)
                stop_robot_eyes()
            else:
                print("❌ Robot eyes test failed")
    else:
        print("🐕 Robot Eyes Integration Module")
        print("Usage:")
        print("  python3 robot_eyes_integration.py demo  - Run integration demo")
        print("  python3 robot_eyes_integration.py test  - Quick test")
        print("\nTo integrate with your robot:")
        print("  from robot_eyes_integration import init_robot_eyes, eyes_walking_start, ...")
        print("  init_robot_eyes()  # At start of your robot program")
        print("  eyes_walking_start()  # When robot starts walking")
        print("  eyes_obstacle_detected(distance)  # When obstacle detected")
        print("  # etc...")
