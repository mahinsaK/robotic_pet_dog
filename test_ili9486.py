#!/usr/bin/env python3
"""
ILI9486 Display Test Script
Based on your working display1.py script
Resolution: 320x480
"""
import time
import signal
import sys

try:
    from luma.core.interface.serial import spi
    from luma.lcd.device import ili9486
    from PIL import Image, ImageDraw, ImageFont
    print("✅ Luma libraries imported successfully")
except ImportError as e:
    print("❌ Error importing libraries:")
    print(f"   {e}")
    print("   Install with: pip install luma.lcd pillow")
    sys.exit(1)

class ILI9486Test:
    """ILI9486 Display Test Class"""
    
    def __init__(self):
        self.device = None
        self.width = 320
        self.height = 480
        
    def initialize(self):
        """Initialize the display"""
        try:
            # Create SPI interface with your pin configuration
            serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=17)
            
            # Initialize ILI9486 device
            self.device = ili9486(serial, rotate=0)
            self.width = self.device.width
            self.height = self.device.height
            
            print(f"✅ ILI9486 initialized! Resolution: {self.width}x{self.height}")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing display: {e}")
            return False
    
    def clear_display(self, color="black"):
        """Clear display with specified color"""
        if not self.device:
            print("❌ Display not initialized")
            return False
            
        try:
            image = Image.new("RGB", (self.width, self.height), color)
            self.device.display(image)
            print(f"✅ Display cleared with {color}")
            return True
        except Exception as e:
            print(f"❌ Error clearing display: {e}")
            return False
    
    def test_colors(self):
        """Test different solid colors"""
        if not self.device:
            print("❌ Display not initialized")
            return False
            
        colors = ["red", "green", "blue", "white", "black", "yellow", "cyan", "magenta"]
        
        print("\n🎨 TESTING SOLID COLORS")
        print("-" * 40)
        
        try:
            for color in colors:
                print(f"Displaying {color}...")
                image = Image.new("RGB", (self.width, self.height), color)
                self.device.display(image)
                time.sleep(2)
            
            print("✅ Color test complete")
            return True
        except Exception as e:
            print(f"❌ Color test failed: {e}")
            return False
    
    def test_text_display(self):
        """Test text display"""
        if not self.device:
            print("❌ Display not initialized")
            return False
            
        print("\n📝 TESTING TEXT DISPLAY")
        print("-" * 40)
        
        try:
            image = Image.new("RGB", (self.width, self.height), "black")
            draw = ImageDraw.Draw(image)
            
            # Test various text sizes and colors
            draw.text((10, 10), "ILI9486 Display Test", fill="white")
            draw.text((10, 40), f"Resolution: {self.width}x{self.height}", fill="yellow")
            draw.text((10, 70), "Testing Text Display", fill="green")
            draw.text((10, 100), "Line 4 - Red Text", fill="red")
            draw.text((10, 130), "Line 5 - Blue Text", fill="blue")
            draw.text((10, 160), "Line 6 - Cyan Text", fill="cyan")
            
            # Add some shapes
            draw.rectangle([(10, 200), (310, 250)], outline="white", width=2)
            draw.text((20, 215), "Rectangle with border", fill="white")
            
            draw.ellipse([(10, 270), (100, 360)], outline="yellow", width=3)
            draw.text((120, 310), "Circle", fill="yellow")
            
            self.device.display(image)
            print("✅ Text display test complete")
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"❌ Text display test failed: {e}")
            return False
    
    def test_patterns(self):
        """Test various patterns"""
        if not self.device:
            print("❌ Display not initialized")
            return False
            
        print("\n🎯 TESTING PATTERNS")
        print("-" * 40)
        
        try:
            # Vertical stripes
            print("Testing vertical stripes...")
            image = Image.new("RGB", (self.width, self.height), "black")
            draw = ImageDraw.Draw(image)
            
            for i in range(0, self.width, 20):
                color = "red" if (i // 20) % 2 == 0 else "blue"
                draw.rectangle([(i, 0), (i + 10, self.height)], fill=color)
            
            self.device.display(image)
            time.sleep(3)
            
            # Horizontal stripes
            print("Testing horizontal stripes...")
            image = Image.new("RGB", (self.width, self.height), "black")
            draw = ImageDraw.Draw(image)
            
            for i in range(0, self.height, 20):
                color = "green" if (i // 20) % 2 == 0 else "yellow"
                draw.rectangle([(0, i), (self.width, i + 10)], fill=color)
            
            self.device.display(image)
            time.sleep(3)
            
            # Checkerboard
            print("Testing checkerboard...")
            image = Image.new("RGB", (self.width, self.height), "black")
            draw = ImageDraw.Draw(image)
            
            block_size = 20
            for x in range(0, self.width, block_size):
                for y in range(0, self.height, block_size):
                    if ((x // block_size) + (y // block_size)) % 2 == 0:
                        draw.rectangle([(x, y), (x + block_size, y + block_size)], fill="white")
            
            self.device.display(image)
            time.sleep(3)
            
            print("✅ Pattern test complete")
            return True
            
        except Exception as e:
            print(f"❌ Pattern test failed: {e}")
            return False
    
    def test_animation(self):
        """Test simple animation"""
        if not self.device:
            print("❌ Display not initialized")
            return False
            
        print("\n🌟 TESTING ANIMATION")
        print("-" * 40)
        print("Running animation for 10 seconds...")
        
        try:
            start_time = time.time()
            
            while time.time() - start_time < 10:
                # Moving circle
                t = time.time() - start_time
                x = int((self.width - 50) * (0.5 + 0.5 * math.cos(t)))
                y = int((self.height - 50) * (0.5 + 0.5 * math.sin(t)))
                
                image = Image.new("RGB", (self.width, self.height), "black")
                draw = ImageDraw.Draw(image)
                
                # Draw moving circle
                draw.ellipse([(x, y), (x + 50, y + 50)], fill="red")
                
                # Add time display
                draw.text((10, 10), f"Time: {t:.1f}s", fill="white")
                
                self.device.display(image)
                time.sleep(0.1)
            
            print("✅ Animation test complete")
            return True
            
        except Exception as e:
            print(f"❌ Animation test failed: {e}")
            return False

def signal_handler(signum, frame):
    """Handle Ctrl+C signal"""
    print("\n🛑 Test interrupted by user")
    sys.exit(0)

def main():
    """Main test function"""
    print("📱 ILI9486 DISPLAY TEST SCRIPT")
    print("=" * 40)
    print("Pin Configuration:")
    print("  VCC -> 5V")
    print("  GND -> GND")
    print("  MOSI -> GPIO10")
    print("  SCLK -> GPIO11")
    print("  CS -> GPIO8")
    print("  DC -> GPIO25")
    print("  RST -> GPIO17")
    print("=" * 40)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize display
    display = ILI9486Test()
    
    if not display.initialize():
        print("❌ Failed to initialize display")
        return
    
    try:
        while True:
            print("\n🧪 ILI9486 TEST MENU:")
            print("1. Clear display")
            print("2. Test colors")
            print("3. Test text display")
            print("4. Test patterns")
            print("5. Test animation")
            print("6. Custom color fill")
            print("7. Run all tests")
            print("8. Quit")
            
            choice = input("\nSelect test (1-8): ").strip()
            
            if choice == '1':
                color = input("Enter color (default: black): ").strip() or "black"
                display.clear_display(color)
                
            elif choice == '2':
                display.test_colors()
                
            elif choice == '3':
                display.test_text_display()
                
            elif choice == '4':
                display.test_patterns()
                
            elif choice == '5':
                import math  # Import here for animation
                display.test_animation()
                
            elif choice == '6':
                print("Available colors: red, green, blue, white, black, yellow, cyan, magenta")
                color = input("Enter color: ").strip()
                display.clear_display(color)
                
            elif choice == '7':
                print("\n🏃 RUNNING ALL TESTS")
                print("=" * 40)
                
                tests = [
                    ("Clear Display", lambda: display.clear_display("black")),
                    ("Color Test", display.test_colors),
                    ("Text Display", display.test_text_display),
                    ("Pattern Test", display.test_patterns),
                ]
                
                for test_name, test_func in tests:
                    print(f"\n🔬 Running {test_name}...")
                    if test_func():
                        print(f"✅ {test_name} PASSED")
                    else:
                        print(f"❌ {test_name} FAILED")
                    time.sleep(1)
                
                # Clear at the end
                display.clear_display("black")
                print("\n🏁 All tests complete!")
                
            elif choice == '8':
                print("👋 Goodbye!")
                display.clear_display("black")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-8.")
                
            if choice not in ['7', '8']:
                input("\nPress Enter to continue...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n👋 Test terminated by user")
        if display.device:
            display.clear_display("black")

if __name__ == "__main__":
    main()
