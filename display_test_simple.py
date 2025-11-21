import time
import random
import math
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
import threading

# Display dimensions for ILI9486 in landscape mode
WIDTH = 480
HEIGHT = 320

# Mood color definitions
MOOD_COLORS = {
    "happy": (0, 255, 0),
    "sad": (34, 34, 178),
    "angry": (255, 69, 0),
    "love": (147, 20, 255),
    "neutral": (38, 247, 253),
    "excited": (0, 255, 255)
}

class RoboEyes:
    def __init__(self):
        # Setup ILI9486 display using luma.lcd in landscape mode (rotate=1), fallback if needed
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        try:
            self.disp = ili9486(serial, width=480, height=320, rotate=1)
        except Exception:
            self.disp = ili9486(serial, rotate=1)
        print(f"Display initialized successfully! Resolution: {self.disp.width}x{self.disp.height}")

        self.width = WIDTH
        self.height = HEIGHT
        self.image = Image.new("RGB", (self.width, self.height), "black")
        self.draw_obj = ImageDraw.Draw(self.image)

        # Adjust eye dimensions to fit the 480x320 display
        self.eye_w = 110
        self.eye_h = 110
        self.eye_spacing = 30
        self.eye_radius = 18

        # Center the eyes horizontally and vertically
        total_eye_width = 2 * self.eye_w + self.eye_spacing
        start_x = (self.width - total_eye_width) // 2
        y_pos = (self.height - self.eye_h) // 2
        self.left_eye_pos = (start_x, y_pos)
        self.right_eye_pos = (start_x + self.eye_w + self.eye_spacing, y_pos)

        self.mood = "neutral"
        self.blinking = False
        self.auto_blink = False

        self.blink_direction = 0
        self.blink_progress = 0.0
        self.blink_speed = 0.005
        self.blink_hold_time = 0.03
        self.blink_hold_timer = 0

        self.last_blink = time.monotonic()
        self.next_blink_time = time.monotonic() + random.uniform(8, 16)

        self.frame_interval = 0.05
        self.last_frame = 0

        self.vertical_offset = 0
        self.scale_factor = 1.0
        self.animation_phase = 0.0

        self.eye_x_offset = 0
        self.eye_y_offset = 0
        self.next_neutral_shift_time = time.monotonic() + random.uniform(2, 5)
        self.neutral_shift_start_time = 0
        self.neutral_shift_duration = 0.5

        self.running = False
        self.update_thread = None

    def set_mood(self, mood):
        self.mood = mood

    def blink(self):
        if not self.blinking:
            self.blinking = True
            self.blink_direction = 1
            self.blink_progress = 0.0
            self.blink_speed = random.uniform(0.003, 0.008)

    def toggle_auto_blink(self):
        self.auto_blink = not self.auto_blink

    def mood_color(self):
        return MOOD_COLORS.get(self.mood, (0, 0, 255))

    def draw(self):
        self.image.paste((0, 0, 0), [0, 0, self.width, self.height])
        self._draw_eye(self.draw_obj, self.left_eye_pos, True)
        self._draw_eye(self.draw_obj, self.right_eye_pos, False)
        self.disp.display(self.image)

    def _draw_heart(self, draw, cx, cy, size, fill_color):
        scale = 0.05
        points = []
        for t in range(0, 360, 5):
            angle = math.radians(t)
            x = size * 16 * (math.sin(angle) ** 3)
            y = -size * (13 * math.cos(angle) - 5 * math.cos(2 * angle) - 2 * math.cos(3 * angle) - math.cos(4 * angle))
            points.append((cx + int(x * scale), cy + int(y * scale)))
        draw.polygon(points, fill=fill_color)

    def _draw_star(self, draw, cx, cy, size, fill_color):
        points = []
        for i in range(5):
            angle_outer = math.radians(i * 72 - 90)
            angle_inner = math.radians(i * 72 + 36 - 90)
            points.append((cx + size * math.cos(angle_outer), cy + size * math.sin(angle_outer)))
            points.append((cx + size * 0.5 * math.cos(angle_inner), cy + size * 0.5 * math.sin(angle_inner)))
        draw.polygon(points, fill=fill_color)

    def _draw_eye(self, draw, pos, is_left):
        x, y = pos
        y += self.vertical_offset

        scale = self.scale_factor
        eye_w = int(self.eye_w * scale)
        eye_h = int(self.eye_h * scale)
        eye_x = x + (self.eye_w - eye_w) // 2
        eye_y = y + (self.eye_h - eye_h) // 2

        b, g, r = self.mood_color()
        color = (r, g, b)

        offset_x = self.eye_x_offset if self.mood == "neutral" else 0
        offset_y = self.eye_y_offset if self.mood == "neutral" else 0

        cx = eye_x + eye_w // 2 + offset_x
        cy = eye_y + eye_h // 2 + offset_y
        size = min(eye_w, eye_h) // 2

        if self.mood not in ("love", "excited"):
            draw.rounded_rectangle(
                (eye_x, eye_y, eye_x + eye_w, eye_y + eye_h),
                radius=self.eye_radius,
                fill=color
            )

        if self.blinking:
            max_lid_height = eye_h // 2
            lid_height = int(max_lid_height * self.blink_progress)
            slit_height = 4
            if lid_height * 2 > eye_h - slit_height:
                lid_height = (eye_h - slit_height) // 2
            draw.rectangle((eye_x, eye_y, eye_x + eye_w, eye_y + lid_height), fill="black")
            draw.rectangle((eye_x, eye_y + eye_h - lid_height, eye_x + eye_w, eye_y + eye_h), fill="black")
            return

        if self.mood == "love":
            self._draw_heart(draw, cx, cy, size + 10, (193, 182, 255))
        elif self.mood == "excited":
            self._draw_star(draw, cx, cy, size, (0, 255, 255))
        elif self.mood == "sad":
            self._draw_sad_eye(draw, eye_x, eye_y, is_left)
        elif self.mood == "angry":
            self._draw_angry_eye(draw, eye_x, eye_y, is_left)
        elif self.mood == "happy":
            self._draw_happy_eye(draw, eye_x, y)

    def _draw_sad_eye(self, draw, x, y, is_left):
        if is_left:
            draw.polygon([(x, y), (x + self.eye_w, y), (x, y + self.eye_h // 2)], fill="black")
        else:
            draw.polygon([(x, y), (x + self.eye_w, y), (x + self.eye_w, y + self.eye_h // 2)], fill="black")

    def _draw_angry_eye(self, draw, x, y, is_left):
        if is_left:
            draw.polygon([(x, y), (x + self.eye_w, y), (x + self.eye_w, y + self.eye_h // 2)], fill="black")
        else:
            draw.polygon([(x, y), (x + self.eye_w, y), (x, y + self.eye_h // 2)], fill="black")

    def _draw_happy_eye(self, draw, x, y):
        eyelid_height = self.eye_h // 2
        draw.rounded_rectangle(
            (x - 1, y + self.eye_h - eyelid_height, x + self.eye_w + 1, y + self.eye_h + eyelid_height),
            radius=self.eye_radius,
            fill="black"
        )

    def update(self):
        now = time.monotonic()
        dt = now - self.last_frame
        self.last_frame = now

        self.animation_phase += dt

        if self.mood == "happy":
            self.vertical_offset = int(math.sin(self.animation_phase * 3) * 5)
            self.scale_factor = 1.0
        elif self.mood == "sad":
            amplitude = 3
            base_offset = 8
            self.vertical_offset = base_offset + int(amplitude * math.sin(self.animation_phase * 1.5))
            self.scale_factor = 1.0
        elif self.mood in ("angry", "love", "excited"):
            self.vertical_offset = 0
            self.scale_factor = 1.0 + 0.05 * math.sin(self.animation_phase * 4)
        else:
            self.vertical_offset = 0
            self.scale_factor = 1.0
            if now >= self.next_neutral_shift_time:
                self.eye_x_offset = random.randint(-5, 5)
                self.eye_y_offset = random.randint(-3, 3)
                self.neutral_shift_start_time = now
                self.next_neutral_shift_time = now + uniform(2, 5)
            elif now - self.neutral_shift_start_time >= self.neutral_shift_duration:
                self.eye_x_offset = 0
                self.eye_y_offset = 0

        if self.auto_blink and not self.blinking and now >= self.next_blink_time:
            self.blink()

        if self.blinking:
            self.blink_progress += self.blink_direction * dt / self.blink_speed
            self.blink_progress = max(0.0, min(1.0, self.blink_progress))

            if self.blink_progress >= 1.0:
                self.blink_progress = 1.0
                if self.blink_hold_timer == 0:
                    self.blink_hold_timer = now + self.blink_hold_time
                elif now >= self.blink_hold_timer:
                    self.blink_direction = -1
                    self.blink_hold_timer = 0
            elif self.blink_progress <= 0.0 and self.blink_direction == -1:
                self.blinking = False
                self.blink_direction = 0
                self.next_blink_time = now + random.uniform(1, 8)

        self.draw()

    def set_neutral(self):
        self.set_mood("neutral")
        self.toggle_auto_blink()
        self.update()

    def set_black(self):
        """Turn off the display and stop eye animations (sleep mode)."""
        self.blinking = False
        self.auto_blink = False
        self.image.paste((0, 0, 0), [0, 0, self.width, self.height])
        self.disp.display(self.image)

    def start(self):
        """Start continuous updating in a background thread."""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()

    def stop(self):
        """Stop the background update loop."""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
            self.update_thread = None

    def _update_loop(self):
        """Internal method that runs in a thread, continuously calling update()."""
        while self.running:
            self.update()
            time.sleep(self.frame_interval)

if __name__ == "__main__":
    print("Starting RoboEyes mood test...")
    eyes = RoboEyes()

    # Test all moods with animations
    moods = ["neutral", "happy", "sad", "angry", "love", "excited"]
    for mood in moods:
        print(f"Displaying {mood} mood...")
        eyes.set_mood(mood)
        if mood == "neutral":
            eyes.toggle_auto_blink()  # Enable auto-blink for neutral mood
        eyes.start()  # Start continuous animation
        time.sleep(10)  # Display each mood for 10 seconds
        eyes.stop()  # Stop animation before switching mood
        eyes.set_black()  # Clear display between moods
        time.sleep(1)

    print("Mood test complete. Display turned off.")