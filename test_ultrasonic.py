#!/usr/bin/env python3
"""
Ultrasonic Sensor (HC-SR04) Test Script
Tests the ultrasonic sensor functionality with detailed diagnostics
"""
import RPi.GPIO as GPIO
import time
import signal
import sys

# Ultrasonic sensor configuration
TRIG = 23  # GPIO23
ECHO = 24  # GPIO24

def setup_ultrasonic():
    """Initialize GPIO pins for ultrasonic sensor"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("✅ Ultrasonic sensor initialized")
    print(f"   TRIG pin: GPIO{TRIG}")
    print(f"   ECHO pin: GPIO{ECHO}")

def get_distance():
    """
    Get distance measurement from HC-SR04 sensor
    Returns distance in centimeters, -1 if timeout
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
        # Timeout protection (max ~0.1 second for faster response)
        if pulse_start - timeout_start > 0.1:
            return -1  # Timeout error
    
    # Wait for echo to end
    pulse_end = time.time()
    timeout_start = pulse_end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        # Timeout protection (max ~0.1 second for faster response)
        if pulse_end - timeout_start > 0.1:
            return -1  # Timeout error
    
    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound = 343m/s, divide by 2 for round trip
    distance = round(distance, 2)
    
    return distance

def check_obstacle_detection():
    """Test obstacle detection at different thresholds"""
    print("\n🔍 OBSTACLE DETECTION TEST")
    print("-" * 40)
    
    thresholds = [10, 20, 30, 50]  # cm
    
    for threshold in thresholds:
        distance = get_distance()
        if distance == -1:
            print(f"❌ Threshold {threshold}cm: SENSOR ERROR")
        else:
            obstacle = "🚨 OBSTACLE!" if distance <= threshold else "✅ Clear"
            print(f"📏 Threshold {threshold}cm: {distance:.2f}cm | {obstacle}")
        time.sleep(0.1)

def continuous_monitoring():
    """Continuous distance monitoring"""
    print("\n📡 CONTINUOUS MONITORING MODE")
    print("-" * 40)
    print("Press Ctrl+C to stop monitoring\n")
    
    measurement_count = 0
    error_count = 0
    min_distance = float('inf')
    max_distance = 0
    
    try:
        while True:
            distance = get_distance()
            measurement_count += 1
            
            if distance == -1:
                error_count += 1
                print(f"❌ Measurement #{measurement_count}: TIMEOUT ERROR")
            else:
                min_distance = min(min_distance, distance)
                max_distance = max(max_distance, distance)
                
                # Status based on distance
                if distance <= 10:
                    status = "🔴 VERY CLOSE"
                elif distance <= 30:
                    status = "🟡 CLOSE"
                elif distance <= 100:
                    status = "🟢 MEDIUM"
                else:
                    status = "🔵 FAR"
                
                print(f"📏 #{measurement_count}: {distance:.2f}cm | {status}")
            
            time.sleep(0.5)  # 2 measurements per second
            
    except KeyboardInterrupt:
        print(f"\n📊 MONITORING STATISTICS:")
        print(f"   Total measurements: {measurement_count}")
        print(f"   Successful: {measurement_count - error_count}")
        print(f"   Errors: {error_count}")
        if measurement_count > error_count:
            success_rate = ((measurement_count - error_count) / measurement_count) * 100
            print(f"   Success rate: {success_rate:.1f}%")
            if min_distance != float('inf'):
                print(f"   Distance range: {min_distance:.2f}cm - {max_distance:.2f}cm")

def performance_test():
    """Test sensor performance and timing"""
    print("\n⚡ PERFORMANCE TEST")
    print("-" * 40)
    
    num_tests = 50
    times = []
    distances = []
    errors = 0
    
    print(f"Running {num_tests} rapid measurements...")
    
    start_time = time.time()
    for i in range(num_tests):
        test_start = time.time()
        distance = get_distance()
        test_end = time.time()
        
        times.append(test_end - test_start)
        
        if distance == -1:
            errors += 1
        else:
            distances.append(distance)
        
        # Small delay to prevent overwhelming the sensor
        time.sleep(0.01)
    
    total_time = time.time() - start_time
    
    print(f"\n📊 PERFORMANCE RESULTS:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time per measurement: {sum(times)/len(times)*1000:.2f}ms")
    print(f"   Successful measurements: {len(distances)}/{num_tests}")
    print(f"   Error count: {errors}")
    print(f"   Success rate: {(len(distances)/num_tests)*100:.1f}%")
    
    if distances:
        print(f"   Distance statistics:")
        print(f"     Min: {min(distances):.2f}cm")
        print(f"     Max: {max(distances):.2f}cm")
        print(f"     Average: {sum(distances)/len(distances):.2f}cm")

def cleanup_gpio(signum=None, frame=None):
    """Clean up GPIO on exit"""
    print("\n🧹 Cleaning up GPIO...")
    GPIO.cleanup()
    print("✅ GPIO cleanup complete")
    sys.exit(0)

def main():
    """Main test function"""
    print("🔊 ULTRASONIC SENSOR (HC-SR04) TEST SCRIPT")
    print("=" * 50)
    
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, cleanup_gpio)
    signal.signal(signal.SIGTERM, cleanup_gpio)
    
    try:
        # Initialize sensor
        setup_ultrasonic()
        
        # Wait for sensor to stabilize
        print("\n⏳ Waiting for sensor to stabilize...")
        time.sleep(2)
        
        while True:
            print("\n🧪 TEST MENU:")
            print("1. Single measurement")
            print("2. Obstacle detection test")
            print("3. Continuous monitoring")
            print("4. Performance test")
            print("5. Quit")
            
            choice = input("\nSelect test (1-5): ").strip()
            
            if choice == '1':
                print("\n📏 SINGLE MEASUREMENT")
                print("-" * 40)
                distance = get_distance()
                if distance == -1:
                    print("❌ Sensor timeout - check connections")
                else:
                    obstacle_status = "🚨 OBSTACLE!" if distance <= 30 else "✅ Clear"
                    print(f"Distance: {distance:.2f}cm | {obstacle_status}")
                    
            elif choice == '2':
                check_obstacle_detection()
                
            elif choice == '3':
                continuous_monitoring()
                
            elif choice == '4':
                performance_test()
                
            elif choice == '5':
                break
                
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
            input("\nPress Enter to continue...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()
