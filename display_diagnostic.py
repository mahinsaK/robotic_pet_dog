#!/usr/bin/env python3
"""
ILI9486 Display Line Issue Diagnostic
Helps diagnose why display might only show a single line
"""

import time
from luma.core.interface.serial import spi
from luma.lcd.device import ili9486
from PIL import Image, ImageDraw, ImageFont

def test_line_by_line():
    """Test drawing line by line to identify display issues"""
    print("Testing line-by-line display...")
    
    try:
        # Initialize display
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
        device = ili9486(serial, rotate=0)
        
        print(f"Display size: {device.width}x{device.height}")
        
        # Test 1: Single pixel lines across the screen
        print("Test 1: Drawing horizontal lines...")
        image = Image.new("RGB", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        
        # Draw horizontal lines at different positions
        line_positions = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450]
        for i, y in enumerate(line_positions):
            if y < device.height:
                color = ["red", "green", "blue", "yellow", "cyan", "magenta", "white", "orange"][i % 8]
                draw.line([(0, y), (device.width-1, y)], fill=color, width=2)
                print(f"  Line at y={y} ({color})")
        
        device.display(image)
        print("Horizontal lines displayed - can you see multiple colored lines?")
        time.sleep(5)
        
        # Test 2: Vertical lines
        print("Test 2: Drawing vertical lines...")
        image = Image.new("RGB", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        
        line_positions = [0, 40, 80, 120, 160, 200, 240, 280]
        for i, x in enumerate(line_positions):
            if x < device.width:
                color = ["red", "green", "blue", "yellow", "cyan", "magenta", "white", "orange"][i % 8]
                draw.line([(x, 0), (x, device.height-1)], fill=color, width=2)
                print(f"  Line at x={x} ({color})")
        
        device.display(image)
        print("Vertical lines displayed - can you see multiple colored lines?")
        time.sleep(5)
        
        # Test 3: Text at different positions
        print("Test 3: Text at different positions...")
        image = Image.new("RGB", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        
        text_lines = [
            (10, 10, "Line 1: Top", "white"),
            (10, 50, "Line 2: Second", "red"),
            (10, 100, "Line 3: Third", "green"),
            (10, 150, "Line 4: Fourth", "blue"),
            (10, 200, "Line 5: Fifth", "yellow"),
            (10, 250, "Line 6: Sixth", "cyan"),
            (10, 300, "Line 7: Seventh", "magenta"),
            (10, 350, "Line 8: Eighth", "orange"),
            (10, 400, "Line 9: Ninth", "white"),
            (10, 450, "Line 10: Bottom", "red")
        ]
        
        for x, y, text, color in text_lines:
            if y < device.height - 20:  # Make sure text fits
                draw.text((x, y), text, fill=color)
                print(f"  Text at y={y}: '{text}' ({color})")
        
        device.display(image)
        print("Multiple text lines displayed - can you see all 10 lines?")
        time.sleep(8)
        
        # Test 4: Gradual fill test
        print("Test 4: Gradual screen fill...")
        for i in range(0, device.height, 20):
            image = Image.new("RGB", (device.width, device.height), "black")
            draw = ImageDraw.Draw(image)
            
            # Fill from top to current position
            draw.rectangle([(0, 0), (device.width-1, i)], fill="blue")
            draw.text((10, 10), f"Filling to line {i}/{device.height}", fill="white")
            
            device.display(image)
            time.sleep(0.3)
        
        print("Gradual fill completed")
        
        # Test 5: Rotation test
        print("Test 5: Testing different rotations...")
        rotations = [0, 1, 2, 3]
        
        for rotation in rotations:
            try:
                device = ili9486(serial, rotate=rotation)
                image = Image.new("RGB", (device.width, device.height), "black")
                draw = ImageDraw.Draw(image)
                
                draw.text((10, 10), f"Rotation: {rotation}", fill="white")
                draw.text((10, 40), f"Size: {device.width}x{device.height}", fill="yellow")
                draw.rectangle([(0, 0), (device.width-1, device.height-1)], outline="red", width=3)
                
                device.display(image)
                print(f"  Rotation {rotation}: {device.width}x{device.height}")
                time.sleep(2)
                
            except Exception as e:
                print(f"  Rotation {rotation} failed: {e}")
        
        # Clear display
        image = Image.new("RGB", (device.width, device.height), "black")
        device.display(image)
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def diagnose_single_line_issue():
    """Provide diagnostic information for single line issues"""
    print("\n" + "="*50)
    print("SINGLE LINE ISSUE DIAGNOSTICS")
    print("="*50)
    
    print("\nPossible causes for only seeing a single line:")
    print("1. DISPLAY TIMING ISSUES:")
    print("   - Try different SPI speeds")
    print("   - Check power supply stability")
    
    print("\n2. WIRING ISSUES:")
    print("   - Double-check all connections")
    print("   - Ensure good solder joints")
    print("   - Check for loose connections")
    
    print("\n3. DISPLAY HARDWARE:")
    print("   - Display may be partially damaged")
    print("   - Incorrect display type (not ILI9486)")
    print("   - Manufacturing defect")
    
    print("\n4. SOFTWARE CONFIGURATION:")
    print("   - Wrong rotation setting")
    print("   - Incorrect resolution")
    print("   - Driver compatibility")
    
    print("\nTROUBLESHOOTING STEPS:")
    print("1. Try different rotation values (0, 1, 2, 3)")
    print("2. Check power supply voltage (should be stable 5V)")
    print("3. Test with different SPI speeds")
    print("4. Verify display part number/model")
    print("5. Try alternative display libraries")

def main():
    print("ILI9486 Single Line Issue Diagnostic")
    print("="*50)
    
    # Run comprehensive line tests
    if test_line_by_line():
        print("\n✓ Line tests completed")
        print("Check your display during the tests:")
        print("- Could you see multiple horizontal lines?")
        print("- Could you see multiple vertical lines?") 
        print("- Could you see multiple text lines?")
        print("- Did the gradual fill work properly?")
        print("- Did any rotation work better?")
    else:
        print("\n✗ Line tests failed")
    
    # Show diagnostic information
    diagnose_single_line_issue()

if __name__ == "__main__":
    main()
