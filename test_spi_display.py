#!/usr/bin/env python3
"""
RPi SPI Display Test Script
Tests SPI display functionality with the following connections:
VCC -> 5V
GND -> GND
MOSI -> GPIO10 (SPI0_MOSI)
SCLK -> GPIO11 (SPI0_SCLK) 
CS -> GPIO8 (SPI0_CE0)
DC -> GPIO25 (Data/Command)
RST -> GPIO17 (Reset)
"""
import time
import signal
import sys
import random
import math

try:
    import RPi.GPIO as GPIO
    print("✅ RPi.GPIO imported successfully")
except ImportError as e:
    print("❌ Error importing RPi.GPIO:")
    print(f"   {e}")
    sys.exit(1)

try:
    import spidev
    print("✅ spidev imported successfully")
except ImportError as e:
    print("❌ Error importing spidev:")
    print(f"   {e}")
    print("   Install with: sudo apt-get install python3-spidev")
    sys.exit(1)

# Try to import additional display libraries
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
    print("✅ PIL/Pillow imported successfully")
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL/Pillow not available - install with: pip install Pillow")

# Display pin configuration
DC_PIN = 25     # Data/Command pin
RST_PIN = 17    # Reset pin
CS_PIN = 8      # Chip Select (SPI0_CE0)
MOSI_PIN = 10   # SPI0_MOSI
SCLK_PIN = 11   # SPI0_SCLK

# SPI configuration
SPI_BUS = 0
SPI_DEVICE = 0
SPI_MAX_SPEED_HZ = 8000000  # 8MHz

# Display dimensions (common sizes - adjust as needed)
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64

