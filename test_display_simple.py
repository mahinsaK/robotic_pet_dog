#!/usr/bin/env python3
"""
Simple display test to check if display is working
"""

import time
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486

def test_display():
    """Test basic display functionality"""
    try:
        # Initialize display with your working configuration
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        device = ili9486(serial, rotate=1)  # Landscape
        
        print(f"Display initialized: {device.width}x{device.height}")
        
        # Create a simple test image
        image = Image.new("RGB", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        
        # Draw test pattern
        print("Drawing test pattern...")
        
        # Red rectangle
        draw.rectangle([(10, 10), (100, 100)], fill=(255, 0, 0))
        
        # Green circle
        draw.ellipse([(150, 50), (250, 150)], fill=(0, 255, 0))
        
        # Blue text
        draw.text((300, 100), "TEST", fill=(0, 0, 255))
        
        # White border
        draw.rectangle([(0, 0), (device.width-1, device.height-1)], outline=(255, 255, 255), width=3)
        
        # Display the image
        device.display(image)
        print("Test pattern displayed!")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing display...")
    if test_display():
        print("Display test successful!")
        time.sleep(5)
    else:
        print("Display test failed!")
