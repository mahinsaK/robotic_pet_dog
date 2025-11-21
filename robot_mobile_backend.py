import importlib.util
import os

# Import DFPlayer control
dfplayer_path = os.path.join(os.path.dirname(__file__), 'dfplayer_control copy.py')
spec = importlib.util.spec_from_file_location('dfplayer_control', dfplayer_path)
dfplayer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dfplayer)

# Import RoboEyes display
display_path = os.path.join(os.path.dirname(__file__), 'display_sanduni copy.py')
spec2 = importlib.util.spec_from_file_location('display_sanduni', display_path)
display = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(display)

# Initialize RoboEyes instance
roboeyes = display.RoboEyes()

#!/usr/bin/env python3
"""
Mobile Robot Control Backend Server
Integrates with robot_mobile_control.html UI
Uses hardware control functions from p12-6.py
Includes gesture control via TCP socket and servo testing mode
"""

import asyncio
import websockets
import json
import time
import threading
import queue
import numpy as np
import signal
import sys
import socket

# Import hardware libraries
try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
    print("✅ Hardware libraries loaded successfully")
except ImportError as e:
    print(f"⚠️ Hardware libraries not available: {e}")
    print("Running in simulation mode...")
    HARDWARE_AVAILABLE = False

class RobotController:
    def __init__(self):
        self.hardware_initialized = False
        self.current_angles = {}
        self.lock = threading.Lock()
        self.servo_config = {
            0: {"name": "FL Shoulder", "type": "270", "default": 200, "leg": "FL", "direction": "- outwards"},
            1: {"name": "FL Thigh", "type": "270", "default": 10, "leg": "FL", "direction": "+ backwards"},
            2: {"name": "FL Knee", "type": "270", "default": 145, "leg": "FL", "direction": "- bending"},
            4: {"name": "FR Shoulder", "type": "270", "default": 100, "leg": "FR", "direction": "+ outwards"},
            5: {"name": "FR Thigh", "type": "270", "default": 115, "leg": "FR", "direction": "- backwards"},
            6: {"name": "FR Knee", "type": "180", "default": 10, "leg": "FR", "direction": "+ bending"},
            8: {"name": "RL Shoulder", "type": "180", "default": 150, "leg": "RL", "direction": "- outwards"},
            9: {"name": "RL Thigh", "type": "270", "default": 19, "leg": "RL", "direction": "+ backwards"},
            10: {"name": "RL Knee", "type": "180", "default": 150, "leg": "RL", "direction": "- bending"},
            12: {"name": "RR Shoulder", "type": "180", "default": 120, "leg": "RR", "direction": "+ outwards"},
            13: {"name": "RR Thigh", "type": "270", "default": 110, "leg": "RR", "direction": "- backwards"},
            14: {"name": "RR Knee", "type": "180", "default": 5, "leg": "RR", "direction": "+ bending"}
        }
        self.current_angles = {ch: self.servo_config[ch]["default"] for ch in self.servo_config}
        if HARDWARE_AVAILABLE:
            try:
                self.init_hardware()
                self.hardware_initialized = True
                print("✅ Hardware initialized successfully")
            except Exception as e:
                print(f"❌ Hardware initialization failed: {e}")
                self.hardware_initialized = False
        else:
            print("🔧 Running in simulation mode - no hardware will be controlled")
    
    def init_hardware(self):
        if not HARDWARE_AVAILABLE:
            return
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pwm = PCA9685(self.i2c)
        self.pwm.frequency = 50
        for i in range(16):
            self.pwm.channels[i].duty_cycle = 0
        self.TRIG = 23
        self.ECHO = 24
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)
        GPIO.output(self.TRIG, False)
    
    def cleanup_hardware(self):
        if not self.hardware_initialized:
            return
        print("🔧 Cleaning up hardware...")
        try:
            for channel in self.servo_config:
                neutral_angle = self.servo_config[channel]["default"]
                pwm_value = self.angle_to_pwm(neutral_angle, self.servo_config[channel]["type"])
                self.pwm.channels[channel].duty_cycle = int(pwm_value * 65535 / 4096)
                time.sleep(0.01)
            time.sleep(0.5)
            for i in range(16):
                self.pwm.channels[i].duty_cycle = 0
            self.pwm.deinit()
            GPIO.cleanup()
            print("✅ Hardware cleanup complete")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
    
    def angle_to_pwm(self, angle, servo_type):
        if servo_type == "180":
            min_angle, max_angle = 0, 180
        else:
            min_angle, max_angle = 0, 270
        min_pwm, max_pwm = 100, 500
        angle = max(min(angle, max_angle), min_angle)
        return int(min_pwm + (angle - min_angle) / (max_angle - min_angle) * (max_pwm - min_pwm))
    
    def set_pose(self, target_angles, transition_time=0.3, steps=15):
        if not self.hardware_initialized:
            print(f"🎭 [SIM] Setting pose: {list(target_angles.keys())}")
            self.current_angles.update(target_angles)
            return
        with self.lock:
            step_angles = {}
            for ch in target_angles:
                start = self.current_angles.get(ch, self.servo_config[ch]["default"])
                end = target_angles[ch]
                step_angles[ch] = np.linspace(start, end, steps)
            for i in range(steps):
                for ch in target_angles:
                    angle = step_angles[ch][i]
                    pwm_value = self.angle_to_pwm(angle, self.servo_config[ch]["type"])
                    try:
                        self.pwm.channels[ch].duty_cycle = int(pwm_value * 65535 / 4096)
                    except Exception as e:
                        print(f"Error setting PWM on channel {ch}: {e}")
                time.sleep(transition_time / steps)
            self.current_angles.update(target_angles)
    
    def get_distance(self):
        if not self.hardware_initialized:
            import random
            return random.uniform(10, 200)
        for _ in range(3):
            try:
                GPIO.output(self.TRIG, True)
                time.sleep(0.00001)
                GPIO.output(self.TRIG, False)
                pulse_start = time.time()
                timeout_start = pulse_start
                while GPIO.input(self.ECHO) == 0:
                    pulse_start = time.time()
                    if pulse_start - timeout_start > 0.1:
                        break
                else:
                    pulse_end = time.time()
                    timeout_start = pulse_end
                    while GPIO.input(self.ECHO) == 1:
                        pulse_end = time.time()
                        if pulse_end - timeout_start > 0.1:
                            break
                    else:
                        pulse_duration = pulse_end - pulse_start
                        distance = pulse_duration * 17150
                        return round(distance, 2)
                time.sleep(0.01)
            except Exception as e:
                print(f"Distance sensor error: {e}")
        print("⚠️ Distance sensor failed after retries")
        return -1
    
    def check_obstacle(self):
        distance = self.get_distance()
        if distance == -1:
            print("⚠️ Invalid distance reading, treating as no obstacle")
            return False
        return distance <= 30

