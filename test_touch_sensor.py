 #!/usr/bin/env python3
"""
Test script for TTP-223 blue touch sensor
Touch sensor I/O pin connected to GPIO 26

The TTP-223 is a capacitive touch sensor that outputs:
- HIGH (3.3V) when touched
- LOW (0V) when not touched
"""

import RPi.GPIO as GPIO
import time
import signal
import sys

# Touch sensor configuration
TOUCH_PIN = 26  # GPIO26

def setup_touch_sensor():
    """Initialize GPIO for touch sensor"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TOUCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    print("Touch sensor initialized on GPIO26")
    print("Touch sensor ready - touch the sensor pad to test!")

def cleanup_gpio(signum=None, frame=None):
    """Clean up GPIO on exit"""
    print("\nCleaning up GPIO...")
    GPIO.cleanup()
    sys.exit(0)

def test_touch_sensor_polling():
    """Test touch sensor using polling method"""
    print("\n=== Testing Touch Sensor (Polling Method) ===")
    print("Touch the sensor pad - press Ctrl+C to exit")
    
    last_state = False
    touch_count = 0
    
    try:
        while True:
            current_state = GPIO.input(TOUCH_PIN)
            
            # Detect state change (touch/release)
            if current_state != last_state:
                if current_state:
                    touch_count += 1
                    print(f"🟢 TOUCHED! (Count: {touch_count}) - GPIO26 = HIGH")
                else:
                    print(f"🔴 RELEASED - GPIO26 = LOW")
                last_state = current_state
            
            time.sleep(0.05)  # 50ms polling rate
            
    except KeyboardInterrupt:
        print(f"\nTouch test finished. Total touches detected: {touch_count}")

def test_touch_sensor_interrupt():
    """Test touch sensor using interrupt method"""
    print("\n=== Testing Touch Sensor (Interrupt Method) ===")
    print("Touch the sensor pad - press Ctrl+C to exit")
    
    touch_count = 0
    
    def touch_detected(channel):
        nonlocal touch_count
        if GPIO.input(TOUCH_PIN):
            touch_count += 1
            print(f"🟢 TOUCH DETECTED! (Count: {touch_count}) - Interrupt on GPIO{channel}")
    
    def touch_released(channel):
        print(f"🔴 TOUCH RELEASED - Interrupt on GPIO{channel}")
    
    # Set up interrupts for both rising and falling edges
    GPIO.add_event_detect(TOUCH_PIN, GPIO.RISING, callback=touch_detected, bouncetime=200)
    GPIO.add_event_detect(TOUCH_PIN, GPIO.FALLING, callback=touch_released, bouncetime=200)
    
    try:
        print("Interrupt handlers active. Touch the sensor...")
        while True:
            time.sleep(1)  # Just wait for interrupts
            
    except KeyboardInterrupt:
        print(f"\nInterrupt test finished. Total touches detected: {touch_count}")
    finally:
        GPIO.remove_event_detect(TOUCH_PIN)

def test_touch_sensor_continuous():
    """Continuously monitor touch sensor state"""
    print("\n=== Continuous Touch Sensor Monitor ===")
    print("Real-time monitoring - press Ctrl+C to exit")
    
    try:
        while True:
            state = GPIO.input(TOUCH_PIN)
            status = "TOUCHED 🟢" if state else "NOT TOUCHED 🔴"
            voltage = "3.3V" if state else "0V"
            
            # Clear line and print status
            print(f"\rTouch Status: {status} | GPIO26: {state} ({voltage})", end="", flush=True)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nContinuous monitoring stopped.")

def test_touch_sensor_toggle():
    """Test touch sensor with toggle functionality"""
    print("\n=== Touch Sensor Toggle Mode ===")
    print("Touch once to toggle between two actions - press Ctrl+C to exit")
    
    # Toggle state and actions
    toggle_state = False
    action_1 = "🔴 LED OFF / Motor STOP"
    action_2 = "🟢 LED ON / Motor START"
    
    last_touch_state = False
    touch_count = 0
    
    print(f"Current Action: {action_1}")
    
    try:
        while True:
            current_touch_state = GPIO.input(TOUCH_PIN)
            
            # Detect rising edge (touch moment)
            if current_touch_state and not last_touch_state:
                # Touch detected - toggle action
                toggle_state = not toggle_state
                touch_count += 1
                
                current_action = action_2 if toggle_state else action_1
                status = "ON" if toggle_state else "OFF"
                
                print(f"\n👆 Touch #{touch_count} detected!")
                print(f"🔄 Toggled to: {current_action}")
                print(f"📊 Current State: {status}")
                
                # Simulate action execution
                if toggle_state:
                    print("✅ Executing: Start motor, turn on LED, activate system")
                else:
                    print("⏹️  Executing: Stop motor, turn off LED, deactivate system")
                
                # Wait to avoid multiple triggers from single touch
                time.sleep(0.3)
            
            last_touch_state = current_touch_state
            time.sleep(0.05)  # 50ms polling rate
            
    except KeyboardInterrupt:
        final_state = "ON" if toggle_state else "OFF"
        print(f"\nToggle test finished.")
        print(f"Total touches: {touch_count}")
        print(f"Final state: {final_state}")

def main():
    """Main test function"""
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, cleanup_gpio)
    signal.signal(signal.SIGTERM, cleanup_gpio)
    
    setup_touch_sensor()
    
    print("\n" + "="*50)
    print("TTP-223 Touch Sensor Test Script")
    print("="*50)
    print("Touch sensor connected to GPIO26")
    print("\nDifferences between test modes:")
    print("• Polling: Only shows when state CHANGES (touch/release events)")
    print("• Continuous: Shows CURRENT state constantly (real-time)")
    print("• Toggle: One touch = one action switch (like a power button)")
    print("\nChoose test mode:")
    print("1. Polling method (detects touch/release)")
    print("2. Interrupt method (event-driven)")
    print("3. Continuous monitoring (real-time)")
    print("4. Toggle mode (touch to switch actions)")
    print("5. Run all tests")
    print("q. Quit")
    
    try:
        while True:
            choice = input("\nEnter choice (1/2/3/4/5/q): ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == '1':
                test_touch_sensor_polling()
            elif choice == '2':
                test_touch_sensor_interrupt()
            elif choice == '3':
                test_touch_sensor_continuous()
            elif choice == '4':
                test_touch_sensor_toggle()
            elif choice == '5':
                print("Running all tests...")
                test_touch_sensor_polling()
                time.sleep(1)
                test_touch_sensor_interrupt()
                time.sleep(1)
                test_touch_sensor_continuous()
                time.sleep(1)
                test_touch_sensor_toggle()
            else:
                print("Invalid choice. Please enter 1, 2, 3, 4, 5, or q")
                
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()
