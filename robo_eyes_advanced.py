#!/usr/bin/env python3
"""
Advanced Robot Eyes with Moods and Animations
Fixed version with proper syntax and display compatibility
"""

import time
import random
import math
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
from luma.core.render import canvas
from PIL import Image, ImageDraw
from enum import Enum

# Define mood and position enums
class Mood(Enum):
    DEFAULT = 0
    HAPPY = 1
    TIRED = 2
    ANGRY = 3

class Position(Enum):
    DEFAULT = 0
    N = 1
    NE = 2
    E = 3
    SE = 4
    S = 5
    SW = 6
    W = 7
    NW = 8

class RoboEyes:
    def __init__(self):
        # Initialize SPI interface with your working pin configuration
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        
        try:
            self.device = ili9486(serial, rotate=1)  # Landscape
        except:
            self.device = ili9486(serial, width=320, height=480, rotate=1)
        
        print(f"Advanced Robot Eyes Display: {self.device.width}x{self.device.height}")
        
        # Eye parameters adjusted for display size
        self.left_eye_x = self.device.width // 4  # Center x for left eye
        self.left_eye_y = self.device.height // 2  # Center y for left eye
        self.right_eye_x = 3 * self.device.width // 4  # Center x for right eye
        self.right_eye_y = self.device.height // 2  # Center y for right eye
        self.eye_width = 80
        self.eye_height = 100
        self.border_radius = 20
        self.space_between = 120
        self.cyclops = False
        self.mood = Mood.DEFAULT
        self.position = Position.DEFAULT
        self.curiosity = False
        self.h_flicker = False
        self.v_flicker = False
        self.h_flicker_amplitude = 0
        self.v_flicker_amplitude = 0
        self.autoblinker = False
        self.idle_mode = False
        self.blink_interval = 3  # seconds
        self.blink_variation = 1  # seconds
        self.idle_interval = 5  # seconds
        self.idle_variation = 2  # seconds
        self.left_eye_open = True
        self.right_eye_open = True
        self.last_blink = time.time()
        self.last_idle = time.time()
        self.frame_rate = 30  # FPS
        self.last_frame = time.time()
        
        # Create base image
        self.image = Image.new("RGB", (self.device.width, self.device.height), "black")
        self.draw = ImageDraw.Draw(self.image)

    def begin(self, frame_rate=30):
        self.frame_rate = frame_rate

    def set_width(self, left, right):
        self.eye_width = left  # Assuming symmetric eyes for simplicity

    def set_height(self, left, right):
        self.eye_height = left

    def set_border_radius(self, left, right):
        self.border_radius = left

    def set_space_between(self, space):
        self.space_between = space
        self.right_eye_x = self.left_eye_x + space

    def set_cyclops(self, on):
        self.cyclops = on

    def set_mood(self, mood):
        self.mood = mood
        print(f"Mood changed to: {mood.name}")

    def set_position(self, pos):
        self.position = pos
        print(f"Looking: {pos.name}")

    def set_curiosity(self, on):
        self.curiosity = on

    def set_h_flicker(self, on, amplitude):
        self.h_flicker = on
        self.h_flicker_amplitude = amplitude

    def set_v_flicker(self, on, amplitude):
        self.v_flicker = on
        self.v_flicker_amplitude = amplitude

    def set_autoblinker(self, on, interval, variation):
        self.autoblinker = on
        self.blink_interval = interval
        self.blink_variation = variation

    def set_idle_mode(self, on, interval, variation):
        self.idle_mode = on
        self.idle_interval = interval
        self.idle_variation = variation

    def open(self, left=True, right=True):
        self.left_eye_open = left
        self.right_eye_open = right

    def close(self, left=True, right=True):
        self.left_eye_open = not left
        self.right_eye_open = not right

    def blink(self, left=True, right=True):
        print("Blinking...")
        self.close(left, right)
        self.update()
        time.sleep(0.1)
        self.open(left, right)
        self.update()

    def anim_confused(self):
        print("Animation: Confused")
        for _ in range(5):
            self.set_h_flicker(True, 10)
            self.update()
            time.sleep(0.05)
            self.set_h_flicker(False, 0)
            self.update()
            time.sleep(0.05)

    def anim_laugh(self):
        print("Animation: Laughing")
        for _ in range(5):
            self.set_v_flicker(True, 10)
            self.update()
            time.sleep(0.05)
            self.set_v_flicker(False, 0)
            self.update()
            time.sleep(0.05)

    def draw_rounded_rect(self, x, y, w, h, radius, outline_color, fill_color):
        """Draw a rounded rectangle using PIL"""
        # Draw main rectangles
        self.draw.rectangle([(x + radius, y), (x + w - radius, y + h)], fill=fill_color)
        self.draw.rectangle([(x, y + radius), (x + w, y + h - radius)], fill=fill_color)
        
        # Draw corners
        self.draw.ellipse([(x, y), (x + 2*radius, y + 2*radius)], fill=fill_color)
        self.draw.ellipse([(x + w - 2*radius, y), (x + w, y + 2*radius)], fill=fill_color)
        self.draw.ellipse([(x, y + h - 2*radius), (x + 2*radius, y + h)], fill=fill_color)
        self.draw.ellipse([(x + w - 2*radius, y + h - 2*radius), (x + w, y + h)], fill=fill_color)
        
        # Draw outline if needed
        if outline_color != fill_color:
            # Outer outline
            self.draw.rectangle([(x + radius, y), (x + w - radius, y + 1)], fill=outline_color)
            self.draw.rectangle([(x + radius, y + h - 1), (x + w - radius, y + h)], fill=outline_color)
            self.draw.rectangle([(x, y + radius), (x + 1, y + h - radius)], fill=outline_color)
            self.draw.rectangle([(x + w - 1, y + radius), (x + w, y + h - radius)], fill=outline_color)

    def update(self):
        # Frame rate control
        current_time = time.time()
        if current_time - self.last_frame < 1.0 / self.frame_rate:
            return
        self.last_frame = current_time

        # Autoblinker
        if self.autoblinker and current_time - self.last_blink > self.blink_interval + random.uniform(-self.blink_variation, self.blink_variation):
            self.blink()
            self.last_blink = current_time

        # Idle mode
        if self.idle_mode and current_time - self.last_idle > self.idle_interval + random.uniform(-self.idle_variation, self.idle_variation):
            positions = [Position.N, Position.NE, Position.E, Position.SE, Position.S, Position.SW, Position.W, Position.NW]
            self.set_position(random.choice(positions))
            self.last_idle = current_time

        # Calculate eye positions
        offset_x = 0
        offset_y = 0
        if self.h_flicker:
            offset_x = random.randint(-self.h_flicker_amplitude, self.h_flicker_amplitude)
        if self.v_flicker:
            offset_y = random.randint(-self.v_flicker_amplitude, self.v_flicker_amplitude)

        # Position adjustments
        pos_offset_x = 0
        pos_offset_y = 0
        if self.position == Position.N:
            pos_offset_y = -20
        elif self.position == Position.NE:
            pos_offset_x, pos_offset_y = 20, -20
        elif self.position == Position.E:
            pos_offset_x = 20
        elif self.position == Position.SE:
            pos_offset_x, pos_offset_y = 20, 20
        elif self.position == Position.S:
            pos_offset_y = 20
        elif self.position == Position.SW:
            pos_offset_x, pos_offset_y = -20, 20
        elif self.position == Position.W:
            pos_offset_x = -20
        elif self.position == Position.NW:
            pos_offset_x, pos_offset_y = -20, -20

        # Curiosity effect
        curiosity_height = self.eye_height
        if self.curiosity and abs(pos_offset_x) > 0:
            curiosity_height = self.eye_height + 10

        # Clear image
        self.image = Image.new("RGB", (self.device.width, self.device.height), "black")
        self.draw = ImageDraw.Draw(self.image)

        # Calculate eye positions
        left_pupil_x = self.left_eye_x + pos_offset_x + offset_x
        left_pupil_y = self.left_eye_y + pos_offset_y + offset_y
        right_pupil_x = self.right_eye_x + pos_offset_x + offset_x
        right_pupil_y = self.right_eye_y + pos_offset_y + offset_y

        # Mood adjustments
        pupil_size = self.eye_width // 4
        eye_color = (255, 255, 255)  # White
        pupil_color = (255, 255, 255)  # White pupils
        
        if self.mood == Mood.HAPPY:
            pupil_size = self.eye_width // 3
            eye_color = (100, 255, 100)  # Light green
        elif self.mood == Mood.TIRED:
            curiosity_height = self.eye_height // 2
            eye_color = (100, 100, 255)  # Light blue
        elif self.mood == Mood.ANGRY:
            pupil_size = self.eye_width // 5
            eye_color = (255, 100, 100)  # Light red

        # Draw left eye
        if not self.cyclops and self.left_eye_open:
            eye_x = self.left_eye_x - self.eye_width // 2
            eye_y = self.left_eye_y - curiosity_height // 2
            self.draw_rounded_rect(eye_x, eye_y, self.eye_width, curiosity_height, 
                                 self.border_radius, eye_color, (0, 0, 0))
            
            # Draw pupil
            self.draw.ellipse([
                (left_pupil_x - pupil_size, left_pupil_y - pupil_size),
                (left_pupil_x + pupil_size, left_pupil_y + pupil_size)
            ], fill=pupil_color)

        # Draw right eye
        if not self.cyclops and self.right_eye_open:
            eye_x = self.right_eye_x - self.eye_width // 2
            eye_y = self.right_eye_y - curiosity_height // 2
            self.draw_rounded_rect(eye_x, eye_y, self.eye_width, curiosity_height,
                                 self.border_radius, eye_color, (0, 0, 0))
            
            # Draw pupil
            self.draw.ellipse([
                (right_pupil_x - pupil_size, right_pupil_y - pupil_size),
                (right_pupil_x + pupil_size, right_pupil_y + pupil_size)
            ], fill=pupil_color)

        # Draw cyclops eye
        if self.cyclops and self.left_eye_open:
            eye_x = self.left_eye_x - self.eye_width // 2
            eye_y = self.left_eye_y - curiosity_height // 2
            self.draw_rounded_rect(eye_x, eye_y, self.eye_width, curiosity_height,
                                 self.border_radius, eye_color, (0, 0, 0))
            
            # Draw pupil
            self.draw.ellipse([
                (left_pupil_x - pupil_size, left_pupil_y - pupil_size),
                (left_pupil_x + pupil_size, left_pupil_y + pupil_size)
            ], fill=pupil_color)

        # Update display
        self.device.display(self.image)

