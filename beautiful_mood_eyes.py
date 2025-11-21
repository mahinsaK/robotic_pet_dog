#!/usr/bin/env python3
"""
Beautiful Multi-Mood Robot Eyes System
6 Different Eye Expressions with Beautiful Colors
"""

import time
import random
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486

class BeautifulRobotEyes:
    def __init__(self):
        # Setup display (landscape 480x320)
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        try:
            self.device = ili9486(serial, width=480, height=320, rotate=1)
        except Exception:
            self.device = ili9486(serial, rotate=1)
        
        self.W, self.H = self.device.width, self.device.height
        
        # Eye dimensions
        self.eye_w = int(self.W * 0.35)
        self.eye_h = int(self.H * 0.6)
        self.eye_y = self.H // 2
        self.eye_spacing = int(self.W * 0.15)
        self.left_eye_x = self.W // 3 - self.eye_spacing
        self.right_eye_x = self.W // 1.5 + self.eye_spacing
        
        # Colors - Beautiful gradient colors
        self.colors = {
            'cyan': (0, 255, 255),
            'blue': (30, 144, 255),
            'green': (50, 205, 50),
            'purple': (138, 43, 226),
            'orange': (255, 140, 0),
            'pink': (255, 20, 147),
            'red': (255, 69, 0),
            'yellow': (255, 215, 0)
        }
        
        self.bg_color = (15, 15, 25)  # Dark background
        self.current_mood = "normal"
        self.current_color = self.colors['cyan']
    
    def draw_sad_eyes(self, draw, blink=1.0, color=None):
        """Droopy, sad eyes - teardrop shape"""
        if color is None:
            color = self.current_color
        
        # Left eye - droopy teardrop
        x, y = self.left_eye_x, self.eye_y
        points = [
            (x, y - int(self.eye_h * 0.3 * blink)),
            (x + self.eye_w//3, y - int(self.eye_h * 0.4 * blink)),
            (x + self.eye_w//2, y - int(self.eye_h * 0.2 * blink)),
            (x + self.eye_w, y + int(self.eye_h * 0.3 * blink)),
            (x + self.eye_w//2, y + int(self.eye_h * 0.4 * blink)),
            (x, y)
        ]
        draw.polygon(points, fill=color, outline=(color[0]//2, color[1]//2, color[2]//2), width=3)
        
        # Right eye - droopy teardrop
        x2 = self.right_eye_x
        points2 = [
            (x2 + self.eye_w, y - int(self.eye_h * 0.3 * blink)),
            (x2 + 2*self.eye_w//3, y - int(self.eye_h * 0.4 * blink)),
            (x2 + self.eye_w//2, y - int(self.eye_h * 0.2 * blink)),
            (x2, y + int(self.eye_h * 0.3 * blink)),
            (x2 + self.eye_w//2, y + int(self.eye_h * 0.4 * blink)),
            (x2 + self.eye_w, y)
        ]
        draw.polygon(points2, fill=color, outline=(color[0]//2, color[1]//2, color[2]//2), width=3)
    
    def draw_happy_eyes(self, draw, blink=1.0, color=None):
        """Happy curved eyes"""
        if color is None:
            color = self.current_color
        
        # Left eye - curved happy shape
        x, y = self.left_eye_x, self.eye_y - int(self.eye_h * 0.1)
        draw.arc([x, y - int(self.eye_h * 0.3 * blink), 
                 x + self.eye_w, y + int(self.eye_h * 0.3 * blink)], 
                start=-30, end=210, fill=color, width=12)
        draw.ellipse([x + self.eye_w//4, y - int(self.eye_h * 0.2 * blink), 
                     x + 3*self.eye_w//4, y + int(self.eye_h * 0.2 * blink)], 
                    fill=color, outline=(color[0]//2, color[1]//2, color[2]//2), width=2)
        
        # Right eye - curved happy shape
        x2 = self.right_eye_x
        draw.arc([x2, y - int(self.eye_h * 0.3 * blink), 
                 x2 + self.eye_w, y + int(self.eye_h * 0.3 * blink)], 
                start=-30, end=210, fill=color, width=12)
        draw.ellipse([x2 + self.eye_w//4, y - int(self.eye_h * 0.2 * blink), 
                     x2 + 3*self.eye_w//4, y + int(self.eye_h * 0.2 * blink)], 
                    fill=color, outline=(color[0]//2, color[1]//2, color[2]//2), width=2)
    
    def draw_angry_eyes(self, draw, blink=1.0, color=None):
        """Angry slanted eyes"""
        if color is None:
            color = (255, 69, 0)  # Red for angry
        
        # Left eye - angry slant
        x, y = self.left_eye_x, self.eye_y
        points = [
            (x + self.eye_w//3, y - int(self.eye_h * 0.4 * blink)),
            (x + self.eye_w, y - int(self.eye_h * 0.2 * blink)),
            (x + 2*self.eye_w//3, y + int(self.eye_h * 0.3 * blink)),
            (x, y + int(self.eye_h * 0.1 * blink))
        ]
        draw.polygon(points, fill=color, outline=(200, 0, 0), width=3)
        
        # Right eye - angry slant
        x2 = self.right_eye_x
        points2 = [
            (x2 + 2*self.eye_w//3, y - int(self.eye_h * 0.4 * blink)),
            (x2 + self.eye_w, y + int(self.eye_h * 0.1 * blink)),
            (x2 + self.eye_w//3, y + int(self.eye_h * 0.3 * blink)),
            (x2, y - int(self.eye_h * 0.2 * blink))
        ]
        draw.polygon(points2, fill=color, outline=(200, 0, 0), width=3)
    
    def draw_tired_eyes(self, draw, blink=1.0, color=None):
        """Tired half-closed eyes"""
        if color is None:
            color = self.colors['purple']
        
        # Left eye - sleepy horizontal oval
        x, y = self.left_eye_x, self.eye_y
        draw.ellipse([x, y - int(self.eye_h * 0.15 * blink), 
                     x + self.eye_w, y + int(self.eye_h * 0.15 * blink)], 
                    fill=color, outline=(color[0]//2, color[1]//2, color[2]//2), width=2)
        
        # Right eye - sleepy horizontal oval
        x2 = self.right_eye_x
        draw.ellipse([x2, y - int(self.eye_h * 0.15 * blink), 
                     x2 + self.eye_w, y + int(self.eye_h * 0.15 * blink)], 
                    fill=color, outline=(color[0]//2, color[1]//2, color[2]//2), width=2)
    
    def draw_normal_eyes(self, draw, blink=1.0, color=None):
        """Normal oval eyes"""
        if color is None:
            color = self.current_color
        
        # Left eye - normal oval
        x, y = self.left_eye_x, self.eye_y - int(self.eye_h * 0.3)
        draw.ellipse([x, y, x + self.eye_w, y + int(self.eye_h * blink)], 
                    fill=color, outline=(color[0]//2, color[1]//2, color[2]//2), width=3)
        
        # Right eye - normal oval
        x2 = self.right_eye_x
        draw.ellipse([x2, y, x2 + self.eye_w, y + int(self.eye_h * blink)], 
                    fill=color, outline=(color[0]//2, color[1]//2, color[2]//2), width=3)
    
    def draw_calm_eyes(self, draw, blink=1.0, color=None):
        """Calm peaceful eyes"""
        if color is None:
            color = self.colors['green']
        
        # Left eye - calm rounded rectangle
        x, y = self.left_eye_x, self.eye_y - int(self.eye_h * 0.25)
        draw.rounded_rectangle([x, y, x + self.eye_w, y + int(self.eye_h * 0.5 * blink)], 
                              radius=self.eye_w//4, fill=color, 
                              outline=(color[0]//2, color[1]//2, color[2]//2), width=2)
        
        # Right eye - calm rounded rectangle
        x2 = self.right_eye_x
        draw.rounded_rectangle([x2, y, x2 + self.eye_w, y + int(self.eye_h * 0.5 * blink)], 
                              radius=self.eye_w//4, fill=color, 
                              outline=(color[0]//2, color[1]//2, color[2]//2), width=2)
    
    def get_eye_drawer(self, mood):
        """Get the appropriate drawing function for the mood"""
        mood_map = {
            'sad': self.draw_sad_eyes,
            'happy': self.draw_happy_eyes,
            'angry': self.draw_angry_eyes,
            'tired': self.draw_tired_eyes,
            'normal': self.draw_normal_eyes,
            'calm': self.draw_calm_eyes
        }
        return mood_map.get(mood, self.draw_normal_eyes)
    
    def blink_animation(self, mood="normal", color_name="cyan", duration=3.0):
        """Animate eyes with blinking for specified duration"""
        color = self.colors.get(color_name, self.colors['cyan'])
        self.current_color = color
        eye_drawer = self.get_eye_drawer(mood)
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # Eyes open
            for t in range(40):
                img = Image.new("RGB", (self.W, self.H), self.bg_color)
                draw = ImageDraw.Draw(img)
                eye_drawer(draw, blink=1.0, color=color)
                self.device.display(img)
                time.sleep(0.05)
            
            # Blink animation
            for t in range(6):
                blink = max(0.1, 1.0 - t/6)
                img = Image.new("RGB", (self.W, self.H), self.bg_color)
                draw = ImageDraw.Draw(img)
                eye_drawer(draw, blink=blink, color=color)
                self.device.display(img)
                time.sleep(0.02)
            
            for t in range(6):
                blink = max(0.1, t/6)
                img = Image.new("RGB", (self.W, self.H), self.bg_color)
                draw = ImageDraw.Draw(img)
                eye_drawer(draw, blink=blink, color=color)
                self.device.display(img)
                time.sleep(0.02)
    
    def mood_cycle(self):
        """Cycle through all moods automatically"""
        moods = [
            ('normal', 'cyan'),
            ('happy', 'yellow'),
            ('sad', 'blue'),
            ('angry', 'red'),
            ('tired', 'purple'),
            ('calm', 'green')
        ]
        
        print("🎭 Starting Beautiful Robot Eyes - Mood Cycle")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                for mood, color in moods:
                    print(f"😊 {mood.title()} mood with {color} color")
                    self.blink_animation(mood, color, duration=5.0)
                    time.sleep(1)
        except KeyboardInterrupt:
            img = Image.new("RGB", (self.W, self.H), self.bg_color)
            self.device.display(img)
            print("\n✨ Beautiful Robot Eyes stopped.")

def main():
    eyes = BeautifulRobotEyes()
    eyes.mood_cycle()

if __name__ == "__main__":
    main()