# Robot poses
STANDING_ANGLES = {
    0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
    8: 150, 9: 83, 10: 50, 12: 120, 13: 45, 14: 105
}
SITTING_ANGLES = {
     0: 160, 1: 110, 2: 10, 4: 100, 5: 15, 6: 150,
    8: 150, 9: 123, 10: 10, 12: 120, 13: 5, 14: 145
}
BACKWARD_PHASES = {
    "front_right": [{5: 65, 6: 120}, {5: 35, 6: 125}, {5: 35, 6: 115}, {5: 45, 6: 115}],
    "front_left": [{1: 60, 2: 40}, {1: 90, 2: 35}, {1: 90, 2: 45}, {1: 80, 2: 45}],
    "rear_right": [{13: 55, 14: 115}, {13: 25, 14: 120}, {13: 25, 14: 110}, {13: 35, 14: 110}],
    "rear_left": [{9: 73, 10: 40}, {9: 103, 10: 35}, {9: 103, 10: 45}, {9: 93, 10: 50}]
}
WALKING_PHASES = {
    "front_right": [{5: 45, 6: 115},{5: 35, 6: 115}, {5: 35, 6: 125},{5: 65, 6: 120}],
    "front_left": [{1: 80, 2: 45}, {1: 90, 2: 45}, {1: 90, 2: 35}, {1: 60, 2: 40}],
    "rear_right": [{13: 35, 14: 110}, {13: 25, 14: 110}, {13: 25, 14: 120}, {13: 55, 14: 115}],
    "rear_left": [{9: 93, 10: 45}, {9: 103, 10: 45}, {9: 103, 10: 35}, {9: 73, 10: 40}]
}
TURN_RIGHT_PHASES = {
    "front_right": [ {5: 50, 6: 105},  {5: 35, 6: 110}, {5: 35, 6: 125}, {5: 60, 6: 115}],
    "front_left": [{1: 65, 2: 45}, {1: 90, 2: 50}, {1: 90, 2: 35}, {1: 55, 2: 35}],
    "rear_right": [ {13: 40, 14: 100}, {13: 25, 14: 105}, {13: 25, 14: 120}, {13: 50, 14: 110}],
    "rear_left": [{9: 78, 10: 45}, {9: 103, 10: 50}, {9: 103, 10: 35}, {9: 68, 10: 35}]
}
TURN_LEFT_PHASES = {
    "front_right": [{5: 60, 6: 115}, {5: 35, 6: 110}, {5: 35, 6: 125}, {5: 70, 6: 125}],
    "front_left": [{1: 75, 2: 55}, {1: 90, 2: 50}, {1: 90, 2: 35}, {1: 65, 2: 45}],
    "rear_right": [{13: 62, 14: 110}, {13: 37, 14: 105}, {13: 37, 14: 120}, {13: 72, 14: 120}],
    "rear_left": [{9: 88, 10: 55}, {9: 103, 10: 50}, {9: 103, 10: 35}, {9: 78, 10: 45}]
}
# Dance phases
dance1_phases = {
    1: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105
    },
    2: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    3: {
        0: 160, 1: 100, 2: 10, 4: 100, 5: 25, 6: 150,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    4: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    5: {
        0: 160, 1: 100, 2: 10, 4: 100, 5: 25, 6: 150,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    6: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    7: {
        0: 160, 1: 100, 2: 10, 4: 100, 5: 25, 6: 150,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    8: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    9: {
        0: 160, 1: 100, 2: 10, 4: 100, 5: 25, 6: 150,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    10: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    11: {
        0: 160, 1: 100, 2: 10, 4: 100, 5: 25, 6: 150,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    12: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    13: {
        0: 160, 1: 100, 2: 10, 4: 100, 5: 25, 6: 150,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    14: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 110, 10: 150, 12: 120, 13: 30, 14: 5
    },
    15: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105
    }
}

dance2_phases = {
    1: {0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110, 8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105},
    2: {0: 160, 1: 90, 2: 70, 4: 100, 5: 35, 6: 90, 8: 150, 9: 63, 10: 20, 12: 120, 13: 77, 14: 135},
    3: {0: 160, 1: 10, 2: 150, 4: 100, 5: 115, 6: 10, 8: 150, 9: 63, 10: 20, 12: 120, 13: 77, 14: 135},
    4: {0: 160, 1: 10, 2: 150, 4: 100, 5: 115, 6: 10, 8: 150, 9: 13, 10: 0, 12: 120, 13: 127, 14: 155},
    5: {0: 160, 1: 80, 2: 150, 4: 100, 5: 45, 6: 10, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    6: {0: 160, 1: 55, 2: 70, 4: 100, 5: 70, 6: 90, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    7: {0: 160, 1: 55, 2: 70, 4: 100, 5: 70, 6: 90, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    8: {0: 185, 1: 10, 2: 91, 4: 72, 5: 115, 6: 63, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    9: {0: 140, 1: 55, 2: 70, 4: 120, 5: 70, 6: 90, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    10: {0: 160, 1: 55, 2: 70, 4: 100, 5: 70, 6: 90, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    11: {0: 220, 1: 55, 2: 0, 4: 160, 5: 70, 6: 160, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    12: {0: 220, 1: 55, 2: 70, 4: 160, 5: 70, 6: 90, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    13: {0: 100, 1: 55, 2: 0, 4: 40, 5: 70, 6: 160, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    14: {0: 100, 1: 55, 2: 70, 4: 40, 5: 70, 6: 90, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    15: {0: 160, 1: 55, 2: 70, 4: 100, 5: 70, 6: 90, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    16: {0: 160, 1: 55, 2: 70, 4: 100, 5: 70, 6: 90, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    17: {0: 160, 1: 80, 2: 150, 4: 100, 5: 45, 6: 10, 8: 150, 9: 43, 10: 0, 12: 120, 13: 97, 14: 155},
    18: {0: 160, 1: 10, 2: 150, 4: 100, 5: 115, 6: 10, 8: 150, 9: 13, 10: 0, 12: 120, 13: 127, 14: 155},
    19: {0: 160, 1: 10, 2: 150, 4: 100, 5: 115, 6: 10, 8: 150, 9: 63, 10: 20, 12: 120, 13: 77, 14: 135},
    20: {0: 160, 1: 90, 2: 70, 4: 100, 5: 35, 6: 90, 8: 150, 9: 63, 10: 20, 12: 120, 13: 77, 14: 135},
    21: {0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110, 8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105},
    22: {0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110, 8: 150, 9: 83, 10: 10, 12: 120, 13: 57, 14: 145}
}

dance3_phases = {
    1: {0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110, 8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105},
    2: {0: 130, 1: 85, 2: 35, 4: 70, 5: 70, 6: 90, 8: 120, 9: 103, 10: 35, 12: 90, 13: 72, 14: 90},
    3: {0: 190, 1: 55, 2: 65, 4: 130, 5: 40, 6: 130, 8: 180, 9: 63, 10: 65, 12: 150, 13: 42, 14: 120},
    4: {0: 130, 1: 85, 2: 35, 4: 70, 5: 70, 6: 90, 8: 120, 9: 103, 10: 35, 12: 90, 13: 72, 14: 90},
    5: {0: 190, 1: 55, 2: 65, 4: 130, 5: 40, 6: 130, 8: 180, 9: 63, 10: 65, 12: 150, 13: 42, 14: 120},
    6: {0: 130, 1: 85, 2: 35, 4: 70, 5: 70, 6: 90, 8: 120, 9: 103, 10: 35, 12: 90, 13: 72, 14: 90},
    7: {0: 190, 1: 55, 2: 65, 4: 130, 5: 40, 6: 130, 8: 180, 9: 63, 10: 65, 12: 150, 13: 42, 14: 120},
    8: {0: 130, 1: 85, 2: 35, 4: 70, 5: 70, 6: 90, 8: 120, 9: 103, 10: 35, 12: 90, 13: 72, 14: 90},
    9: {0: 190, 1: 55, 2: 65, 4: 130, 5: 40, 6: 130, 8: 180, 9: 63, 10: 65, 12: 150, 13: 42, 14: 120},
    10: {0: 130, 1: 85, 2: 35, 4: 70, 5: 70, 6: 90, 8: 120, 9: 103, 10: 35, 12: 90, 13: 72, 14: 90},
    11: {0: 190, 1: 55, 2: 65, 4: 130, 5: 40, 6: 130, 8: 180, 9: 63, 10: 65, 12: 150, 13: 42, 14: 120},
    12: {0: 130, 1: 85, 2: 35, 4: 70, 5: 70, 6: 90, 8: 120, 9: 103, 10: 35, 12: 90, 13: 72, 14: 90},
    13: {0: 190, 1: 55, 2: 65, 4: 130, 5: 40, 6: 130, 8: 180, 9: 63, 10: 65, 12: 150, 13: 42, 14: 120},
    14: {0: 130, 1: 85, 2: 35, 4: 70, 5: 70, 6: 90, 8: 120, 9: 103, 10: 35, 12: 90, 13: 72, 14: 90},
    15: {0: 190, 1: 55, 2: 65, 4: 130, 5: 40, 6: 130, 8: 180, 9: 63, 10: 65, 12: 150, 13: 42, 14: 120},
    16: {0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110, 8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105}
}

dance4_phases = {
    1: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105
    },
    2: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 123, 10: 10, 12: 120, 13: 17, 14: 145
    },
    3: {
        0: 160, 1: 110, 2: 10, 4: 100, 5: 15, 6: 150,
        8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105
    },
    4: {
        0: 160, 1: 70, 2: 50, 4: 100, 5: 55, 6: 110,
        8: 150, 9: 83, 10: 50, 12: 120, 13: 57, 14: 105
    }
}

class GestureReceiver:
    def __init__(self, host='0.0.0.0', port=8888, callback=None):
        self.host = host
        self.port = port
        self.callback = callback
        self.running = False
        self.thread = None
        self.gesture_queue = queue.Queue()
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        print(f"✋ Gesture receiver started on {self.host}:{self.port}")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        print("✋ Gesture receiver stopped")
    
    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    server_socket.bind((self.host, self.port))
                    print(f"✅ Socket successfully bound to {self.host}:{self.port}")
                except OSError as e:
                    print(f"❌ Failed to bind socket to {self.host}:{self.port}: {e}")
                    print("⚠️ Ensure no other process is using port 8888 (e.g., run 'sudo netstat -tulnp | grep 8888')")
                    return
                server_socket.listen(1)
                server_socket.settimeout(1.0)
                print("📡 Waiting for gesture connections...")
                while self.running:
                    try:
                        conn, addr = server_socket.accept()
                        print(f"✋ Connected to gesture source: {addr}")
                        conn.settimeout(1.0)
                        data_buffer = ""
                        while self.running:
                            try:
                                data = conn.recv(1024).decode('utf-8')
                                if not data:
                                    print(f"✋ Gesture source disconnected: {addr}")
                                    break
                                data_buffer += data
                                while '\n' in data_buffer:
                                    line, data_buffer = data_buffer.split('\n', 1)
                                    try:
                                        gesture_data = json.loads(line)
                                        print(f"✋ Raw gesture data received: {gesture_data}")
                                        if self.callback:
                                            self.gesture_queue.put((gesture_data, addr))
                                    except json.JSONDecodeError as e:
                                        print(f"✋ Invalid gesture JSON: {line} | Error: {e}")
                            except socket.timeout:
                                continue
                            except Exception as e:
                                print(f"✋ Gesture receiver error: {e}")
                                break
                        conn.close()
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"✋ Gesture server error: {e}")
                        time.sleep(1)
        except Exception as e:
            print(f"❌ Fatal error in GestureReceiver: {e}")
            print("⚠️ Gesture receiver stopped unexpectedly")

class RobotMobileServer:
    def __init__(self):
        self.robot = RobotController()
        self.clients = set()
        self.running = True
        self.stop_event = threading.Event()
        self.gesture_control_enabled = False
        self.gesture_receiver = GestureReceiver(callback=self.handle_gesture)
        self.gesture_receiver.start()
        self.last_command = None
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Touch sensor integration (toggle stand/sit only)
        self.current_mode = "stand"  # Track current mode for touch
        self._touch_thread = threading.Thread(target=self._touch_sensor_monitor, daemon=True)
        self._touch_thread.start()
        self.loop = asyncio.get_event_loop()

    def _touch_sensor_monitor(self):
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        except Exception as e:
            print(f"⚠️ Touch sensor not available: {e}")
            return
        last_state = GPIO.input(26)
        while self.running:
            try:
                state = GPIO.input(26)
                if state and not last_state:
                    print("🟢 Touch detected on GPIO26 (toggle stand/sit)")
                    # Only toggle if in stand or sit mode
                    if self.current_mode == "stand":
                        asyncio.run_coroutine_threadsafe(self.handle_robot_command(None, "sit"), self.loop)
                        self.current_mode = "sit"
                    elif self.current_mode == "sit":
                        asyncio.run_coroutine_threadsafe(self.handle_robot_command(None, "stand"), self.loop)
                        self.current_mode = "stand"
                last_state = state
                time.sleep(0.05)
            except Exception as e:
                print(f"⚠️ Touch sensor error: {e}")
                time.sleep(1)
    
    def signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        self.gesture_receiver.stop()
        self.robot.cleanup_hardware()
        sys.exit(0)
    
    async def register_client(self, websocket):
        self.clients.add(websocket)
        await self.send_to_client(websocket, {
            "type": "connection",
            "status": "connected",
            "message": "🤖 Connected to Robot Control Server",
            "hardware_available": self.robot.hardware_initialized,
            "servo_config": self.robot.servo_config  # Send servo config to UI
        })
        print(f"✅ Client connected: {websocket.remote_address}")
    
    async def unregister_client(self, websocket):
        self.clients.discard(websocket)
        print(f"❌ Client disconnected: {websocket.remote_address}")
    
    async def send_to_client(self, websocket, data):
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def broadcast_to_all(self, data):
        if self.clients:
            await asyncio.gather(
                *[self.send_to_client(client, data) for client in self.clients.copy()],
                return_exceptions=True
            )
    
    def handle_gesture(self, gesture_data, addr):
        if not self.gesture_control_enabled:
            print("✋ Gesture received but gesture control is disabled")
            return
        gesture = gesture_data.get('gesture', 'Unknown')
        confidence = gesture_data.get('confidence', 0.0)
        source = gesture_data.get('source', str(addr))
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(gesture_data.get('timestamp', time.time())))
        gesture_message = (
            f"Received at {timestamp}:\n"
            f"  Gesture: {gesture}\n"
            f"  Confidence: {confidence:.1%}\n"
            f"  Source: {source}\n"
            f"{'-' * 40}"
        )
        print(gesture_message)
        gesture_map = {
            'Open Hand': 'walk',
            'Fist': 'stop',
            'Thumbs Up': 'backward',
            'Thumbs Up Ascending': 'backward',
            'Peace': 'sit',
            'Unknown': None
        }
        command = gesture_map.get(gesture)
        if confidence < 0.6:
            gesture = 'Unknown'
            command = None
        if command and command != self.last_command:
            self.last_command = command
            print(f"✋ Executing command from gesture: {command.upper()}")
            asyncio.create_task(self.handle_robot_command(None, command))
            asyncio.create_task(self.broadcast_to_all({
                "type": "gesture_status",
                "message": gesture_message,
                "command": command
            }))
        elif not command and self.last_command:
            self.last_command = None
            print("✋ Stopping robot due to unknown or low-confidence gesture")
            asyncio.create_task(self.handle_robot_command(None, 'q'))
            asyncio.create_task(self.broadcast_to_all({
                "type": "gesture_status",
                "message": gesture_message,
                "command": "stop"
            }))
        else:
            asyncio.create_task(self.broadcast_to_all({
                "type": "gesture_status",
                "message": gesture_message,
                "command": None
            }))
    
    async def process_gestures(self):
        while self.running:
            try:
                gesture_data, addr = self.gesture_receiver.gesture_queue.get_nowait()
                self.handle_gesture(gesture_data, addr)
            except queue.Empty:
                await asyncio.sleep(0.1)
    
    async def handle_servo_angle(self, websocket, channel, angle):
        if channel not in self.robot.servo_config:
            await self.send_to_client(websocket, {
                "type": "error",
                "message": f"❌ Invalid servo channel: {channel}"
            })
            return
        max_angle = 180 if self.robot.servo_config[channel]["type"] == "180" else 270
        # Use the input angle directly as the absolute angle, not an offset
        absolute_angle = max(0, min(float(angle), max_angle))  # Clamp to valid range
        try:
            self.robot.set_pose({channel: absolute_angle}, transition_time=0.1, steps=10)
            response = {
                "type": "servo_update",
                "channel": channel,
                "angle": absolute_angle,
                "offset": 0,  # No offset, using absolute angle
                "standing_angle": STANDING_ANGLES.get(channel, self.robot.servo_config[channel]["default"]),
                "name": self.robot.servo_config[channel]["name"],
                "status": "success",
                "message": f"🔧 Servo Ch{channel} ({self.robot.servo_config[channel]['name']}) set to {absolute_angle:.1f}°"
            }
            await self.broadcast_to_all(response)
        except Exception as e:
            await self.send_to_client(websocket, {
                "type": "error",
                "message": f"❌ Failed to set servo Ch{channel}: {str(e)}"
            })
    
    def execute_walk(self):
        print("🚶 Starting trot walk...")
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        while not self.stop_event.is_set():
            if self.robot.check_obstacle():
                distance = self.robot.get_distance()
                print(f"🚨 Obstacle detected at {distance:.1f}cm! Turning right...")
                obstacle_turn_cycles = 0
                max_turn_cycles = 10
                while self.robot.check_obstacle() and obstacle_turn_cycles < max_turn_cycles and not self.stop_event.is_set():
                    self.execute_turn_cycle(TURN_RIGHT_PHASES)
                    obstacle_turn_cycles += 1
                    time.sleep(0.1)
                print("✅ Obstacle cleared, resuming walk...")
                continue
            self.execute_walk_cycle()
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        print("✅ Walk complete")
    
    def execute_walk_cycle(self):
        for phase_idx in range(4):
            if self.stop_event.is_set():
                break
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4
            angles = STANDING_ANGLES.copy()
            angles.update(WALKING_PHASES["rear_left"][rl_fr])
            angles.update(WALKING_PHASES["front_right"][rl_fr])
            angles.update(WALKING_PHASES["rear_right"][rr_fl])
            angles.update(WALKING_PHASES["front_left"][rr_fl])
            self.robot.set_pose(angles, transition_time=0.015)
            time.sleep(0.0025)
    
    def execute_backward(self):
        print("↩️ Starting backward walk...")
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        while not self.stop_event.is_set():
            self.execute_backward_cycle()
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        print("✅ Backward walk complete")
    
    def execute_backward_cycle(self):
        for phase_idx in range(4):
            if self.stop_event.is_set():
                break
            rl_fr = phase_idx
            rr_fl = (phase_idx + 2) % 4
            angles = STANDING_ANGLES.copy()
            angles.update(BACKWARD_PHASES["rear_left"][rl_fr])
            angles.update(BACKWARD_PHASES["front_right"][rl_fr])
            angles.update(BACKWARD_PHASES["rear_right"][rr_fl])
            angles.update(BACKWARD_PHASES["front_left"][rr_fl])
            self.robot.set_pose(angles, transition_time=0.015)
            time.sleep(0.0025)
    
    def execute_turn_cycle(self, turn_phases):
        for phase_idx in range(4):
            if self.stop_event.is_set():
                break
            fr_rl = phase_idx
            fl_rr = (phase_idx + 2) % 4
            angles = STANDING_ANGLES.copy()
            angles.update(turn_phases["front_right"][fr_rl])
            angles.update(turn_phases["rear_left"][fr_rl])
            angles.update(turn_phases["front_left"][fl_rr])
            angles.update(turn_phases["rear_right"][fl_rr])
            self.robot.set_pose(angles, transition_time=0.015)
            time.sleep(0.0025)
    
    def execute_turn_right(self):
        print("➡️ Starting right turn...")
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        while not self.stop_event.is_set():
            self.execute_turn_cycle(TURN_RIGHT_PHASES)
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        print("✅ Right turn complete")
    
    def execute_turn_left(self):
        print("⬅️ Starting left turn...")
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        while not self.stop_event.is_set():
            self.execute_turn_cycle(TURN_LEFT_PHASES)
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        print("✅ Left turn complete")
    
    def execute_dance(self, mode):
        if mode == 1:
            phases = dance1_phases
        elif mode == 2:
            phases = dance2_phases
        elif mode == 3:
            phases = dance3_phases
        elif mode == 4:
            phases = dance4_phases
        else:
            print("❌ Invalid dance mode")
            return
        print(f"💃 Starting dance mode {mode}...")
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        while not self.stop_event.is_set():
            for phase in sorted(phases.keys()):
                if self.stop_event.is_set():
                    break
                self.robot.set_pose(phases[phase], transition_time=0.5, steps=20)
                time.sleep(0.5)
        self.robot.set_pose(STANDING_ANGLES, transition_time=0.015)
        print("✅ Dance complete")
    
    async def handle_robot_command(self, websocket, command, data=None):
        print(f"🎮 Executing command: {command.upper()}")
        try:
            # Mood/sound mapping logic
            if command in ['walk', 'backward']:
                # forward & backward
                dfplayer.send_command(0x08, 0, 2)  # aggressive.mp3 (track 2)
                roboeyes.set_mood('neutral')
                roboeyes.start()
            elif command in ['right', 'left']:
                # turn left & right
                dfplayer.send_command(0x08, 0, 6)  # sad.mp3 (track 6)
                roboeyes.set_mood('neutral')
                roboeyes.start()
            elif command in ['q', 'stop']:
                # Emergency stop
                dfplayer.send_command(0x08, 0, 8)  # barking.mp3 (track 7)
                roboeyes.set_mood('sad')
                roboeyes.start()
            elif command == 'dance':
                # Dancing
                dfplayer.send_command(0x08, 0, 7)  # howl.mp3 (track 8)
                roboeyes.set_mood('love')
                roboeyes.start()
            elif command == 'distance':
                # Object detecting
                dfplayer.send_command(0x08, 0, 1)  # dancing.mp3 (track 1)
                roboeyes.set_mood('angry')
                roboeyes.start()
            elif command == 'sit':
                # sit
                dfplayer.send_command(0x08, 0, 2)  # aggressive.mp3 (track 2)
                roboeyes.set_mood('love')
                roboeyes.start()
            elif command == 'stand':
                # stand
                dfplayer.send_command(0x08, 0, 2)  # aggressive.mp3 (track 2)
                roboeyes.set_mood('excited')
                roboeyes.start()
            if command == 'stand':
                self.stop_event.clear()
                self.robot.set_pose(STANDING_ANGLES)
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": "🦾 Robot standing"
                }
            elif command == 'sit':
                self.stop_event.clear()
                self.robot.set_pose(SITTING_ANGLES)
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": "🪑 Robot sitting"
                }
            elif command == 'walk':
                self.stop_event.clear()
                threading.Thread(target=self.execute_walk, daemon=True).start()
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": "🚶 Walking forward (with obstacle avoidance)"
                }
            elif command == 'backward':
                self.stop_event.clear()
                threading.Thread(target=self.execute_backward, daemon=True).start()
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": "↩️ Walking backward"
                }
            elif command == 'right':
                self.stop_event.clear()
                threading.Thread(target=self.execute_turn_right, daemon=True).start()
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": "➡️ Turning right"
                }
            elif command == 'left':
                self.stop_event.clear()
                threading.Thread(target=self.execute_turn_left, daemon=True).start()
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": "⬅️ Turning left"
                }
            elif command == 'dance':
                mode = data.get('mode', 1) if data else 1
                self.stop_event.clear()
                threading.Thread(target=self.execute_dance, args=(mode,), daemon=True).start()
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": f"💃 Dance mode {mode} started"
                }
            elif command == 'distance':
                distance = self.robot.get_distance()
                if distance == -1:
                    status_msg = "❌ Sensor timeout"
                    distance_text = "Error"
                else:
                    obstacle_status = "🚨 OBSTACLE!" if distance <= 30 else "✅ Clear"
                    status_msg = f"📏 Distance: {distance:.1f}cm | {obstacle_status}"
                    distance_text = f"{distance:.1f}cm"
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": status_msg,
                    "distance": distance_text
                }
            elif command == 'music_play':
                try:
                    # Resume or start playing music (play command)
                    dfplayer.send_command(0x0D)  # Resume playback
                    response = {
                        "type": "robot_response",
                        "command": command,
                        "status": "success",
                        "message": "🎵 Music playing"
                    }
                except Exception as e:
                    response = {
                        "type": "robot_response",
                        "command": command,
                        "status": "error",
                        "message": f"❌ Music play failed: {str(e)}"
                    }
            elif command == 'music_pause':
                try:
                    # Pause music playback
                    dfplayer.send_command(0x0E)  # Pause playback
                    response = {
                        "type": "robot_response",
                        "command": command,
                        "status": "success",
                        "message": "⏸️ Music paused"
                    }
                except Exception as e:
                    response = {
                        "type": "robot_response",
                        "command": command,
                        "status": "error",
                        "message": f"❌ Music pause failed: {str(e)}"
                    }
            elif command == 'music_stop':
                try:
                    # Stop music playback completely
                    dfplayer.send_command(0x16)  # Stop playback
                    response = {
                        "type": "robot_response",
                        "command": command,
                        "status": "success",
                        "message": "🛑 Music stopped"
                    }
                except Exception as e:
                    response = {
                        "type": "robot_response",
                        "command": command,
                        "status": "error",
                        "message": f"❌ Music stop failed: {str(e)}"
                    }
            elif command == 'q' or command == 'stop':
                self.stop_event.set()
                self.robot.set_pose(STANDING_ANGLES)
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "success",
                    "message": "🛑 Stopped - robot standing"
                }
            else:
                response = {
                    "type": "robot_response",
                    "command": command,
                    "status": "error",
                    "message": f"❌ Unknown command: {command}"
                }
            if websocket:
                await self.send_to_client(websocket, response)
        except Exception as e:
            print(f"❌ Error executing command {command}: {e}")
            if websocket:
                await self.send_to_client(websocket, {
                    "type": "robot_response",
                    "command": command,
                    "status": "error",
                    "message": f"❌ Command failed: {str(e)}"
                })
    
    async def handle_client_message(self, websocket, message):
        try:
            data = json.loads(message)
            if data.get("type") == "robot_command":
                command = data.get("command", "").lower().strip()
                if command:
                    await self.handle_robot_command(websocket, command, data)
                else:
                    await self.send_to_client(websocket, {
                        "type": "error",
                        "message": "❌ No command specified"
                    })
            elif data.get("type") == "gesture_control":
                self.gesture_control_enabled = data.get("enabled", False)
                await self.broadcast_to_all({
                    "type": "gesture_status",
                    "message": f"Gesture control {'enabled' if self.gesture_control_enabled else 'disabled'}"
                })
                print(f"✋ Gesture control {'enabled' if self.gesture_control_enabled else 'disabled'}")
            elif data.get("type") == "servo_angle":
                channel = data.get("channel")
                angle = data.get("angle")
                if channel is not None and angle is not None:
                    await self.handle_servo_angle(websocket, channel, angle)
                else:
                    await self.send_to_client(websocket, {
                        "type": "error",
                        "message": "❌ Missing channel or angle in servo command"
                    })
            else:
                await self.send_to_client(websocket, {
                    "type": "error",
                    "message": f"❌ Unknown message type: {data.get('type', 'none')}"
                })
        except json.JSONDecodeError:
            await self.send_to_client(websocket, {
                "type": "error",
                "message": "❌ Invalid JSON format"
            })
        except Exception as e:
            print(f"❌ Error handling message: {e}")
            await self.send_to_client(websocket, {
                "type": "error",
                "message": f"❌ Server error: {str(e)}"
            })
    
    async def websocket_handler(self, websocket):
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
        finally:
            await self.unregister_client(websocket)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

async def main():
    server = RobotMobileServer()
    print("🤖 Starting Robot Mobile Control Server...")
    print("=" * 50)
    local_ip = get_local_ip()
    port = 8765
    print(f"📡 WebSocket server: ws://0.0.0.0:{port}")
    print(f"🌐 Local access: ws://localhost:{port}")
    print(f"📱 Mobile access: ws://{local_ip}:{port}")
    print(f"🔧 Hardware available: {server.robot.hardware_initialized}")
    print("=" * 50)
    print("📋 Supported commands:")
    print("   • stand - Robot stands up")
    print("   • sit - Robot sits down")
    print("   • walk - Walk forward with obstacle avoidance")
    print("   • backward - Walk backward")
    print("   • right - Turn right")
    print("   • left - Turn left")
    print("   • dance (with mode 1-4) - Dance modes")
    print("   • distance - Check distance sensor")
    print("   • music_play - Resume/play music")
    print("   • music_pause - Pause music")
    print("   • music_stop - Stop music completely")
    print("   • q/stop - Stop movement and stand")
    print("   • Gestures: Open Hand (walk), Fist (stop), Thumbs Up (backward), Peace (sit)")
    print("   • Test mode: Adjust servo angles directly with sliders")
    print("=" * 50)
    print("🚀 Server ready! Connect your mobile interface to start controlling the robot.")
    print("💡 UI should be available at: http://localhost:8080/robot_mobile_control.html")
    print("⚠️ Press Ctrl+C to stop the server")
    try:
        async with websockets.serve(server.websocket_handler, "0.0.0.0", port):
            await asyncio.gather(
                server.process_gestures(),
                asyncio.Future()
            )
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested...")
    finally:
        server.gesture_receiver.stop()
        server.robot.cleanup_hardware()
        print("👋 Server stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Server error: {e}")
cmd = input("Enter command: ").lower().strip()