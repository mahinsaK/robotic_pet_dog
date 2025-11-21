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

def test_manual_gpio_control():
    """Test manual GPIO control to verify hardware connections"""
    print("\nTesting manual GPIO control...")
    
    try:
        # Initialize GPIO pins manually
        dc_pin = digitalio.DigitalInOut(board.D25)  # DC
        rst_pin = digitalio.DigitalInOut(board.D17)  # RST
        cs_pin = digitalio.DigitalInOut(board.D8)    # CS
        
        dc_pin.direction = digitalio.Direction.OUTPUT
        rst_pin.direction = digitalio.Direction.OUTPUT
        cs_pin.direction = digitalio.Direction.OUTPUT
        
        print("✓ GPIO pins initialized")
        
        # Test reset sequence
        print("Performing hardware reset...")
        rst_pin.value = True
        time.sleep(0.1)
        rst_pin.value = False
        time.sleep(0.1) 
        rst_pin.value = True
        time.sleep(0.1)
        print("✓ Reset sequence completed")
        
        # Test CS pin
        print("Testing CS pin...")
        cs_pin.value = True
        time.sleep(0.1)
        cs_pin.value = False
        time.sleep(0.1)
        cs_pin.value = True
        print("✓ CS pin test completed")
        
        # Test DC pin
        print("Testing DC pin...")
        dc_pin.value = False  # Command mode
        time.sleep(0.1)
        dc_pin.value = True   # Data mode
        time.sleep(0.1)
        print("✓ DC pin test completed")
        
        return True
        
    except Exception as e:
        print(f"✗ GPIO test failed: {e}")
        return False
        print("✓ SPI interface accessible")
        spi_device.close()
        return True
    except Exception as e:
        print(f"✗ SPI interface error: {e}")
        return False

def test_gpio_availability():
    """Test GPIO availability"""
    print("\n=== GPIO Test ===")
    try:
        import RPi.GPIO as GPIO
        print("✓ RPi.GPIO available")
        return True
    except Exception as e:
        print(f"✗ RPi.GPIO error: {e}")
        print("  Try: sudo apt install python3-rpi.gpio")
        return False

def test_display_configurations():
    """Test different display configurations"""
    print("\n=== Display Configuration Tests ===")
    
    # Configuration options to try
    configs = [
        {"name": "Default pins", "gpio_DC": 24, "gpio_RST": 25},
        {"name": "Alternative pins", "gpio_DC": 23, "gpio_RST": 24},
        {"name": "No RST pin", "gpio_DC": 24, "gpio_RST": None},
        {"name": "Different SPI device", "gpio_DC": 24, "gpio_RST": 25, "device": 1},
    ]
    
    for i, config in enumerate(configs):
        print(f"\nTesting configuration {i+1}: {config['name']}")
        try:
            # Create SPI interface
            device_num = config.get('device', 0)
            serial = spi(
                port=0, 
                device=device_num, 
                gpio_DC=config['gpio_DC'], 
                gpio_RST=config['gpio_RST']
            )
            
            # Try to initialize display
            device = ili9486(serial, rotate=0)
            print(f"✓ Display initialized: {device.width}x{device.height}")
            
            # Test basic display
            test_basic_display(device, f"Config {i+1}")
            return device, serial
            
        except Exception as e:
            print(f"✗ Configuration failed: {e}")
    
    return None, None

def test_basic_display(device, label):
    """Test basic display functionality"""
    try:
        # Create a simple test image
        image = Image.new("RGB", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        
        # Draw test pattern
        draw.rectangle([(5, 5), (device.width-5, device.height-5)], outline="white", width=3)
        draw.text((10, 10), f"Test: {label}", fill="white")
        draw.text((10, 40), f"Size: {device.width}x{device.height}", fill="yellow")
        
        # Draw colored squares
        colors = ["red", "green", "blue", "yellow", "cyan", "magenta"]
        square_size = 40
        for i, color in enumerate(colors):
            x = 10 + (i % 3) * (square_size + 10)
            y = 80 + (i // 3) * (square_size + 10)
            draw.rectangle([(x, y), (x + square_size, y + square_size)], fill=color)
        
        # Display the image
        device.display(image)
        print(f"✓ Test pattern displayed for {label}")
        time.sleep(3)
        
        # Clear display
        clear_image = Image.new("RGB", (device.width, device.height), "black")
        device.display(clear_image)
        print("✓ Display cleared")
        
        return True
        
    except Exception as e:
        print(f"✗ Display test failed: {e}")
        return False

def check_system_setup():
    """Check system requirements"""
    print("=== System Setup Check ===")
    
    # Check if SPI is enabled
    try:
        with open('/boot/config.txt', 'r') as f:
            config_content = f.read()
            if 'dtparam=spi=on' in config_content:
                print("✓ SPI enabled in /boot/config.txt")
            else:
                print("✗ SPI not enabled in /boot/config.txt")
                print("  Add 'dtparam=spi=on' to /boot/config.txt and reboot")
    except:
        print("? Could not check /boot/config.txt")
    
    # Check SPI devices
    import os
    if os.path.exists('/dev/spidev0.0'):
        print("✓ SPI device /dev/spidev0.0 exists")
    else:
        print("✗ SPI device /dev/spidev0.0 not found")
    
    if os.path.exists('/dev/spidev0.1'):
        print("✓ SPI device /dev/spidev0.1 exists")

def main():
    print("TFT Display Troubleshooting for ILI9486")
    print("=" * 50)
    
    # System checks
    check_system_setup()
    
    # Test components
    spi_ok = test_spi_interface()
    gpio_ok = test_gpio_availability()
    
    if not spi_ok:
        print("\n⚠️  SPI interface issues detected. Please check:")
        print("   1. Is SPI enabled? Run: sudo raspi-config -> Interface Options -> SPI -> Enable")
        print("   2. Reboot after enabling SPI")
        return
    
    if not gpio_ok:
        print("\n⚠️  GPIO issues detected. Install RPi.GPIO:")
        print("   sudo apt update && sudo apt install python3-rpi.gpio")
        return
    
    # Test display configurations
    device, serial = test_display_configurations()
    
    if device:
        print("\n🎉 Success! Display is working!")
        print("\nHardware connection summary:")
        print("   VCC -> 5V or 3.3V")
        print("   GND -> Ground")
        print("   CS  -> GPIO 8 (SPI0 CE0)")
        print("   RST -> GPIO 25 (or as configured)")
        print("   DC  -> GPIO 24 (or as configured)")
        print("   SDI -> GPIO 10 (SPI0 MOSI)")
        print("   SCK -> GPIO 11 (SPI0 SCLK)")
        print("   LED -> 3.3V (backlight)")
    else:
        print("\n❌ Could not initialize display. Check:")
        print("   1. Hardware connections")
        print("   2. Power supply (5V/3.3V)")
        print("   3. SPI wiring")
        print("   4. GPIO pin assignments")
        print("\nCommon ILI9486 pin connections:")
        print("   Display -> Raspberry Pi")
        print("   VCC     -> 5V (Pin 2) or 3.3V (Pin 1)")
        print("   GND     -> Ground (Pin 6)")
        print("   CS      -> GPIO 8 (Pin 24)")
        print("   RST     -> GPIO 25 (Pin 22)")
        print("   DC      -> GPIO 24 (Pin 18)")
        print("   SDI     -> GPIO 10 (Pin 19)")
        print("   SCK     -> GPIO 11 (Pin 23)")
        print("   LED     -> 3.3V (Pin 17) for backlight")

if __name__ == "__main__":
    main()
