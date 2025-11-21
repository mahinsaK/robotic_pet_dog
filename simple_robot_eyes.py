#!/usr/bin/env python3
"""
Robot Pet Eyes - Display Only Version
Simple version without GPIO for testing display functionality
"""

import time
import math
import random
from dataclasses import dataclass
from typing import Tuple
from enum import Enum

# Display imports only
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
from PIL import Image, ImageDraw, ImageFont

@dataclass
class EyeConfig:
    """Configuration for eye appearance and behavior"""
    width: int = 80
    height: int = 100
    spacing: int = 60
    border_radius: int = 20
    pupil_size: int = 25
    iris_size: int = 45
    blink_speed: float = 0.15

class Mood(Enum):
    """Available eye moods for the pet dog"""
    DEFAULT = "default"
    HAPPY = "happy"
    TIRED = "tired"
    CURIOUS = "curious"
    SLEEPY = "sleepy"

class Direction(Enum):
    """Eye gaze directions"""
    CENTER = (0, 0)
    E = (1, 0)
    W = (-1, 0)
    NE = (1, -1)
    NW = (-1, -1)

@dataclass
class EyeState:
    """Current state of the eyes"""
    mood: Mood = Mood.DEFAULT
    direction: Direction = Direction.CENTER
    blink_state: float = 1.0
    pupil_offset: Tuple[float, float] = (0.0, 0.0)

