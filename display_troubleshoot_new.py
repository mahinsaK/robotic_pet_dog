#!/usr/bin/env python3
"""
ILI9486 Display Troubleshooting - When Display Powers On But Shows Nothing
"""

import time
import board
import busio
import digitalio
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
from PIL import Image, ImageDraw

def test_spi_speeds():
    """Test different SPI speeds to find what works"""
    print("Testing different SPI speeds...")
    
    # Different SPI speeds to try (Hz)
    speeds = [8000000, 4000000, 2000000, 1000000, 500000]
    
    for speed in speeds:
        try:
            print(f"\nTrying SPI speed: {speed} Hz")
            
            # Create SPI interface with custom speed
            serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17, spi_speed_hz=speed)
            device = ili9486(serial, rotate=0)
            
            # Create a very simple test
            image = Image.new("RGB", (device.width, device.height), "red")
            draw = ImageDraw.Draw(image)
            draw.text((50, 50), f"SPI: {speed}Hz", fill="white")
            
            device.display(image)
            print(f"✓ Speed {speed} Hz - Image sent successfully")
            print("Check display for red screen with text")
            time.sleep(3)
            
        except Exception as e:
            print(f"✗ Speed {speed} Hz failed: {e}")

def test_basic_functionality():
    """Test most basic display functionality"""
    print("\nTesting basic display functionality...")
    
    try:
        # Initialize with default settings
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        device = ili9486(serial, rotate=0)
        
        print(f"Display initialized: {device.width}x{device.height}")
        
        # Test 1: All white (maximum brightness)
        print("Test 1: All white screen...")
        image = Image.new("RGB", (device.width, device.height), (255, 255, 255))
        device.display(image)
        print("White screen displayed - check for any light/glow")
        time.sleep(3)
        
        # Test 2: All red
        print("Test 2: All red screen...")
        image = Image.new("RGB", (device.width, device.height), (255, 0, 0))
        device.display(image)
        print("Red screen displayed")
        time.sleep(3)
        
        # Test 3: Checkerboard pattern (high contrast)
        print("Test 3: Checkerboard pattern...")
        image = Image.new("RGB", (device.width, device.height), "white")
        draw = ImageDraw.Draw(image)
        
        square_size = 40
        for x in range(0, device.width, square_size * 2):
            for y in range(0, device.height, square_size * 2):
                # Black squares
                draw.rectangle([
                    (x, y), 
                    (x + square_size - 1, y + square_size - 1)
                ], fill="black")
                draw.rectangle([
                    (x + square_size, y + square_size), 
                    (x + square_size * 2 - 1, y + square_size * 2 - 1)
                ], fill="black")
        
        device.display(image)
        print("Checkerboard pattern displayed")
        time.sleep(3)
        
        # Test 4: Large text
        print("Test 4: Large text...")
        image = Image.new("RGB", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        draw.text((20, 50), "DISPLAY", fill="white")
        draw.text((20, 100), "TEST", fill="red")
        draw.text((20, 150), "WORKING", fill="green")
        
        device.display(image)
        print("Large text displayed")
        time.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def check_hardware_connections():
    """Check hardware connections manually"""
    print("\n" + "="*50)
    print("HARDWARE CONNECTION CHECK")
    print("="*50)
    
    print("Please verify these connections with a multimeter:")
    print("1. VCC to 5V rail - should measure ~5V")
    print("2. GND to ground - should measure 0V")
    print("3. MOSI (GPIO10) - should be connected")
    print("4. SCLK (GPIO11) - should be connected")
    print("5. CS (GPIO8) - should be connected")
    print("6. DC (GPIO25) - should be connected")
    print("7. RST (GPIO17) - should be connected")
    
    print("\nBacklight check:")
    print("- Some ILI9486 displays have separate LED+ and LED- pins")
    print("- LED+ should connect to 5V")
    print("- LED- should connect to GND (or through current limiting resistor)")
    print("- Without backlight, display may work but appear very dim/black")
    
    input("\nPress Enter after checking connections...")

def test_alternative_library():
    """Test with alternative display approach"""
    print("\nTesting alternative display initialization...")
    
    try:
        # Try different initialization parameters
        configs = [
            {"rotate": 0},
            {"rotate": 1},
            {"rotate": 2}, 
            {"rotate": 3},
            {"width": 320, "height": 480, "rotate": 0},
            {"width": 480, "height": 320, "rotate": 0},
        ]
        
        for i, config in enumerate(configs):
            try:
                print(f"Config {i+1}: {config}")
                serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
                device = ili9486(serial, **config)
                
                # Very simple test - pure colors
                colors = ["white", "red", "green", "blue"]
                for color in colors:
                    image = Image.new("RGB", (device.width, device.height), color)
                    device.display(image)
                    print(f"  {color} displayed")
                    time.sleep(1)
                
                print(f"✓ Config {i+1} worked!")
                return True
                
            except Exception as e:
                print(f"✗ Config {i+1} failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"✗ Alternative library test failed: {e}")
        return False

def main():
    print("ILI9486 Display Troubleshooting")
    print("When display powers on but shows nothing")
    print("="*50)
    
    print("\nYour wiring configuration:")
    print("VCC -> 5V, GND -> GND")
    print("MOSI -> GPIO10, SCLK -> GPIO11, CS -> GPIO8")
    print("DC -> GPIO25, RST -> GPIO17")
    
    # Check hardware first
    check_hardware_connections()
    
    # Test basic functionality
    print("\nRunning basic functionality tests...")
    basic_ok = test_basic_functionality()
    
    if not basic_ok:
        print("\nTrying different SPI speeds...")
        test_spi_speeds()
        
        print("\nTrying alternative configurations...")
        test_alternative_library()
    
    print("\n" + "="*50)
    print("TROUBLESHOOTING SUMMARY")
    print("="*50)
    
    if basic_ok:
        print("✓ Basic tests passed - display should be working")
        print("If you still see nothing, check:")
        print("  1. Backlight connections (LED+ and LED-)")
        print("  2. Display brightness/contrast settings")
    else:
        print("✗ Tests failed - likely issues:")
        print("  1. Wiring problems (double-check all connections)")
        print("  2. Power supply issues (check 5V stability)")
        print("  3. Wrong display type (verify it's ILI9486)")
        print("  4. Defective display module")
    
    print("\nNext steps:")
    print("1. Check ALL wiring with multimeter")
    print("2. Verify 5V power supply is stable")
    print("3. Look for LED+ and LED- pins for backlight")
    print("4. Try a different display module if available")

if __name__ == "__main__":
    main()
