#!/usr/bin/env python3
"""
Simple test script for ILI9486 display to verify hardware setup
Run this first to ensure your display is working before using the full robot eyes system
"""

from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
from PIL import Image, ImageDraw, ImageFont
import time
import sys

def test_display():
    """Test the ILI9486 display with your specific wiring"""
    print("Testing ILI9486 Display...")
    print("Wiring should be:")
    print("  VCC  -> 5V")
    print("  GND  -> GND")
    print("  MOSI -> GPIO 10")
    print("  SCLK -> GPIO 11")
    print("  CS   -> GPIO 8 (CE0)")
    print("  DC   -> GPIO 25")
    print("  RST  -> GPIO 17")
    print()
    
    try:
        # Initialize SPI with your specific GPIO configuration
        # This matches your actual wiring from display1.py
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        print("✓ SPI interface initialized")
        
        # Initialize ILI9486 device - try auto-detection first
        try:
            device = ili9486(serial, rotate=1)  # Landscape orientation
            print(f"✓ Display initialized: {device.width}x{device.height}")
        except Exception as e:
            print(f"Auto-detection failed: {e}")
            print("Trying with manual resolution...")
            device = ili9486(serial, width=320, height=480, rotate=1)
            print(f"✓ Display initialized with manual resolution: {device.width}x{device.height}")
        
        # Test 1: Basic color display
        print("Test 1: Color background test...")
        colors = ["red", "green", "blue", "white", "black"]
        for color in colors:
            image = Image.new("RGB", (device.width, device.height), color)
            device.display(image)
            print(f"  Displaying {color}...")
            time.sleep(1)
        
        # Test 2: Simple graphics
        print("Test 2: Graphics test...")
        image = Image.new("RGB", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        
        # Draw border
        draw.rectangle([(0, 0), (device.width-1, device.height-1)], outline="white", width=3)
        
        # Draw text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 20), "Robot Pet Eyes Test", fill="cyan", font=font)
        draw.text((20, 50), f"Display: {device.width}x{device.height}", fill="yellow", font=font)
        draw.text((20, 80), "Hardware Test: PASSED", fill="green", font=font)
        
        # Draw some shapes
        draw.ellipse([(50, 120), (150, 220)], fill="red", outline="white", width=2)
        draw.ellipse([(200, 120), (300, 220)], fill="blue", outline="white", width=2)
        draw.rectangle([(350, 120), (450, 220)], fill="green", outline="white", width=2)
        
        device.display(image)
        print("  Graphics displayed successfully!")
        time.sleep(3)
        
        # Test 3: Animation test
        print("Test 3: Simple animation test...")
        for i in range(30):
            image = Image.new("RGB", (device.width, device.height), "black")
            draw = ImageDraw.Draw(image)
            
            # Moving circle
            x = int(50 + (device.width - 100) * (i / 29))
            y = device.height // 2
            draw.ellipse([(x-20, y-20), (x+20, y+20)], fill="yellow")
            
            # Progress text
            draw.text((20, 20), f"Animation frame {i+1}/30", fill="white", font=font)
            
            device.display(image)
            time.sleep(0.1)
        
        # Test 4: Touch response simulation
        print("Test 4: Simulated eye blink...")
        for blink_cycle in range(3):
            # Eyes open
            image = Image.new("RGB", (device.width, device.height), "black")
            draw = ImageDraw.Draw(image)
            
            # Draw two eyes
            left_eye_center = (device.width//2 - 60, device.height//2)
            right_eye_center = (device.width//2 + 60, device.height//2)
            
            # Open eyes
            for eye_center in [left_eye_center, right_eye_center]:
                draw.ellipse([
                    (eye_center[0]-40, eye_center[1]-50),
                    (eye_center[0]+40, eye_center[1]+50)
                ], fill="white", outline="cyan", width=2)
                
                # Iris
                draw.ellipse([
                    (eye_center[0]-20, eye_center[1]-25),
                    (eye_center[0]+20, eye_center[1]+25)
                ], fill="blue")
                
                # Pupil
                draw.ellipse([
                    (eye_center[0]-10, eye_center[1]-12),
                    (eye_center[0]+10, eye_center[1]+12)
                ], fill="black")
            
            draw.text((20, 20), f"Blink test {blink_cycle+1}/3", fill="white", font=font)
            device.display(image)
            time.sleep(0.8)
            
            # Eyes closed (blink)
            image = Image.new("RGB", (device.width, device.height), "black")
            draw = ImageDraw.Draw(image)
            
            for eye_center in [left_eye_center, right_eye_center]:
                draw.line([
                    (eye_center[0]-40, eye_center[1]),
                    (eye_center[0]+40, eye_center[1])
                ], fill="cyan", width=4)
            
            draw.text((20, 20), f"Blink test {blink_cycle+1}/3 - BLINK", fill="white", font=font)
            device.display(image)
            time.sleep(0.2)
        
        # Test complete
        print("✓ All tests completed successfully!")
        print("\nYour display is working correctly.")
        print("You can now run the full robot eyes system:")
        print("  python3 robot_pet_eyes.py")
        
        # Final display
        image = Image.new("RGB", (device.width, device.height), "green")
        draw = ImageDraw.Draw(image)
        draw.text((device.width//2-80, device.height//2-10), "TEST PASSED!", fill="white", font=font)
        device.display(image)
        time.sleep(2)
        
        # Clear display
        image = Image.new("RGB", (device.width, device.height), "black")
        device.display(image)
        
        return True
        
    except Exception as e:
        print(f"✗ Display test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check SPI is enabled: sudo raspi-config -> Interface Options -> SPI")
        print("2. Verify wiring connections")
        print("3. Install required libraries: pip3 install luma.lcd luma.core pillow")
        print("4. Try running with sudo if permission issues")
        return False

if __name__ == "__main__":
    success = test_display()
    sys.exit(0 if success else 1)
