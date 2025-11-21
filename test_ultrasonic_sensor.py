#!/usr/bin/env python3
"""
HC-SR04 Ultrasonic Sensor Test Script
For SpotMicro Robot

Pin Connections:
VCC -> Pin 2 (5V)
GND -> Pin 6 (Ground)
Trig -> GPIO23
Echo -> GPIO24
"""

import RPi.GPIO as GPIO
import time

# GPIO pin configuration
TRIG = 23  # GPIO23
ECHO = 24  # GPIO24

def setup_ultrasonic():
    """Initialize GPIO pins for ultrasonic sensor"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("Ultrasonic sensor initialized")
    print("Waiting for sensor to settle...")
    time.sleep(2)

def get_distance():
    """
    Get distance measurement from HC-SR04 sensor
    Returns distance in centimeters
    """
    # Send 10us pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIG, False)
    
    # Wait for echo to start
    pulse_start = time.time()
    timeout_start = pulse_start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        # Timeout protection (max ~1 second)
        if pulse_start - timeout_start > 1:
            return -1  # Timeout error
    
    # Wait for echo to end
    pulse_end = time.time()
    timeout_start = pulse_end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        # Timeout protection (max ~1 second)
        if pulse_end - timeout_start > 1:
            return -1  # Timeout error
    
    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound = 343m/s, divide by 2 for round trip
    distance = round(distance, 2)
    
    return distance

def test_continuous_reading():
    """Test continuous distance readings"""
    print("\n=== Continuous Distance Reading Test ===")
    print("Press Ctrl+C to stop")
    print("Distance readings (cm):")
    print("-" * 40)
    
    try:
        while True:
            distance = get_distance()
            
            if distance == -1:
                print("Timeout - No echo received")
            elif distance > 400:
                print("Out of range (>400cm)")
            elif distance < 2:
                print("Too close (<2cm)")
            else:
                # Add visual indicator for obstacle detection
                if distance <= 30:
                    status = "🚨 OBSTACLE DETECTED! 🚨"
                elif distance <= 50:
                    status = "⚠️  Getting close"
                else:
                    status = "✅ Clear path"
                
                print(f"Distance: {distance:6.2f} cm | {status}")
            
            time.sleep(0.5)  # Read every 500ms
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")

def test_obstacle_detection():
    """Test obstacle detection threshold (30cm)"""
    print("\n=== Obstacle Detection Threshold Test ===")
    print("Testing 30cm obstacle detection threshold")
    print("Move an object closer and farther to test")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    obstacle_detected = False
    
    try:
        while True:
            distance = get_distance()
            
            if distance == -1:
                print("Sensor timeout - check connections")
            elif distance > 400:
                print("No objects detected (>400cm)")
                obstacle_detected = False
            elif distance <= 30:
                if not obstacle_detected:
                    print(f"🚨 OBSTACLE DETECTED at {distance:.2f}cm - ROBOT SHOULD TURN RIGHT!")
                    obstacle_detected = True
                else:
                    print(f"🚨 Still detecting obstacle at {distance:.2f}cm")
            else:
                if obstacle_detected:
                    print(f"✅ Obstacle cleared! Distance: {distance:.2f}cm - ROBOT CAN CONTINUE FORWARD")
                    obstacle_detected = False
                else:
                    print(f"✅ Path clear - Distance: {distance:.2f}cm")
            
            time.sleep(0.3)  # Faster reading for obstacle detection
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")

def test_sensor_accuracy():
    """Test sensor accuracy with known distances"""
    print("\n=== Sensor Accuracy Test ===")
    print("Place objects at known distances and verify readings")
    print("Recommended test distances: 10cm, 20cm, 30cm, 50cm, 100cm")
    print("Press Enter after positioning object, 'q' to quit")
    print("-" * 50)
    
    while True:
        user_input = input("\nPosition object and press Enter (or 'q' to quit): ").strip().lower()
        if user_input == 'q':
            break
        
        # Take multiple readings for accuracy
        readings = []
        print("Taking 5 readings...")
        
        for i in range(5):
            distance = get_distance()
            if distance > 0:
                readings.append(distance)
            time.sleep(0.2)
        
        if readings:
            avg_distance = sum(readings) / len(readings)
            min_distance = min(readings)
            max_distance = max(readings)
            
            print(f"Average distance: {avg_distance:.2f} cm")
            print(f"Range: {min_distance:.2f} - {max_distance:.2f} cm")
            print(f"Variation: ±{(max_distance - min_distance)/2:.2f} cm")
        else:
            print("No valid readings obtained")

def main():
    """Main test function"""
    print("=" * 60)
    print("        HC-SR04 Ultrasonic Sensor Test")
    print("        SpotMicro Robot Project")
    print("=" * 60)
    print("\nSensor Connections:")
    print("VCC -> Pin 2 (5V)")
    print("GND -> Pin 6 (Ground)")  
    print("Trig -> GPIO23")
    print("Echo -> GPIO24")
    print("-" * 60)
    
    try:
        setup_ultrasonic()
        
        while True:
            print("\nSelect test mode:")
            print("1. Continuous distance reading")
            print("2. Obstacle detection test (30cm threshold)")
            print("3. Sensor accuracy test")
            print("4. Single distance reading")
            print("q. Quit")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == '1':
                test_continuous_reading()
            elif choice == '2':
                test_obstacle_detection()
            elif choice == '3':
                test_sensor_accuracy()
            elif choice == '4':
                distance = get_distance()
                if distance == -1:
                    print("Sensor timeout - check connections")
                else:
                    print(f"Distance: {distance:.2f} cm")
            elif choice == 'q':
                break
            else:
                print("Invalid choice. Please try again.")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        GPIO.cleanup()
        print("\nGPIO cleanup complete. Test finished.")

if __name__ == "__main__":
    main()
