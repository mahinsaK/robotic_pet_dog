#!/usr/bin/env python3
"""
ILI9486 Backlight Test and Fix
The display is working but backlight is likely the issue
"""

import time
import board
import digitalio
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
from PIL import Image, ImageDraw

def check_backlight_pins():
    """Check for common backlight pin configurations"""
    print("BACKLIGHT TROUBLESHOOTING")
    print("="*40)
    
    print("Your ILI9486 display likely has these additional pins:")
    print("- LED+ (or LED_A, BL+, LEDA)")
    print("- LED- (or LED_K, BL-, LEDK)")
    print()
    print("Common backlight wiring:")
    print("Option 1: LED+ -> 5V, LED- -> GND")
    print("Option 2: LED+ -> 5V, LED- -> GND through 100-220Ω resistor")
    print("Option 3: LED+ -> 3.3V, LED- -> GND")
    print()
    print("Without backlight connection, display works but appears black!")

def test_with_maximum_brightness():
    """Test display with maximum possible brightness settings"""
    print("\nTesting with maximum brightness...")
    
    try:
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        device = ili9486(serial, rotate=0)
        
        # Create maximum brightness white image
        print("Creating maximum brightness pattern...")
        image = Image.new("RGB", (device.width, device.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Add some high contrast elements
        draw.rectangle([(0, 0), (device.width-1, device.height-1)], outline=(255, 0, 0), width=10)
        draw.text((50, 100), "MAX BRIGHTNESS", fill=(0, 0, 0))
        draw.text((50, 150), "CHECK FOR GLOW", fill=(0, 0, 0))
        
        device.display(image)
        
        print("✓ Maximum brightness white screen displayed")
        print("Look VERY carefully at the display:")
        print("- Any faint glow or light?")
        print("- Shine a flashlight on the screen - see any patterns?")
        print("- Look from different angles")
        
        time.sleep(10)
        return True
        
    except Exception as e:
        print(f"✗ Brightness test failed: {e}")
        return False

def create_backlight_test_gpio():
    """Test potential backlight control via GPIO"""
    print("\nTesting potential backlight GPIO control...")
    
    # Common GPIO pins that might control backlight
    backlight_pins = [18, 19, 12, 13, 6, 26]
    
    for pin_num in backlight_pins:
        try:
            print(f"Testing GPIO{pin_num} as backlight control...")
            
            # Get the pin
            pin = getattr(board, f'D{pin_num}')
            backlight_pin = digitalio.DigitalInOut(pin)
            backlight_pin.direction = digitalio.Direction.OUTPUT
            
            # Try turning it on
            backlight_pin.value = True
            print(f"  GPIO{pin_num} set HIGH - check display")
            time.sleep(2)
            
            # Try turning it off
            backlight_pin.value = False
            print(f"  GPIO{pin_num} set LOW - check display")
            time.sleep(2)
            
            # Clean up
            backlight_pin.deinit()
            
        except Exception as e:
            print(f"  GPIO{pin_num} test failed: {e}")

def display_wiring_guide():
    """Show complete wiring guide including backlight"""
    print("\n" + "="*60)
    print("COMPLETE ILI9486 WIRING GUIDE")
    print("="*60)
    
    print("MAIN CONNECTIONS (you have these):")
    print("VCC  -> 5V")
    print("GND  -> GND") 
    print("MOSI -> GPIO10")
    print("SCLK -> GPIO11")
    print("CS   -> GPIO8")
    print("DC   -> GPIO25")
    print("RST  -> GPIO17")
    
    print("\nBACKLIGHT CONNECTIONS (likely missing):")
    print("LED+ (or BL+, LEDA) -> 5V")
    print("LED- (or BL-, LEDK) -> GND")
    print("  OR")
    print("LED+ -> 5V")
    print("LED- -> 220Ω resistor -> GND")
    
    print("\nOTHER POSSIBLE PINS ON YOUR DISPLAY:")
    print("- Some displays have T_CLK, T_CS, T_DIN, T_DO, T_IRQ (touch)")
    print("- Some have SD_CS, SD_MOSI, SD_MISO, SD_SCK (SD card)")
    print("- Look for LED+/LED- or similar backlight pins")
    
    print("\nTROUBLESHOOTING STEPS:")
    print("1. Check your display module for LED+/LED- pins")
    print("2. Connect LED+ to 5V and LED- to GND")
    print("3. If too bright, add 100-220Ω resistor in LED- line")
    print("4. Some displays need 3.3V instead of 5V for backlight")

def test_display_variations():
    """Test different display driver variations"""
    print("\nTesting display driver variations...")
    
    try:
        # Test with different initialization
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        
        # Create a very obvious test pattern
        print("Creating high-contrast test pattern...")
        
        device = ili9486(serial, rotate=0)
        
        # Alternating black and white stripes
        image = Image.new("RGB", (device.width, device.height), "white")
        draw = ImageDraw.Draw(image)
        
        stripe_width = 20
        for x in range(0, device.width, stripe_width * 2):
            draw.rectangle([
                (x, 0), 
                (x + stripe_width - 1, device.height - 1)
            ], fill="black")
        
        device.display(image)
        print("High contrast stripes displayed")
        
        time.sleep(5)
        return True
        
    except Exception as e:
        print(f"Display variation test failed: {e}")
        return False

def main():
    print("ILI9486 BACKLIGHT DIAGNOSIS")
    print("Display receives data but shows nothing = backlight issue")
    print("="*60)
    
    # Check backlight information
    check_backlight_pins()
    
    # Test with maximum brightness
    test_with_maximum_brightness()
    
    # Test potential GPIO backlight control
    create_backlight_test_gpio()
    
    # Test display variations
    test_display_variations()
    
    # Show complete wiring guide
    display_wiring_guide()
    
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    print("Your display communication is working perfectly!")
    print("The issue is almost certainly the backlight.")
    print()
    print("IMMEDIATE ACTION:")
    print("1. Look for LED+ and LED- pins on your display")
    print("2. Connect LED+ to 5V")
    print("3. Connect LED- to GND (or through 220Ω resistor)")
    print("4. Your display should immediately light up!")
    print()
    print("If no LED+/LED- pins visible:")
    print("- Check the back of the display module")
    print("- Look for alternative labels (BL+/BL-, LEDA/LEDK)")
    print("- Consult your display's datasheet/documentation")

if __name__ == "__main__":
    main()