def main():
    try:
        print("🤖 Starting Advanced Robot Eyes...")
        eyes = RoboEyes()
        eyes.begin(30)
        eyes.set_width(80, 80)
        eyes.set_height(100, 100)
        eyes.set_border_radius(20, 20)
        eyes.set_space_between(120)
        eyes.set_autoblinker(True, 3, 1)
        eyes.set_idle_mode(True, 5, 2)

        print("🎬 Starting animation sequence...")
        print("Press Ctrl+C to stop")

        while True:
            # Example animation sequence
            eyes.set_mood(Mood.HAPPY)
            eyes.update()
            time.sleep(5)
            
            eyes.anim_laugh()
            
            eyes.set_mood(Mood.TIRED)
            eyes.update()
            time.sleep(5)
            
            eyes.set_mood(Mood.ANGRY)
            eyes.update()
            time.sleep(5)
            
            eyes.anim_confused()
            
            eyes.set_mood(Mood.DEFAULT)
            eyes.update()
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n🛑 Stopping robot eyes...")
        # Clear display
        clear_image = Image.new("RGB", (eyes.device.width, eyes.device.height), "black")
        eyes.device.display(clear_image)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your display is connected correctly:")
        print("VCC->5V, GND->GND, MOSI->GPIO10, SCLK->GPIO11, CS->GPIO8, DC->GPIO25, RST->GPIO17")

if __name__ == "__main__":
    main()
