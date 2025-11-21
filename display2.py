#!/usr/bin/env python3
"""
EMO-style Blinking Normal Cyan Eyes for 320x480 Display
"""

import time
import random
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486

def emo_normal_eyes():
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
    color_cyan = (0, 255, 255)  # Light blue RGB(0, 255, 255) / #00FFFF
    color_bg = (255, 255, 255)  # Black background
    color_border = (0, 255, 255)  # Light blue border

    def draw_normal_eye(draw, center_x, center_y, blink=1.0):
        x = center_x - eye_w // 2
        y = center_y - eye_h // 2
        draw.rounded_rectangle([x, y, x + eye_w, y + int(eye_h * blink)],
                               radius=border, fill=color_cyan,
                               outline=color_border, width=6)

    def draw_eyes(draw, blink=1.0):
        draw_normal_eye(draw, left_eye_x, eye_y, blink)
        draw_normal_eye(draw, right_eye_x, eye_y, blink)

    def clear_eyes(draw):
        draw.rectangle([left_eye_x - eye_w // 2, eye_y - eye_h // 2,
                        left_eye_x + eye_w // 2, eye_y + eye_h // 2], fill=color_bg)
        draw.rectangle([right_eye_x - eye_w // 2, eye_y - eye_h // 2,
                        right_eye_x + eye_w // 2, eye_y + eye_h // 2], fill=color_bg)

    print(f"EMO Normal Eyes: {W}x{H} (light blue)")
    last_blink = time.time() * 1000  # Initialize last_blink outside the loop
    try:
        while True:
            current_time = time.time() * 1000

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
                last_blink = current_time  # Update last_blink after blink

            img = Image.new("RGB", (W, H), color_bg)
            draw = ImageDraw.Draw(img)
            draw_eyes(draw, blink=1.0)
            device.display(img)
            time.sleep(0.05)

    except KeyboardInterrupt:
        img = Image.new("RGB", (W, H), color_bg)
        device.display(img)
        print("\nStopped EMO normal eyes.")

if __name__ == "__main__":
    emo_normal_eyes()