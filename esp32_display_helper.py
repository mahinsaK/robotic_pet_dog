#!/usr/bin/env python3
"""
ESP32 TFT Display Helper
Since your display works with ESP32, this helps with development
"""

def generate_esp32_test_code():
    """Generate ESP32 Arduino code for different tests"""
    
    tests = {
        "basic_colors": '''
#include <TFT_eSPI.h>
TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);
  tft.init();
  
  // Test all basic colors
  uint16_t colors[] = {TFT_RED, TFT_GREEN, TFT_BLUE, TFT_YELLOW, TFT_CYAN, TFT_MAGENTA, TFT_WHITE, TFT_BLACK};
  String names[] = {"RED", "GREEN", "BLUE", "YELLOW", "CYAN", "MAGENTA", "WHITE", "BLACK"};
  
  for(int i = 0; i < 8; i++) {
    tft.fillScreen(colors[i]);
    delay(1000);
    Serial.println(names[i]);
  }
}

void loop() {}
''',
        
        "text_test": '''
#include <TFT_eSPI.h>
TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.fillScreen(TFT_BLACK);
  
  // Different text sizes and colors
  tft.setTextSize(1);
  tft.setTextColor(TFT_WHITE);
  tft.setCursor(10, 10);
  tft.println("Size 1 Text");
  
  tft.setTextSize(2);
  tft.setTextColor(TFT_RED);
  tft.setCursor(10, 30);
  tft.println("Size 2 Text");
  
  tft.setTextSize(3);
  tft.setTextColor(TFT_GREEN);
  tft.setCursor(10, 60);
  tft.println("Size 3");
  
  // Multiple lines
  tft.setTextSize(2);
  tft.setTextColor(TFT_YELLOW);
  for(int i = 0; i < 5; i++) {
    tft.setCursor(10, 120 + i * 25);
    tft.print("Line ");
    tft.println(i + 1);
  }
}

void loop() {}
''',
        
        "graphics_test": '''
#include <TFT_eSPI.h>
TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.fillScreen(TFT_BLACK);
  
  // Draw shapes
  tft.drawRect(10, 10, 100, 60, TFT_RED);
  tft.fillRect(120, 10, 100, 60, TFT_GREEN);
  
  tft.drawCircle(60, 100, 30, TFT_BLUE);
  tft.fillCircle(170, 100, 30, TFT_YELLOW);
  
  // Draw lines
  for(int i = 0; i < 10; i++) {
    tft.drawLine(0, 150 + i * 5, tft.width(), 150 + i * 5, TFT_CYAN);
  }
  
  // Border
  tft.drawRect(0, 0, tft.width()-1, tft.height()-1, TFT_WHITE);
}

void loop() {}
''',
        
        "animation_test": '''
#include <TFT_eSPI.h>
TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.fillScreen(TFT_BLACK);
}

void loop() {
  // Bouncing ball animation
  static int x = 20, y = 20;
  static int dx = 3, dy = 2;
  
  // Erase previous ball
  tft.fillCircle(x, y, 10, TFT_BLACK);
  
  // Update position
  x += dx;
  y += dy;
  
  // Bounce off edges
  if(x <= 10 || x >= tft.width() - 10) dx = -dx;
  if(y <= 10 || y >= tft.height() - 10) dy = -dy;
  
  // Draw new ball
  tft.fillCircle(x, y, 10, TFT_RED);
  
  delay(50);
}
'''
    }
    
    return tests

def print_esp32_setup_guide():
    """Print setup guide for ESP32 TFT development"""
    print("ESP32 TFT DISPLAY SETUP GUIDE")
    print("="*40)
    print()
    print("1. ARDUINO IDE SETUP:")
    print("   - Install ESP32 board package")
    print("   - Install TFT_eSPI library")
    print("   - Select your ESP32 board")
    print()
    print("2. TFT_eSPI CONFIGURATION:")
    print("   - Edit User_Setup.h in TFT_eSPI library folder")
    print("   - Uncomment your display driver (e.g., #define ILI9341_DRIVER)")
    print("   - Set correct pin connections")
    print()
    print("3. COMMON DISPLAY DRIVERS:")
    print("   - ILI9341 (240x320)")
    print("   - ILI9486 (320x480)")
    print("   - ST7735 (128x160)")
    print("   - ST7789 (240x240)")
    print()
    print("4. YOUR WORKING WIRING:")
    print("   Since your red screen works, your wiring is correct!")
    print("   VCC -> 3.3V or 5V")
    print("   GND -> GND")
    print("   CS -> defined in User_Setup.h")
    print("   DC -> defined in User_Setup.h")
    print("   RST -> defined in User_Setup.h")
    print("   SDA/MOSI -> defined in User_Setup.h")
    print("   SCL/SCLK -> defined in User_Setup.h")

def create_platformio_config():
    """Create PlatformIO configuration for ESP32 TFT project"""
    config = '''[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps = 
    bodmer/TFT_eSPI@^2.5.0
monitor_speed = 115200

; Optional: specify upload port
; upload_port = /dev/ttyUSB0
; monitor_port = /dev/ttyUSB0
'''
    return config

def main():
    print("ESP32 TFT DISPLAY DEVELOPMENT HELPER")
    print("="*50)
    print()
    print("Great news! Your display works with ESP32.")
    print("The red screen confirms hardware is working.")
    print()
    
    print_esp32_setup_guide()
    
    print("\n" + "="*50)
    print("GENERATED TEST CODES")
    print("="*50)
    
    tests = generate_esp32_test_code()
    
    for test_name, code in tests.items():
        print(f"\n--- {test_name.upper().replace('_', ' ')} ---")
        print("Copy this code to Arduino IDE:")
        print(code)
        print("\n" + "-" * 40)
    
    print("\nPLATFORMIO CONFIGURATION (if using PlatformIO):")
    print("Save as platformio.ini:")
    print(create_platformio_config())
    
    print("\n" + "="*50)
    print("NEXT STEPS")
    print("="*50)
    print("1. Your ESP32 + TFT setup is working!")
    print("2. Use the Arduino IDE with TFT_eSPI library")
    print("3. Try the test codes above")
    print("4. For Python development, consider:")
    print("   - MicroPython with display libraries")
    print("   - ESP32 as display server with WiFi communication")
    print("5. The Raspberry Pi codes won't work directly")
    print("   (different hardware, different libraries)")

if __name__ == "__main__":
    main()
