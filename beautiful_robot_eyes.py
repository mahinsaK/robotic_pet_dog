#!/usr/bin/env python3
"""
EMO-style Blinking Cyan Eyes for 320x480 Display
"""

import time
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
    # Eye size: auto-scale for EMO look
    eye_w = int(W * 0.38)
    eye_h = int(H * 0.65)
    eye_y = H // 2
    eye_spacing = int(W * 0.18)
    left_eye_x = W // 2.7 - eye_spacing - eye_w // 2
    right_eye_x = W // 1.8 + eye_spacing - eye_w // 2
    border = int(eye_w * 0.13)
    blink_time = 0.12
    open_time = 2.0
    color_cyan = (0, 0, 255)  # Updated to true cyan (0, 255, 255)
    color_bg = (255, 255, 255)
    color_border = (0, 180, 180)

    def draw_eyes(draw, blink=1.0):
        # Draw left eye (fully filled, no pupil)
        x, y = left_eye_x, eye_y - eye_h // 2
        draw.rounded_rectangle([x, y, x + eye_w, y + int(eye_h * blink)], radius=border, fill=color_cyan, outline=color_border, width=6)
        # Draw right eye (fully filled, no pupil)
        x2, y2 = right_eye_x, eye_y - eye_h // 2
        draw.rounded_rectangle([x2, y2, x2 + eye_w, y2 + int(eye_h * blink)], radius=border, fill=color_cyan, outline=color_border, width=6)

    print(f"EMO Blinking Eyes: {W}x{H} (cyan)")
    try:
        while True:
            # Eyes open
            for t in range(int(open_time*20)):
                img = Image.new("RGB", (W, H), color_bg)
                draw = ImageDraw.Draw(img)
                draw_eyes(draw, blink=1.0)
                device.display(img)
                time.sleep(0.05)
            # Blink close
            for t in range(8):
                blink = max(0.18, 1.0 - t/8)
                img = Image.new("RGB", (W, H), color_bg)
                draw = ImageDraw.Draw(img)
                draw_eyes(draw, blink=blink)
                device.display(img)
                time.sleep(blink_time/8)
            # Blink open
            for t in range(8):
                blink = max(0.18, t/8)
                img = Image.new("RGB", (W, H), color_bg)
                draw = ImageDraw.Draw(img)
                draw_eyes(draw, blink=blink)
                device.display(img)
                time.sleep(blink_time/8)
    except KeyboardInterrupt:
        img = Image.new("RGB", (W, H), color_bg)
        device.display(img)
        print("\nStopped EMO blinking eyes.")

if __name__ == "__main__":
    emo_blinking_eyes()