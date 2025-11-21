// Simple ESP32 TFT Test - Based on your working red screen
// This should work if your red screen example works

#include <TFT_eSPI.h>
TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 TFT Simple Test");
  
  // Initialize display (same as your working code)
  tft.init();
  
  // Test sequence - if red works, these should too
  Serial.println("Testing colors...");
  
  // Your working red screen
  tft.fillScreen(TFT_RED);
  Serial.println("Red screen (like your working example)");
  delay(2000);
  
  // Test other colors
  tft.fillScreen(TFT_GREEN);
  Serial.println("Green screen");
  delay(2000);
  
  tft.fillScreen(TFT_BLUE);
  Serial.println("Blue screen");
  delay(2000);
  
  tft.fillScreen(TFT_WHITE);
  Serial.println("White screen");
  delay(2000);
  
  tft.fillScreen(TFT_BLACK);
  Serial.println("Black screen");
  delay(2000);
  
  // Test text display
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("Hello ESP32!");
  tft.setCursor(10, 40);
  tft.println("TFT Working!");
  Serial.println("Text displayed");
  delay(3000);
  
  // Test multiple lines
  tft.fillScreen(TFT_NAVY);
  tft.setTextColor(TFT_YELLOW);
  tft.setTextSize(2);
  
  tft.setCursor(10, 20);
  tft.println("Line 1");
  tft.setCursor(10, 50);
  tft.println("Line 2");
  tft.setCursor(10, 80);
  tft.println("Line 3");
  tft.setCursor(10, 110);
  tft.println("Line 4");
  tft.setCursor(10, 140);
  tft.println("Line 5");
  
  Serial.println("Multiple lines displayed");
  Serial.print("Display size: ");
  Serial.print(tft.width());
  Serial.print(" x ");
  Serial.println(tft.height());
}

void loop() {
  // Blinking text to show it's working
  tft.setTextColor(TFT_RED);
  tft.setCursor(10, 180);
  tft.println("WORKING!");
  delay(500);
  
  tft.fillRect(10, 180, 120, 20, TFT_NAVY);  // Erase
  delay(500);
}