class RPiDisplay:
    """RPi Display controller class"""
    
    def __init__(self):
        self.spi = None
        self.width = DISPLAY_WIDTH
        self.height = DISPLAY_HEIGHT
        
    def initialize(self):
        """Initialize GPIO and SPI"""
        try:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(DC_PIN, GPIO.OUT)
            GPIO.setup(RST_PIN, GPIO.OUT)
            print(f"✅ GPIO pins configured - DC: {DC_PIN}, RST: {RST_PIN}")
            
            # Setup SPI
            self.spi = spidev.SpiDev()
            self.spi.open(SPI_BUS, SPI_DEVICE)
            self.spi.max_speed_hz = SPI_MAX_SPEED_HZ
            self.spi.mode = 0b00  # SPI mode 0
            print(f"✅ SPI configured - Bus: {SPI_BUS}, Device: {SPI_DEVICE}, Speed: {SPI_MAX_SPEED_HZ}Hz")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing display: {e}")
            return False
    
    def reset_display(self):
        """Hardware reset of the display"""
        print("🔄 Performing hardware reset...")
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
        print("✅ Hardware reset complete")
    
    def send_command(self, cmd):
        """Send command to display"""
        GPIO.output(DC_PIN, GPIO.LOW)  # Command mode
        if isinstance(cmd, int):
            self.spi.xfer2([cmd])
        else:
            self.spi.xfer2(cmd)
    
    def send_data(self, data):
        """Send data to display"""
        GPIO.output(DC_PIN, GPIO.HIGH)  # Data mode
        if isinstance(data, int):
            self.spi.xfer2([data])
        elif isinstance(data, (list, tuple)):
            self.spi.xfer2(list(data))
        else:
            self.spi.xfer2([data])
    
    def test_spi_communication(self):
        """Test basic SPI communication"""
        print("\n📡 TESTING SPI COMMUNICATION")
        print("-" * 40)
        
        try:
            # Test sending various commands
            test_commands = [0x00, 0xFF, 0xAA, 0x55]
            
            for cmd in test_commands:
                print(f"Sending command: 0x{cmd:02X}")
                self.send_command(cmd)
                time.sleep(0.01)
            
            print("✅ SPI communication test complete")
            return True
            
        except Exception as e:
            print(f"❌ SPI communication test failed: {e}")
            return False
    
    def test_gpio_pins(self):
        """Test GPIO pin control"""
        print("\n🔌 TESTING GPIO PIN CONTROL")
        print("-" * 40)
        
        try:
            # Test DC pin
            print("Testing DC pin (Data/Command)...")
            for i in range(5):
                GPIO.output(DC_PIN, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(DC_PIN, GPIO.LOW)
                time.sleep(0.1)
            print("✅ DC pin test complete")
            
            # Test RST pin
            print("Testing RST pin (Reset)...")
            for i in range(3):
                GPIO.output(RST_PIN, GPIO.LOW)
                time.sleep(0.1)
                GPIO.output(RST_PIN, GPIO.HIGH)
                time.sleep(0.1)
            print("✅ RST pin test complete")
            
            return True
            
        except Exception as e:
            print(f"❌ GPIO pin test failed: {e}")
            return False
    
    def send_initialization_sequence(self):
        """Send common initialization commands"""
        print("\n🚀 SENDING INITIALIZATION SEQUENCE")
        print("-" * 40)
        
        try:
            # Common initialization sequence for many SPI displays
            init_commands = [
                0xAE,  # Display OFF
                0x20, 0x00,  # Set Memory Addressing Mode
                0xB0,  # Set Page Start Address
                0xC8,  # Set COM Output Scan Direction
                0x00,  # Set low column address
                0x10,  # Set high column address
                0x40,  # Set start line address
                0x81, 0xFF,  # Set contrast control
                0xA1,  # Set segment re-map
                0xA6,  # Set normal display
                0xA8, 0x3F,  # Set multiplex ratio
                0xA4,  # Output follows RAM content
                0xD3, 0x00,  # Set display offset
                0xD5, 0xF0,  # Set display clock divide ratio
                0xD9, 0x22,  # Set pre-charge period
                0xDA, 0x12,  # Set com pins hardware configuration
                0xDB, 0x20,  # Set vcomh
                0x8D, 0x14,  # Set DC-DC enable
                0xAF   # Display ON
            ]
            
            print("Sending initialization commands...")
            for i, cmd in enumerate(init_commands):
                self.send_command(cmd)
                time.sleep(0.001)  # Small delay between commands
                if (i + 1) % 5 == 0:
                    print(f"  Sent {i + 1}/{len(init_commands)} commands")
            
            print("✅ Initialization sequence complete")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def clear_display(self):
        """Clear the display"""
        print("🧹 Clearing display...")
        try:
            # Send clear data (all zeros)
            clear_data = [0x00] * (self.width * self.height // 8)
            self.send_data(clear_data)
            print("✅ Display cleared")
            return True
        except Exception as e:
            print(f"❌ Clear display failed: {e}")
            return False
    
    def fill_display(self, pattern=0xFF):
        """Fill display with pattern"""
        print(f"🎨 Filling display with pattern 0x{pattern:02X}...")
        try:
            # Send pattern data
            fill_data = [pattern] * (self.width * self.height // 8)
            self.send_data(fill_data)
            print("✅ Display filled")
            return True
        except Exception as e:
            print(f"❌ Fill display failed: {e}")
            return False
    
    def test_patterns(self):
        """Test various display patterns"""
        print("\n🎨 TESTING DISPLAY PATTERNS")
        print("-" * 40)
        
        patterns = [
            (0x00, "All OFF"),
            (0xFF, "All ON"),
            (0xAA, "Checkerboard 1"),
            (0x55, "Checkerboard 2"),
            (0xF0, "Top half"),
            (0x0F, "Bottom half")
        ]
        
        try:
            for pattern, description in patterns:
                print(f"Testing pattern: {description}")
                self.fill_display(pattern)
                time.sleep(1)
            
            # Clear at the end
            self.clear_display()
            print("✅ Pattern test complete")
            return True
            
        except Exception as e:
            print(f"❌ Pattern test failed: {e}")
            return False
    
    def test_animated_pattern(self):
        """Test animated patterns"""
        print("\n🌟 TESTING ANIMATED PATTERNS")
        print("-" * 40)
        print("Running animation for 10 seconds...")
        
        try:
            start_time = time.time()
            frame = 0
            
            while time.time() - start_time < 10:
                # Create shifting pattern
                pattern = 0xFF >> (frame % 8)
                self.fill_display(pattern)
                frame += 1
                time.sleep(0.2)
                
                if frame % 10 == 0:
                    print(f"  Frame {frame}")
            
            self.clear_display()
            print("✅ Animation test complete")
            return True
            
        except Exception as e:
            print(f"❌ Animation test failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.spi:
                self.spi.close()
            GPIO.cleanup()
            print("✅ Cleanup complete")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

def signal_handler(signum, frame):
    """Handle Ctrl+C signal"""
    print("\n🛑 Test interrupted by user")
    if 'display' in globals():
        display.cleanup()
    sys.exit(0)

def check_spi_interface():
    """Check if SPI interface is enabled"""
    print("🔍 CHECKING SPI INTERFACE")
    print("-" * 40)
    
    try:
        # Check if SPI device exists
        import os
        spi_device = f"/dev/spidev{SPI_BUS}.{SPI_DEVICE}"
        
        if os.path.exists(spi_device):
            print(f"✅ SPI device found: {spi_device}")
            return True
        else:
            print(f"❌ SPI device not found: {spi_device}")
            print("   Enable SPI with: sudo raspi-config -> Interface Options -> SPI")
            return False
            
    except Exception as e:
        print(f"❌ Error checking SPI interface: {e}")
        return False

def main():
    """Main test function"""
    print("🖥️  RPI SPI DISPLAY TEST SCRIPT")
    print("=" * 50)
    print("Pin Configuration:")
    print(f"  VCC -> 5V")
    print(f"  GND -> GND")
    print(f"  MOSI -> GPIO{MOSI_PIN}")
    print(f"  SCLK -> GPIO{SCLK_PIN}")
    print(f"  CS -> GPIO{CS_PIN}")
    print(f"  DC -> GPIO{DC_PIN}")
    print(f"  RST -> GPIO{RST_PIN}")
    print("=" * 50)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check SPI interface
    if not check_spi_interface():
        print("❌ SPI interface check failed")
        return
    
    # Initialize display
    global display
    display = RPiDisplay()
    
    if not display.initialize():
        print("❌ Display initialization failed")
        return
    
    try:
        while True:
            print("\n🧪 DISPLAY TEST MENU:")
            print("1. Hardware reset test")
            print("2. GPIO pin test")
            print("3. SPI communication test")
            print("4. Send initialization sequence")
            print("5. Clear display")
            print("6. Fill display")
            print("7. Pattern tests")
            print("8. Animated pattern test")
            print("9. Full test sequence")
            print("10. Quit")
            
            choice = input("\nSelect test (1-10): ").strip()
            
            if choice == '1':
                display.reset_display()
                
            elif choice == '2':
                display.test_gpio_pins()
                
            elif choice == '3':
                display.test_spi_communication()
                
            elif choice == '4':
                display.send_initialization_sequence()
                
            elif choice == '5':
                display.clear_display()
                
            elif choice == '6':
                pattern = input("Enter fill pattern (hex, e.g., FF): ").strip()
                try:
                    pattern_val = int(pattern, 16) if pattern else 0xFF
                    display.fill_display(pattern_val)
                except ValueError:
                    print("❌ Invalid hex pattern")
                
            elif choice == '7':
                display.test_patterns()
                
            elif choice == '8':
                display.test_animated_pattern()
                
            elif choice == '9':
                print("\n🏃 RUNNING FULL TEST SEQUENCE")
                print("=" * 50)
                
                tests = [
                    ("Hardware Reset", display.reset_display),
                    ("GPIO Pins", display.test_gpio_pins),
                    ("SPI Communication", display.test_spi_communication),
                    ("Initialization", display.send_initialization_sequence),
                    ("Pattern Tests", display.test_patterns),
                ]
                
                for test_name, test_func in tests:
                    print(f"\n🔬 Running {test_name} test...")
                    if test_func():
                        print(f"✅ {test_name} test PASSED")
                    else:
                        print(f"❌ {test_name} test FAILED")
                    time.sleep(1)
                
                print("\n🏁 Full test sequence complete!")
                
            elif choice == '10':
                break
                
            else:
                print("❌ Invalid choice. Please select 1-10.")
                
            if choice != '9':  # Skip for full test
                input("\nPress Enter to continue...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        display.cleanup()

if __name__ == "__main__":
    main()
