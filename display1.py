from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
from PIL import Image, ImageDraw, ImageFont
import time

# Create SPI interface - configured for your actual wiring
# Your wiring: DC=GPIO25, RST=GPIO17
serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)

# ILI9486 typically supports 320x480, let's try without specifying width/height first
try:
    device = ili9486(serial, rotate=0)
    print(f"Display initialized successfully! Resolution: {device.width}x{device.height}")
except Exception as e:
    print(f"Error initializing display: {e}")
    # Try with common ILI9486 resolution
    device = ili9486(serial, width=320, height=480, rotate=0)
    print(f"Display initialized with manual resolution: {device.width}x{device.height}")

# Create image with device dimensions
image = Image.new("RGB", (device.width, device.height), "black")
draw = ImageDraw.Draw(image)

# Add some visual elements to make it more obvious if it's working
draw.rectangle([(0, 0), (device.width-1, device.height-1)], outline="white", width=2)
draw.text((10, 10), "Hello, ILI9486!", fill="white")
draw.text((10, 40), f"Resolution: {device.width}x{device.height}", fill="yellow")
draw.text((10, 70), "Display Test", fill="green")

# Draw a simple pattern
for i in range(0, device.width, 20):
    draw.line([(i, 0), (i, device.height)], fill="blue")

print("Displaying image...")
device.display(image)
print("Image displayed successfully!")

# Keep the display on for a few seconds
time.sleep(5)

# Clear the display
print("Clearing display...")
clear_image = Image.new("RGB", (device.width, device.height), "black")
device.display(clear_image)
print("Display cleared!")