class SimpleRobotEyes:
    """Simplified robot eyes for display testing"""
    
    def __init__(self, config: EyeConfig = None):
        self.config = config or EyeConfig()
        self.state = EyeState()
        self.running = False
        self.walking_mode = False
        self.frame_count = 0
        
        # Initialize display
        self._init_display()
        
        # Load font
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            self.font = ImageFont.load_default()
    
    def _init_display(self):
        """Initialize display with your wiring"""
        # Your actual wiring: VCC->5V, GND->GND, MOSI->GPIO10, SCLK->GPIO11, CS->GPIO8, DC->GPIO25, RST->GPIO17
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        
        try:
            self.device = ili9486(serial, rotate=1)
        except:
            self.device = ili9486(serial, width=320, height=480, rotate=1)
        
        print(f"Display initialized: {self.device.width}x{self.device.height}")
        
        # Create drawing surface
        self.image = Image.new("RGB", (self.device.width, self.device.height), "black")
        self.draw = ImageDraw.Draw(self.image)
        
        # Calculate eye positions
        center_x = self.device.width // 2
        center_y = self.device.height // 2
        
        self.left_eye_center = (center_x - self.config.spacing, center_y)
        self.right_eye_center = (center_x + self.config.spacing, center_y)
    
    def _get_mood_parameters(self, mood: Mood) -> dict:
        """Get eye parameters for different moods"""
        mood_params = {
            Mood.DEFAULT: {'width_mod': 1.0, 'height_mod': 1.0, 'color': (100, 150, 255)},
            Mood.HAPPY: {'width_mod': 1.2, 'height_mod': 0.8, 'color': (150, 255, 150)},
            Mood.TIRED: {'width_mod': 0.8, 'height_mod': 0.6, 'color': (200, 150, 100)},
            Mood.CURIOUS: {'width_mod': 1.3, 'height_mod': 1.2, 'color': (100, 255, 200)},
            Mood.SLEEPY: {'width_mod': 0.6, 'height_mod': 0.4, 'color': (180, 150, 200)}
        }
        return mood_params.get(mood, mood_params[Mood.DEFAULT])
    
    def _draw_eye(self, center: Tuple[int, int]):
        """Draw a single eye"""
        mood_params = self._get_mood_parameters(self.state.mood)
        
        # Calculate dimensions
        width = self.config.width * mood_params['width_mod']
        height = self.config.height * mood_params['height_mod'] * self.state.blink_state
        
        # Walking bounce effect
        if self.walking_mode:
            bounce_offset = math.sin(self.frame_count * 0.3) * 4
            center = (center[0], center[1] + int(bounce_offset))
        
        if height < 2:  # Closed eye
            y = center[1]
            x1 = center[0] - width // 2
            x2 = center[0] + width // 2
            self.draw.line([(x1, y), (x2, y)], fill=mood_params['color'], width=4)
            return
        
        # Eye boundary
        x1 = center[0] - width // 2
        y1 = center[1] - height // 2
        x2 = center[0] + width // 2
        y2 = center[1] + height // 2
        
        # Draw eye outline
        self.draw.rounded_rectangle(
            [(x1, y1), (x2, y2)],
            radius=self.config.border_radius,
            fill="white",
            outline=mood_params['color'],
            width=3
        )
        
        # Calculate pupil position
        gaze_x, gaze_y = self.state.direction.value
        max_offset = min(width, height) * 0.2
        
        pupil_x = center[0] + gaze_x * max_offset + self.state.pupil_offset[0]
        pupil_y = center[1] + gaze_y * max_offset + self.state.pupil_offset[1]
        
        # Constrain pupil
        pupil_x = max(x1 + 20, min(x2 - 20, pupil_x))
        pupil_y = max(y1 + 20, min(y2 - 20, pupil_y))
        
        # Draw iris
        iris_size = self.config.iris_size
        iris_x1 = pupil_x - iris_size // 2
        iris_y1 = pupil_y - iris_size // 2
        iris_x2 = pupil_x + iris_size // 2
        iris_y2 = pupil_y + iris_size // 2
        
        self.draw.ellipse([(iris_x1, iris_y1), (iris_x2, iris_y2)], fill=mood_params['color'])
        
        # Draw pupil
        pupil_size = self.config.pupil_size
        pupil_x1 = pupil_x - pupil_size // 2
        pupil_y1 = pupil_y - pupil_size // 2
        pupil_x2 = pupil_x + pupil_size // 2
        pupil_y2 = pupil_y + pupil_size // 2
        
        self.draw.ellipse([(pupil_x1, pupil_y1), (pupil_x2, pupil_y2)], fill="black")
        
        # Highlight
        highlight_size = 6
        self.draw.ellipse([
            (pupil_x - pupil_size//3, pupil_y - pupil_size//3),
            (pupil_x - pupil_size//3 + highlight_size, pupil_y - pupil_size//3 + highlight_size)
        ], fill="white")
    
    def set_mood(self, mood: Mood):
        """Set eye mood"""
        self.state.mood = mood
        print(f"🐕 Mood: {mood.value}")
    
    def toggle_walking(self):
        """Toggle walking mode"""
        self.walking_mode = not self.walking_mode
        print(f"🚶 Walking: {'ON' if self.walking_mode else 'OFF'}")
    
    def blink(self):
        """Perform a blink"""
        print("😉 Blinking...")
        for i in range(5):
            self.state.blink_state = 1.0 - (i / 4.0)
            self.render_frame()
            time.sleep(0.03)
        time.sleep(0.1)
        for i in range(5):
            self.state.blink_state = i / 4.0
            self.render_frame()
            time.sleep(0.03)
        self.state.blink_state = 1.0
    
    def render_frame(self):
        """Render one frame"""
        # Clear screen
        self.draw.rectangle([(0, 0), (self.device.width, self.device.height)], fill="black")
        
        # Draw eyes
        self._draw_eye(self.left_eye_center)
        self._draw_eye(self.right_eye_center)
        
        # Status info
        status_texts = [
            f"Mood: {self.state.mood.value.title()}",
            f"Walking: {'ON' if self.walking_mode else 'OFF'}",
            f"Frame: {self.frame_count}",
            "Press Ctrl+C to stop"
        ]
        
        for i, text in enumerate(status_texts):
            self.draw.text((10, 10 + i * 16), text, fill="cyan", font=self.font)
        
        # Display
        self.device.display(self.image)
        self.frame_count += 1
    
    def demo_sequence(self):
        """Run a demonstration sequence"""
        print("🐕 Robot Pet Eyes Demo - Display Only Version")
        print("=" * 50)
        
        # Startup - eyes closed
        print("Starting up...")
        self.state.blink_state = 0.0
        self.set_mood(Mood.SLEEPY)
        self.render_frame()
        time.sleep(1)
        
        # Gradual eye opening
        print("Opening eyes...")
        for i in range(20):
            self.state.blink_state = i / 19.0
            self.render_frame()
            time.sleep(0.08)
        
        # Default mood
        self.set_mood(Mood.DEFAULT)
        self.render_frame()
        time.sleep(2)
        
        # Mood demonstrations
        moods = [Mood.HAPPY, Mood.CURIOUS, Mood.TIRED, Mood.DEFAULT]
        for mood in moods:
            self.set_mood(mood)
            for _ in range(30):  # Show each mood for ~1 second
                self.render_frame()
                time.sleep(0.03)
        
        # Walking demo
        print("Demonstrating walking mode...")
        self.set_mood(Mood.HAPPY)
        self.toggle_walking()
        for _ in range(60):  # 2 seconds of walking
            self.render_frame()
            time.sleep(0.03)
        self.toggle_walking()
        
        # Blink demo
        print("Blink demonstration...")
        self.set_mood(Mood.DEFAULT)
        for _ in range(3):
            time.sleep(1)
            self.blink()
        
        # Gaze demo
        print("Gaze direction demo...")
        directions = [Direction.E, Direction.W, Direction.NE, Direction.NW, Direction.CENTER]
        for direction in directions:
            self.state.direction = direction
            for _ in range(20):
                self.render_frame()
                time.sleep(0.05)
        
        # Final
        self.set_mood(Mood.SLEEPY)
        print("Demo complete! 🐕")
        
        # Keep showing for a bit
        for _ in range(60):
            self.render_frame()
            time.sleep(0.05)
        
        # Clear display
        self.draw.rectangle([(0, 0), (self.device.width, self.device.height)], fill="black")
        self.device.display(self.image)

def main():
    """Run the simple robot eyes demo"""
    try:
        config = EyeConfig(
            width=90,
            height=110,
            spacing=70,
            border_radius=22,
            pupil_size=28,
            iris_size=50
        )
        
        eyes = SimpleRobotEyes(config)
        eyes.demo_sequence()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("🧹 Cleaning up...")

if __name__ == "__main__":
    main()
