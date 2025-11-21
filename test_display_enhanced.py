#!/usr/bin/env python3
"""
Enhanced Display Test Script - Multiple Display Type Support
Tests various display types and initialization sequences
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
SPI_MAX_SPEED_HZ = 8000000  # 8MHz

class EnhancedDisplayTest:
    """Enhanced display test with multiple display type support"""
    
    def __init__(self):
        self.spi = None
        GPIO.setwarnings(False)  # Disable GPIO warnings
        
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
            self.spi.mode = 0b00  # SPI mode 0
            
            print("✅ Display interface initialized")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing: {e}")
            return False
    
    def reset_display(self):
        """Hardware reset of the display"""
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
    
    def send_command(self, cmd):
        """Send command to display"""
        GPIO.output(DC_PIN, GPIO.LOW)  # Command mode
        if isinstance(cmd, (list, tuple)):
            self.spi.xfer2(list(cmd))
        else:
            self.spi.xfer2([cmd])
    
    def send_data(self, data):
        """Send data to display"""
        GPIO.output(DC_PIN, GPIO.HIGH)  # Data mode
        if isinstance(data, (list, tuple)):
            self.spi.xfer2(list(data))
        else:
            self.spi.xfer2([data])
    
    def test_ssd1306_128x64(self):
        """Test SSD1306 OLED 128x64 display"""
        print("\n🖥️  TESTING SSD1306 OLED 128x64")
        print("-" * 40)
        
        try:
            self.reset_display()
            
            # SSD1306 initialization sequence
            init_sequence = [
                0xAE,        # Display OFF
                0xD5, 0x80,  # Set display clock divide ratio
                0xA8, 0x3F,  # Set multiplex ratio (1 to 64)
                0xD3, 0x00,  # Set display offset
                0x40,        # Set start line address
                0x8D, 0x14,  # Charge pump setting
                0x20, 0x00,  # Memory addressing mode
                0xA1,        # Set segment re-map
                0xC8,        # Set COM output scan direction
                0xDA, 0x12,  # Set COM pins hardware configuration
                0x81, 0xCF,  # Set contrast control
                0xD9, 0xF1,  # Set pre-charge period
                0xDB, 0x40,  # Set VCOMH deselect level
                0xA4,        # Display follows RAM content
                0xA6,        # Set normal display
                0xAF         # Display ON
            ]
            
            for cmd in init_sequence:
                self.send_command(cmd)
                time.sleep(0.001)
            
            # Test pattern
            print("Sending test pattern...")
            test_pattern = [0xFF if (i // 8) % 2 == 0 else 0x00 for i in range(1024)]
            
            # Set column address
            self.send_command([0x21, 0x00, 0x7F])
            # Set page address  
            self.send_command([0x22, 0x00, 0x07])
            
            # Send pattern data
            self.send_data(test_pattern)
            
            print("✅ SSD1306 test complete")
            return True
            
        except Exception as e:
            print(f"❌ SSD1306 test failed: {e}")
            return False
    
    def test_st7735_128x160(self):
        """Test ST7735 TFT 128x160 display"""
        print("\n🖥️  TESTING ST7735 TFT 128x160")
        print("-" * 40)
        
        try:
            self.reset_display()
            
            # ST7735 initialization sequence
            init_sequence = [
                (0x01, []),           # Software reset
                (0x11, []),           # Sleep out
                (0x3A, [0x05]),       # Set color mode - 16bit
                (0x36, [0x00]),       # Memory access control
                (0x29, []),           # Display on
            ]
            
            for cmd, data in init_sequence:
                self.send_command(cmd)
                if data:
                    self.send_data(data)
                time.sleep(0.1)
            
            # Set window
            self.send_command(0x2A)  # Column address set
            self.send_data([0x00, 0x00, 0x00, 0x7F])  # 0 to 127
            
            self.send_command(0x2B)  # Row address set  
            self.send_data([0x00, 0x00, 0x00, 0x9F])  # 0 to 159
            
            self.send_command(0x2C)  # Memory write
            
            # Send test pattern (red screen)
            red_pixel = [0xF8, 0x00]  # Red in RGB565
            pattern = red_pixel * (128 * 160)
            
            print("Sending red test pattern...")
            chunk_size = 1024
            for i in range(0, len(pattern), chunk_size):
                chunk = pattern[i:i+chunk_size]
                self.send_data(chunk)
            
            print("✅ ST7735 test complete")
            return True
            
        except Exception as e:
            print(f"❌ ST7735 test failed: {e}")
            return False
    
    def test_ili9341_240x320(self):
        """Test ILI9341 TFT 240x320 display"""
        print("\n🖥️  TESTING ILI9341 TFT 240x320")
        print("-" * 40)
        
        try:
            self.reset_display()
            
            # ILI9341 initialization sequence
            init_commands = [
                (0xEF, [0x03, 0x80, 0x02]),
                (0xCF, [0x00, 0xC1, 0x30]),
                (0xED, [0x64, 0x03, 0x12, 0x81]),
                (0xE8, [0x85, 0x00, 0x78]),
                (0xCB, [0x39, 0x2C, 0x00, 0x34, 0x02]),
                (0xF7, [0x20]),
                (0xEA, [0x00, 0x00]),
                (0xC0, [0x23]),           # Power control VRH[5:0]
                (0xC1, [0x10]),           # Power control SAP[2:0];BT[3:0]
                (0xC5, [0x3e, 0x28]),     # VCM control
                (0xC7, [0x86]),           # VCM control2
                (0x36, [0x48]),           # Memory Access Control
                (0x3A, [0x55]),           # Pixel Format
                (0xB1, [0x00, 0x18]),     # Frame Rate Control
                (0xB6, [0x08, 0x82, 0x27]), # Display Function Control
                (0xF2, [0x00]),           # 3Gamma Function Disable
                (0x26, [0x01]),           # Gamma curve selected
                (0xE0, [0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E, 0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00]),
                (0xE1, [0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31, 0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F]),
                (0x11, []),               # Sleep out
                (0x29, []),               # Display on
            ]
            
            for cmd, data in init_commands:
                self.send_command(cmd)
                if data:
                    self.send_data(data)
                time.sleep(0.001)
            
            time.sleep(0.12)  # Wait for display to wake up
            
            # Set window and fill with blue
            self.send_command(0x2A)  # Column address set
            self.send_data([0x00, 0x00, 0x00, 0xEF])  # 0 to 239
            
            self.send_command(0x2B)  # Row address set
            self.send_data([0x00, 0x00, 0x01, 0x3F])  # 0 to 319
            
            self.send_command(0x2C)  # Memory write
            
            # Send blue pattern
            blue_pixel = [0x00, 0x1F]  # Blue in RGB565
            print("Sending blue test pattern...")
            
            # Send in chunks
            for row in range(320):
                row_data = blue_pixel * 240
                self.send_data(row_data)
                if row % 50 == 0:
                    print(f"  Row {row}/320")
            
            print("✅ ILI9341 test complete")
            return True
            
        except Exception as e:
            print(f"❌ ILI9341 test failed: {e}")
            return False
    
    def test_generic_display(self):
        """Test with generic commands that work on many displays"""
        print("\n🖥️  TESTING GENERIC DISPLAY COMMANDS")
        print("-" * 40)
        
        try:
            self.reset_display()
            
            # Try common wake-up commands
            wake_commands = [0x11, 0x29, 0xAF, 0xA4, 0xA6]
            
            for cmd in wake_commands:
                print(f"Sending wake command: 0x{cmd:02X}")
                self.send_command(cmd)
                time.sleep(0.1)
            
            # Try to fill with pattern
            print("Sending test data...")
            test_data = [0xFF] * 1000  # 1000 bytes of 0xFF
            self.send_data(test_data)
            
            print("✅ Generic test complete")
            return True
            
        except Exception as e:
            print(f"❌ Generic test failed: {e}")
            return False
    
    def voltage_test(self):
        """Test different voltage scenarios"""
        print("\n⚡ VOLTAGE/POWER TEST")
        print("-" * 40)
        print("This test will toggle reset and DC pins to help identify power issues")
        
        try:
            for i in range(10):
                print(f"Cycle {i+1}/10")
                
                # Toggle reset
                GPIO.output(RST_PIN, GPIO.LOW)
                time.sleep(0.5)
                GPIO.output(RST_PIN, GPIO.HIGH)
                time.sleep(0.5)
                
                # Toggle DC
                GPIO.output(DC_PIN, GPIO.LOW)
                time.sleep(0.2)
                GPIO.output(DC_PIN, GPIO.HIGH)
                time.sleep(0.2)
                
                # Send some data
                self.send_command(0x00)
                self.send_data([0xFF, 0x00, 0xFF, 0x00])
                
            print("✅ Voltage test complete")
            print("📝 Check if any LEDs or indicators on display responded")
            return True
            
        except Exception as e:
            print(f"❌ Voltage test failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.spi:
                self.spi.close()
            GPIO.cleanup()
        except:
            pass

def main():
    """Main test function"""
    print("🔍 ENHANCED DISPLAY DIAGNOSTIC TOOL")
    print("=" * 50)
    
    display = EnhancedDisplayTest()
    
    if not display.initialize():
        return
    
    try:
        while True:
            print("\n🧪 ENHANCED TEST MENU:")
            print("1. Test SSD1306 OLED (128x64)")
            print("2. Test ST7735 TFT (128x160)")
            print("3. Test ILI9341 TFT (240x320)")
            print("4. Test Generic Display")
            print("5. Voltage/Power Test")
            print("6. Run All Tests")
            print("7. Quit")
            
            choice = input("\nSelect test (1-7): ").strip()
            
            if choice == '1':
                display.test_ssd1306_128x64()
            elif choice == '2':
                display.test_st7735_128x160()
            elif choice == '3':
                display.test_ili9341_240x320()
            elif choice == '4':
                display.test_generic_display()
            elif choice == '5':
                display.voltage_test()
            elif choice == '6':
                print("\n🏃 RUNNING ALL DISPLAY TESTS")
                print("=" * 50)
                
                tests = [
                    ("SSD1306 OLED", display.test_ssd1306_128x64),
                    ("ST7735 TFT", display.test_st7735_128x160),
                    ("ILI9341 TFT", display.test_ili9341_240x320),
                    ("Generic Display", display.test_generic_display),
                    ("Voltage Test", display.voltage_test),
                ]
                
                for test_name, test_func in tests:
                    print(f"\n🔬 Testing {test_name}...")
                    result = test_func()
                    print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
                    time.sleep(2)
                    
                    # Ask user if they saw anything
                    response = input(f"Did you see anything on the display during {test_name} test? (y/n): ").strip().lower()
                    if response == 'y':
                        print(f"🎉 SUCCESS! Display appears to be {test_name}")
                        break
                
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
