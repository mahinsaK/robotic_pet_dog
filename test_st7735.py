#!/usr/bin/env python3
"""
ST7735 Specific Test Script
Based on your display responding to ST7735 commands
"""
import time
import signal
import sys
import RPi.GPIO as GPIO
import spidev

# Display pin configuration
DC_PIN = 25     # Data/Command pin
RST_PIN = 17    # Reset pin
CS_PIN = 8      # Chip Select (SPI0_CE0)

# SPI configuration
SPI_BUS = 0
SPI_DEVICE = 0
SPI_MAX_SPEED_HZ = 4000000  # Slower speed for stability

class ST7735Display:
    """ST7735 Display Controller"""
    
    def __init__(self):
        self.spi = None
        self.width = 128
        self.height = 160
        GPIO.setwarnings(False)
        
    def initialize(self):
        """Initialize GPIO and SPI"""
        try:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(DC_PIN, GPIO.OUT)
            GPIO.setup(RST_PIN, GPIO.OUT)
            
            # Setup SPI
            self.spi = spidev.SpiDev()
            self.spi.open(SPI_BUS, SPI_DEVICE)
            self.spi.max_speed_hz = SPI_MAX_SPEED_HZ
            self.spi.mode = 0b00
            
            print("✅ ST7735 interface initialized")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing: {e}")
            return False
    
    def reset_display(self):
        """Hardware reset"""
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
    
    def send_command(self, cmd):
        """Send command"""
        GPIO.output(DC_PIN, GPIO.LOW)
        self.spi.xfer2([cmd])
    
    def send_data(self, data):
        """Send data"""
        GPIO.output(DC_PIN, GPIO.HIGH)
        if isinstance(data, (list, tuple)):
            self.spi.xfer2(list(data))
        else:
            self.spi.xfer2([data])
    
    def initialize_st7735(self):
        """Proper ST7735 initialization sequence"""
        print("🚀 Initializing ST7735...")
        
        self.reset_display()
        
        # ST7735 initialization sequence
        self.send_command(0x01)  # Software reset
        time.sleep(0.15)
        
        self.send_command(0x11)  # Sleep out
        time.sleep(0.5)
        
        # Frame rate control
        self.send_command(0xB1)
        self.send_data([0x01, 0x2C, 0x2D])
        
        self.send_command(0xB2)
        self.send_data([0x01, 0x2C, 0x2D])
        
        self.send_command(0xB3)
        self.send_data([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D])
        
        # Column inversion
        self.send_command(0xB4)
        self.send_data([0x07])
        
        # Power control
        self.send_command(0xC0)
        self.send_data([0xA2, 0x02, 0x84])
        
        self.send_command(0xC1)
        self.send_data([0xC5])
        
        self.send_command(0xC2)
        self.send_data([0x0A, 0x00])
        
        self.send_command(0xC3)
        self.send_data([0x8A, 0x2A])
        
        self.send_command(0xC4)
        self.send_data([0x8A, 0xEE])
        
        # VCOM control
        self.send_command(0xC5)
        self.send_data([0x0E])
        
        # Memory access control
        self.send_command(0x36)
        self.send_data([0xC8])  # RGB order, row/col exchange
        
        # Color mode - 16bit
        self.send_command(0x3A)
        self.send_data([0x05])
        
        # Gamma correction
        self.send_command(0xE0)
        self.send_data([0x02, 0x1C, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2D,
                       0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10])
        
        self.send_command(0xE1)
        self.send_data([0x03, 0x1D, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D,
                       0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10])
        
        # Display on
        self.send_command(0x29)
        time.sleep(0.1)
        
        print("✅ ST7735 initialization complete")
    
    def set_window(self, x0, y0, x1, y1):
        """Set display window"""
        self.send_command(0x2A)  # Column address set
        self.send_data([0x00, x0, 0x00, x1])
        
        self.send_command(0x2B)  # Row address set
        self.send_data([0x00, y0, 0x00, y1])
        
        self.send_command(0x2C)  # Memory write
    
    def fill_screen(self, color):
        """Fill entire screen with color"""
        print(f"Filling screen with color: {color}")
        
        # Set full screen window
        self.set_window(0, 0, self.width-1, self.height-1)
        
        # Convert color to RGB565 bytes
        if color == "red":
            pixel = [0xF8, 0x00]
        elif color == "green":
            pixel = [0x07, 0xE0]
        elif color == "blue":
            pixel = [0x00, 0x1F]
        elif color == "white":
            pixel = [0xFF, 0xFF]
        elif color == "black":
            pixel = [0x00, 0x00]
        elif color == "yellow":
            pixel = [0xFF, 0xE0]
        elif color == "cyan":
            pixel = [0x07, 0xFF]
        elif color == "magenta":
            pixel = [0xF8, 0x1F]
        else:
            pixel = [0x00, 0x00]  # default to black
        
        # Fill screen
        total_pixels = self.width * self.height
        
        # Send in chunks for efficiency
        chunk_size = 1024
        pixels_per_chunk = chunk_size // 2
        
        for chunk_start in range(0, total_pixels, pixels_per_chunk):
            pixels_in_chunk = min(pixels_per_chunk, total_pixels - chunk_start)
            chunk_data = pixel * pixels_in_chunk
            self.send_data(chunk_data)
            
            if chunk_start % 5000 == 0:
                print(f"  Progress: {chunk_start}/{total_pixels} pixels")
    
    def test_colors(self):
        """Test different colors"""
        print("\n🎨 TESTING COLORS")
        print("-" * 30)
        
        colors = ["red", "green", "blue", "white", "black", "yellow", "cyan", "magenta"]
        
        for color in colors:
            print(f"Testing {color}...")
            self.fill_screen(color)
            time.sleep(2)
    
    def test_pattern(self):
        """Test a simple pattern"""
        print("\n🎯 TESTING PATTERN")
        print("-" * 30)
        
        # Set window
        self.set_window(0, 0, self.width-1, self.height-1)
        
        # Create a striped pattern
        red = [0xF8, 0x00]
        blue = [0x00, 0x1F]
        
        stripe_height = 10
        
        for y in range(self.height):
            if (y // stripe_height) % 2 == 0:
                row_data = red * self.width
            else:
                row_data = blue * self.width
            self.send_data(row_data)
        
        print("✅ Pattern test complete")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.spi:
                self.spi.close()
            GPIO.cleanup()
        except:
            pass

def main():
    """Main function"""
    print("📱 ST7735 DISPLAY TEST")
    print("=" * 30)
    
    display = ST7735Display()
    
    if not display.initialize():
        return
    
    try:
        while True:
            print("\n🧪 ST7735 TEST MENU:")
            print("1. Initialize display")
            print("2. Test colors")
            print("3. Test pattern")
            print("4. Fill with specific color")
            print("5. Clear (black)")
            print("6. Full test sequence")
            print("7. Quit")
            
            choice = input("\nSelect test (1-7): ").strip()
            
            if choice == '1':
                display.initialize_st7735()
                
            elif choice == '2':
                display.test_colors()
                
            elif choice == '3':
                display.test_pattern()
                
            elif choice == '4':
                print("Available colors: red, green, blue, white, black, yellow, cyan, magenta")
                color = input("Enter color: ").strip().lower()
                display.fill_screen(color)
                
            elif choice == '5':
                display.fill_screen("black")
                
            elif choice == '6':
                print("\n🏃 RUNNING FULL TEST")
                print("=" * 30)
                display.initialize_st7735()
                time.sleep(1)
                display.test_colors()
                time.sleep(1)
                display.test_pattern()
                time.sleep(2)
                display.fill_screen("black")
                
            elif choice == '7':
                break
                
            else:
                print("❌ Invalid choice")
                
            if choice != '6':
                input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        display.cleanup()

if __name__ == "__main__":
    main()
