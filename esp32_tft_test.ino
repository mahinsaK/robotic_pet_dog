// ESP32 TFT Display Test - Comprehensive
// For use with TFT_eSPI library on ESP32

#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 TFT Display Test Starting...");
  
  // Initialize the display
  tft.init();
  tft.setRotation(0); // 0-3 for different orientations
  
  Serial.println("Display initialized");
  Serial.print("Display width: ");
  Serial.println(tft.width());
  Serial.print("Display height: ");
  Serial.println(tft.height());
  
  // Test sequence
  runDisplayTests();
}

void loop() {
  // Keep running animation tests
  animationTest();
  delay(5000);
}

void runDisplayTests() {
  Serial.println("Running display tests...");
  
  // Test 1: Solid colors
  colorTest();
  delay(2000);
  
  // Test 2: Text display
  textTest();
  delay(3000);
  
  // Test 3: Shapes and graphics
  graphicsTest();
  delay(3000);
  
  // Test 4: Multiple lines of text
  multiLineTextTest();
  delay(3000);
}

void colorTest() {
  Serial.println("Color test...");
  
  // Array of colors to test
  uint16_t colors[] = {
    TFT_RED,
    TFT_GREEN, 
    TFT_BLUE,
    TFT_YELLOW,
    TFT_CYAN,
    TFT_MAGENTA,
    TFT_WHITE,
    TFT_BLACK
  };
  
  String colorNames[] = {
    "RED", "GREEN", "BLUE", "YELLOW", 
    "CYAN", "MAGENTA", "WHITE", "BLACK"
  };
  
  for (int i = 0; i < 8; i++) {
    tft.fillScreen(colors[i]);
    tft.setTextColor(colors[i] == TFT_WHITE ? TFT_BLACK : TFT_WHITE);
    tft.setTextSize(2);
    tft.setCursor(10, 10);
    tft.println(colorNames[i]);
    Serial.println("Displaying: " + colorNames[i]);
    delay(1000);
  }
}

void textTest() {
  Serial.println("Text test...");
  
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  
  // Different text sizes
  for (int size = 1; size <= 4; size++) {
    tft.setTextSize(size);
    tft.setCursor(10, 30 + (size - 1) * 30);
    tft.print("Text Size ");
    tft.println(size);
  }
  
  // Colored text
  tft.setTextSize(2);
  tft.setTextColor(TFT_RED);
  tft.setCursor(10, 150);
  tft.println("RED TEXT");
  
  tft.setTextColor(TFT_GREEN);
  tft.setCursor(10, 170);
  tft.println("GREEN TEXT");
  
  tft.setTextColor(TFT_BLUE);
  tft.setCursor(10, 190);
  tft.println("BLUE TEXT");
}

void graphicsTest() {
  Serial.println("Graphics test...");
  
  tft.fillScreen(TFT_BLACK);
  
  // Draw rectangles
  tft.drawRect(10, 10, 100, 50, TFT_RED);
  tft.fillRect(120, 10, 100, 50, TFT_GREEN);
  
  // Draw circles
  tft.drawCircle(60, 100, 30, TFT_BLUE);
  tft.fillCircle(170, 100, 30, TFT_YELLOW);
  
  // Draw lines
  for (int i = 0; i < tft.width(); i += 20) {
    tft.drawLine(0, 150, i, tft.height() - 1, TFT_CYAN);
  }
  
  // Add labels
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.setCursor(15, 25);
  tft.println("RECT");
  tft.setCursor(125, 25);
  tft.println("FILLED");
  tft.setCursor(35, 85);
  tft.println("CIRCLE");
  tft.setCursor(145, 85);
  tft.println("FILLED");
}

void multiLineTextTest() {
  Serial.println("Multi-line text test...");
  
  tft.fillScreen(TFT_NAVY);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  
  String lines[] = {
    "ESP32 TFT Test",
    "Line 2: Working",
    "Line 3: Display OK",
    "Line 4: All Good",
    "Line 5: Success!"
  };
  
  for (int i = 0; i < 5; i++) {
    tft.setCursor(10, 20 + i * 25);
    tft.println(lines[i]);
    delay(500);
  }
  
  // Add border
  tft.drawRect(0, 0, tft.width() - 1, tft.height() - 1, TFT_YELLOW);
}

void animationTest() {
  Serial.println("Animation test...");
  
  tft.fillScreen(TFT_BLACK);
  
  // Moving circle animation
  for (int x = 20; x < tft.width() - 20; x += 5) {
    tft.fillCircle(x - 5, 50, 15, TFT_BLACK);  // Erase previous
    tft.fillCircle(x, 50, 15, TFT_RED);        // Draw new
    delay(50);
  }
  
  // Moving text
  tft.setTextColor(TFT_GREEN);
  tft.setTextSize(2);
  for (int y = 100; y < tft.height() - 50; y += 3) {
    tft.fillRect(0, y - 3, tft.width(), 20, TFT_BLACK);  // Erase
    tft.setCursor(10, y);
    tft.println("MOVING TEXT");
    delay(100);
  }
}

// Function to test different rotations
void rotationTest() {
  Serial.println("Rotation test...");
  
  for (int rotation = 0; rotation < 4; rotation++) {
    tft.setRotation(rotation);
    tft.fillScreen(TFT_BLACK);
    
    tft.setTextColor(TFT_WHITE);
    tft.setTextSize(2);
    tft.setCursor(10, 10);
    tft.print("Rotation: ");
    tft.println(rotation);
    
    tft.setCursor(10, 40);
    tft.print("Size: ");
    tft.print(tft.width());
    tft.print("x");
    tft.println(tft.height());
    
    // Draw orientation indicator
    tft.drawLine(0, 0, 50, 0, TFT_RED);      // Top edge - red
    tft.drawLine(0, 0, 0, 50, TFT_GREEN);    // Left edge - green
    
    delay(2000);
  }
  
  // Reset to normal rotation
  tft.setRotation(0);
}
