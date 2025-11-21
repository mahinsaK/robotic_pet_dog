#!/usr/bin/env python3
"""
EMO-style Blinking Cyan Eyes with Moods for 320x480 Display
"""

import time
import random
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486

def emo_blinking_eyes():
    # Setup display (landscape 480x320)
    serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
    try:
        device = ili9486(serial, width=480, height=320, rotate=1)
    except Exception:
        device = ili9486(serial, rotate=1)

    W, H = device.width, device.height
    # Eye size
    eye_w = int(W * 0.3)
    eye_h = int(H * 0.5)
    eye_y = H // 2
    eye_offset_x = int(W * 0.25)
    left_eye_x = W // 2 - eye_offset_x
    right_eye_x = W // 2 + eye_offset_x
    border = int(eye_h * 0.15)
    color_cyan = (0, 255, 255)
    color_bg = (255, 255, 255)
    color_border = (0, 180, 180)

    current_mood = 0  # 0=Normal, 1=Angry, 2=Calm, 3=Happy, 4=Sad, 5=Tired
    last_mood_change = time.time() * 1000
    last_blink = time.time() * 1000

    # Mood drawing functions
    def draw_normal_eye(draw, center_x, center_y, blink=1.0):
        x = center_x - eye_w // 2
        y = center_y - eye_h // 2
        draw.rounded_rectangle([x, y, x + eye_w, y + int(eye_h * blink)],
                               radius=border, fill=color_cyan,
                               outline=color_border, width=6)

    def draw_calm_eye(draw, center_x, center_y, blink=1.0):
        calm_eye_w = int(eye_w * 0.75)
        corner_radius = int(eye_h * 0.4)
        x = center_x - calm_eye_w // 2
        y = center_y - eye_h // 2
        draw.rounded_rectangle([x, y, x + calm_eye_w, y + int(eye_h * blink)],
                               radius=corner_radius, fill=color_cyan,
                               outline=color_border, width=6)

    def draw_angry_eye(draw, center_x, center_y, blink=1.0, is_left_eye=True):
        x = center_x - eye_w // 2
        y = center_y - eye_h // 2
        draw.rounded_rectangle([x, y, x + eye_w, y + int(eye_h * blink)],
                               radius=border, fill=color_cyan,
                               outline=color_border, width=6)
        slant_height = int(eye_h * 0.3)
        if is_left_eye:
            draw.polygon([
                (x + eye_w - slant_height, y),
                (x + eye_w, y),
                (x + eye_w, y + slant_height)
            ], fill=color_bg)
        else:
            draw.polygon([
                (x, y),
                (x + slant_height, y),
                (x, y + slant_height)
            ], fill=color_bg)

    def draw_happy_eye(draw, center_x, center_y, blink=1.0):
        x = center_x - eye_w // 2
        y = center_y - eye_h // 2
        draw.rounded_rectangle([x, y, x + eye_w, y + int(eye_h * blink)],
                               radius=border, fill=color_cyan,
                               outline=color_border, width=6)
        notch_height = int(eye_h * 0.2)
        draw.polygon([
            (x, y + int(eye_h * blink) - notch_height),
            (center_x, y + int(eye_h * blink)),
            (x + eye_w, y + int(eye_h * blink) - notch_height)
        ], fill=color_bg)

    def draw_sad_eye(draw, center_x, center_y, blink=1.0, is_left_eye=True):
        """Sad eyes: tapered top inside corner."""
        x = center_x - eye_w // 2
        y = center_y - int(eye_h * 0.5 * blink)
        draw.rounded_rectangle([x, y, x + eye_w, y + int(eye_h * 0.9 * blink)],
                               radius=border, fill=color_cyan,
                               outline=color_border, width=6)
        slant_height = int(eye_h * 0.3)
        if is_left_eye:
            draw.polygon([
                (x, y),  
                (x + slant_height, y),
                (x, y + slant_height)
            ], fill=color_bg)
        else:
            draw.polygon([
                (x + eye_w - slant_height, y),
                (x + eye_w, y),
                (x + eye_w, y + slant_height)
            ], fill=color_bg)

    def draw_tired_eye(draw, center_x, center_y, blink=1.0):
        """Tired eyes: horizontally squashed, eyelid half-closed."""
        tired_eye_w = int(eye_w * 0.8)
        tired_eye_h = int(eye_h * 0.6)
        x = center_x - tired_eye_w // 2
        y = center_y - tired_eye_h // 2
        draw.rounded_rectangle([x, y, x + tired_eye_w, y + int(tired_eye_h * blink)],
                               radius=border, fill=color_cyan,
                               outline=color_border, width=6)

    def draw_eyes(draw, blink=1.0):
        if current_mood == 0:  # Normal
            draw_normal_eye(draw, left_eye_x, eye_y, blink)
            draw_normal_eye(draw, right_eye_x, eye_y, blink)
        elif current_mood == 1:  # Angry
            draw_angry_eye(draw, left_eye_x, eye_y, blink, is_left_eye=True)
            draw_angry_eye(draw, right_eye_x, eye_y, blink, is_left_eye=False)
        elif current_mood == 2:  # Calm
            draw_calm_eye(draw, left_eye_x, eye_y, blink)
            draw_calm_eye(draw, right_eye_x, eye_y, blink)
        elif current_mood == 3:  # Happy
            draw_happy_eye(draw, left_eye_x, eye_y, blink)
            draw_happy_eye(draw, right_eye_x, eye_y, blink)
        elif current_mood == 4:  # Sad
            draw_sad_eye(draw, left_eye_x, eye_y, blink, is_left_eye=True)
            draw_sad_eye(draw, right_eye_x, eye_y, blink, is_left_eye=False)
        elif current_mood == 5:  # Tired
            draw_tired_eye(draw, left_eye_x, eye_y, blink)
            draw_tired_eye(draw, right_eye_x, eye_y, blink)

    def clear_eyes(draw):
        draw.rectangle([left_eye_x - eye_w // 2, eye_y - eye_h // 2,
                        left_eye_x + eye_w // 2, eye_y + eye_h // 2], fill=color_bg)
        draw.rectangle([right_eye_x - eye_w // 2, eye_y - eye_h // 2,
                        right_eye_x + eye_w // 2, eye_y + eye_h // 2], fill=color_bg)

    print(f"EMO Blinking Eyes with Moods: {W}x{H} (cyan)")
    try:
        while True:
            current_time = time.time() * 1000

            # Change mood every 10 seconds
            if current_time - last_mood_change > 10000:
                current_mood = (current_mood + 1) % 6  # now 6 moods
                last_mood_change = current_time
                img = Image.new("RGB", (W, H), color_bg)
                draw = ImageDraw.Draw(img)
                draw_eyes(draw, blink=1.0)
                device.display(img)

            # Blink randomly between 3–5 seconds
            if current_time - last_blink > random.randint(3000, 5000):
                img = Image.new("RGB", (W, H), color_bg)
                draw = ImageDraw.Draw(img)
                clear_eyes(draw)
                device.display(img)
                time.sleep(0.1)
                img = Image.new("RGB", (W, H), color_bg)
                draw = ImageDraw.Draw(img)
                draw_eyes(draw, blink=1.0)
                device.display(img)
                last_blink = current_time

            img = Image.new("RGB", (W, H), color_bg)
            draw = ImageDraw.Draw(img)
            draw_eyes(draw, blink=1.0)
            device.display(img)
            time.sleep(0.05)

    except KeyboardInterrupt:
        img = Image.new("RGB", (W, H), color_bg)
        device.display(img)
        print("\nStopped EMO blinking eyes.")

if __name__ == "__main__":
    emo_blinking_eyes()