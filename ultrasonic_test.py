#!/usr/bin/env python3
"""
Ultrasonic Sensor Test Script
Tests HC-SR04 ultrasonic sensor on GPIO pins 23 (TRIG) and 24 (ECHO)
"""

import RPi.GPIO as GPIO
import time
import statistics

# GPIO pin configuration
TRIG = 23  # GPIO23 - Trigger pin
ECHO = 24  # GPIO24 - Echo pin

def setup_sensor():
    """Initialize GPIO pins for ultrasonic sensor"""
    print("Setting up ultrasonic sensor...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    time.sleep(0.5)  # Let GPIO settle
    print("✅ Sensor initialized")

def get_distance_detailed():
    """
    Get distance measurement with detailed timing information
    Returns distance in cm, or -1 if timeout/error
    """
    # Send 10µs pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIG, False)
    
    # Wait for echo to start
    pulse_start = time.time()
    timeout_start = pulse_start
    
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        # Timeout protection (0.5 second)
        if pulse_start - timeout_start > 0.5:
            print("❌ Timeout waiting for echo start")
            return -1
    
    # Wait for echo to end
    pulse_end = time.time()
    timeout_start = pulse_end
    
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        # Timeout protection (0.5 second)
        if pulse_end - timeout_start > 0.5:
            print("❌ Timeout waiting for echo end")
            return -1
    
    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound calculation
    distance = round(distance, 2)
    
    # Print timing details
    print(f"   Pulse duration: {pulse_duration*1000000:.1f}µs")
    
    return distance

def test_single_reading():
    """Test a single distance reading"""
    print("\n🔍 Testing single reading...")
    distance = get_distance_detailed()
    
    if distance == -1:
        print("❌ Sensor reading failed")
        return False
    else:
        print(f"📏 Distance: {distance:.2f} cm")
        if distance < 5:
            print("⚠️  Very close object detected")
        elif distance > 400:
            print("⚠️  Reading seems too high - check for echoes")
        return True

def test_multiple_readings(count=10):
    """Test multiple readings and show statistics"""
    print(f"\n📊 Testing {count} consecutive readings...")
    readings = []
    successful_readings = 0
    
    for i in range(count):
        print(f"Reading {i+1}/{count}:", end=" ")
        distance = get_distance_detailed()
        
        if distance != -1:
            readings.append(distance)
            successful_readings += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status}")
        time.sleep(0.1)  # Small delay between readings
    
    # Statistics
    print(f"\n📈 Results:")
    print(f"   Successful readings: {successful_readings}/{count} ({successful_readings/count*100:.1f}%)")
    
    if readings:
        print(f"   Average distance: {statistics.mean(readings):.2f} cm")
        print(f"   Min distance: {min(readings):.2f} cm")
        print(f"   Max distance: {max(readings):.2f} cm")
        if len(readings) > 1:
            print(f"   Standard deviation: {statistics.stdev(readings):.2f} cm")
    
    return successful_readings == count

def test_continuous_monitoring():
    """Continuous monitoring mode"""
    print("\n🔄 Continuous monitoring mode (Press Ctrl+C to stop)")
    print("Distance readings every 0.5 seconds:")
    
    try:
        while True:
            distance = get_distance_detailed()
            timestamp = time.strftime("%H:%M:%S")
            
            if distance == -1:
                print(f"[{timestamp}] ❌ Sensor timeout")
            else:
                if distance <= 20:
                    status = "🚨 VERY CLOSE"
                elif distance <= 50:
                    status = "⚠️  CLOSE"
                elif distance <= 100:
                    status = "📏 MEDIUM"
                else:
                    status = "✅ FAR"
                
                print(f"[{timestamp}] {distance:6.2f} cm | {status}")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

def check_gpio_setup():
    """Check if GPIO pins are properly configured"""
    print("\n🔧 Checking GPIO configuration...")
    
    try:
        # Test TRIG pin
        GPIO.output(TRIG, True)
        time.sleep(0.001)
        GPIO.output(TRIG, False)
        print("✅ TRIG pin (GPIO23) working")
        
        # Test ECHO pin reading
        echo_state = GPIO.input(ECHO)
        print(f"✅ ECHO pin (GPIO24) readable, current state: {echo_state}")
        
        return True
    except Exception as e:
        print(f"❌ GPIO error: {e}")
        return False

def test_wiring():
    """Test sensor wiring by checking pin states"""
    print("\n🔌 Testing sensor wiring...")
    
    # Test with trigger high
    GPIO.output(TRIG, True)
    time.sleep(0.01)
    echo_high = GPIO.input(ECHO)
    
    # Test with trigger low
    GPIO.output(TRIG, False)
    time.sleep(0.01)
    echo_low = GPIO.input(ECHO)
    
    print(f"   TRIG HIGH -> ECHO: {echo_high}")
    print(f"   TRIG LOW  -> ECHO: {echo_low}")
    
    if echo_high == echo_low:
        print("✅ ECHO pin responds to changes")
    else:
        print("⚠️  ECHO pin state doesn't change - check wiring")

def main():
    """Main test function"""
    print("=" * 50)
    print("🔬 ULTRASONIC SENSOR TEST SCRIPT")
    print("=" * 50)
    print("Testing HC-SR04 sensor on:")
    print(f"   TRIG: GPIO{TRIG}")
    print(f"   ECHO: GPIO{ECHO}")
    print()
    
    try:
        setup_sensor()
        
        # Check GPIO setup
        if not check_gpio_setup():
            print("❌ GPIO setup failed. Check your wiring.")
            return
        
        # Test wiring
        test_wiring()
        
        while True:
            print("\n" + "=" * 50)
            print("📋 TEST MENU:")
            print("1. Single reading test")
            print("2. Multiple readings test (10 readings)")
            print("3. Continuous monitoring")
            print("4. GPIO configuration check")
            print("5. Wiring test")
            print("q. Quit")
            print("=" * 50)
            
            choice = input("Select test (1-5, q): ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == '1':
                test_single_reading()
            elif choice == '2':
                test_multiple_readings(10)
            elif choice == '3':
                test_continuous_monitoring()
            elif choice == '4':
                check_gpio_setup()
            elif choice == '5':
                test_wiring()
            else:
                print("❌ Invalid choice. Please select 1-5 or q.")
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("\n🧹 Cleaning up GPIO...")
        GPIO.cleanup()
        print("✅ Cleanup complete")

if __name__ == "__main__":
    main()
