import cv2
import mediapipe as mp
import numpy as np
import requests
import time
import math
import subprocess

class NetworkDiagnostic:
    def __init__(self, target_ip):
        self.target_ip = target_ip
        
    def ping_test(self):
        """Test basic ping connectivity"""
        print(f"🏓 Testing ping to {self.target_ip}...")
        
        try:
            # Use ping command for Linux (Raspberry Pi OS)
            cmd = ["ping", "-c", "4", self.target_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Ping successful!")
                return True
            else:
                print("❌ Ping failed!")
                return False
                
        except Exception as e:
            print(f"❌ Ping test error: {e}")
            return False
    
    def find_stream_url(self):
        """Find the working stream URL"""
        print(f"🔍 Finding stream URL for {self.target_ip}...")
        
        # Common ESP32-CAM endpoints
        endpoints = ["/stream", "/mjpeg/1", "/cam", "/video"]
        ports = [80, 81, 8080]
        
        for port in ports:
            for endpoint in endpoints:
                url = f"http://{self.target_ip}:{port}{endpoint}" if port != 80 else f"http://{self.target_ip}{endpoint}"
                
                try:
                    response = requests.get(url, timeout=3, stream=True)
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        if 'multipart' in content_type or 'mjpeg' in content_type:
                            print(f"✅ Found stream at: {url}")
                            return url
                except:
                    continue
        
        return None

class HandGestureDetector:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Gesture recognition variables
        self.gesture_buffer = []
        self.buffer_size = 5
        self.current_gesture = "None"
        
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    
    def is_finger_extended(self, landmarks, finger_tip, finger_pip, finger_mcp=None):
        """Check if a finger is extended"""
        if finger_mcp is None:
            # For thumb, compare tip with pip
            return landmarks[finger_tip].y < landmarks[finger_pip].y
        else:
            # For other fingers, compare tip with pip and pip with mcp
            return (landmarks[finger_tip].y < landmarks[finger_pip].y and 
                   landmarks[finger_pip].y < landmarks[finger_mcp].y)
    
    def detect_gesture(self, landmarks):
        """Detect hand gesture based on landmarks"""
        # Finger landmark indices
        THUMB_TIP = 4
        THUMB_MCP = 2
        INDEX_TIP = 8
        INDEX_PIP = 6
        INDEX_MCP = 5
        MIDDLE_TIP = 12
        MIDDLE_PIP = 10
        MIDDLE_MCP = 9
        RING_TIP = 16
        RING_PIP = 14
        RING_MCP = 13
        PINKY_TIP = 20
        PINKY_PIP = 18
        PINKY_MCP = 17
        
        # Check which fingers are extended
        thumb_extended = landmarks[THUMB_TIP].x > landmarks[THUMB_MCP].x  # Thumb logic is different
        index_extended = self.is_finger_extended(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP)
        middle_extended = self.is_finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
        ring_extended = self.is_finger_extended(landmarks, RING_TIP, RING_PIP, RING_MCP)
        pinky_extended = self.is_finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP)
        
        # Count extended fingers
        extended_fingers = [thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]
        extended_count = sum(extended_fingers)
        
        # Gesture detection logic
        if extended_count == 0:
            return "Fist"
        elif extended_count == 5:
            return "Open Hand"
        elif extended_count == 2 and index_extended and middle_extended and not ring_extended and not pinky_extended:
            return "Peace"
        elif extended_count == 1 and thumb_extended:
            return "Thumbs Up"
        elif extended_count == 1 and index_extended:
            return "Pointing"
        else:
            return "Unknown"
    
    def smooth_gesture(self, gesture):
        """Smooth gesture detection using a buffer"""
        self.gesture_buffer.append(gesture)
        if len(self.gesture_buffer) > self.buffer_size:
            self.gesture_buffer.pop(0)
        
        # Find most common gesture in buffer
        if len(self.gesture_buffer) >= 3:
            gesture_counts = {}
            for g in self.gesture_buffer:
                gesture_counts[g] = gesture_counts.get(g, 0) + 1
            
            most_common = max(gesture_counts, key=gesture_counts.get)
            if gesture_counts[most_common] >= 2:
                return most_common
        
        return self.current_gesture
    
    def process_frame(self, frame):
        """Process a single frame for hand gesture detection"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        gesture = "No Hand Detected"
        confidence = 0.0
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Detect gesture
                gesture = self.detect_gesture(hand_landmarks.landmark)
                smoothed_gesture = self.smooth_gesture(gesture)
                self.current_gesture = smoothed_gesture
                
                # Calculate confidence
                if len(self.gesture_buffer) >= 3:
                    gesture_counts = {}
                    for g in self.gesture_buffer:
                        gesture_counts[g] = gesture_counts.get(g, 0) + 1
                    confidence = gesture_counts.get(smoothed_gesture, 0) / len(self.gesture_buffer)
        
        return gesture, confidence

class ESP32GestureSystem:
    def __init__(self, esp32_ip="172.20.10.2"):
        self.esp32_ip = esp32_ip
        self.diagnostic = NetworkDiagnostic(esp32_ip)
        self.gesture_detector = HandGestureDetector()
        self.stream_url = None
        self.last_gesture = "None"
        
    def setup_connection(self):
        """Setup connection to ESP32-CAM"""
        print("ESP32-CAM Gesture Detection System")
        print("=" * 50)
        
        # Test basic connectivity to ESP32
        if not self.diagnostic.ping_test():
            print("\n❌ Cannot reach ESP32-CAM!")
            print("Please check:")
            print("1. ESP32-CAM is powered on")
            print("2. ESP32-CAM is connected to WiFi")
            print("3. IP address is correct")
            return False
        
        # Find stream URL
        self.stream_url = self.diagnostic.find_stream_url()
        if not self.stream_url:
            print("\n❌ Could not find video stream!")
            print("Please check ESP32-CAM web server is running")
            return False
        
        return True
    
    def run_gesture_detection(self):
        """Main gesture detection loop"""
        if not self.setup_connection():
            return
        
        print(f"\n🎯 Starting gesture detection...")
        print(f"📹 Stream URL: {self.stream_url}")
        print(f"🎯 Detecting: Peace ✌️, Open Hand ✋, Fist ✊, Unknown")
        
        cap = cv2.VideoCapture(self.stream_url)
        
        if not cap.isOpened():
            print("❌ Could not open video stream")
            return
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Failed to read frame")
                    break
                
                # Process frame for gesture detection
                gesture, confidence = self.gesture_detector.process_frame(frame)
                
                # Print gesture to terminal if it changes and is a valid gesture
                if gesture != self.last_gesture and gesture in ["Fist", "Open Hand", "Peace", "Unknown"]:
                    print(f"🤖 Gesture detected: {gesture} (confidence: {confidence:.1%})")
                    self.last_gesture = gesture
                
        except KeyboardInterrupt:
            print("\n⏹️ Stopping gesture detection...")
        
        finally:
            cap.release()
            print("✅ Cleanup completed")

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'cv2': 'opencv-python',
        'mediapipe': 'mediapipe',
        'numpy': 'numpy',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   pip install {package}")
        print("\nPlease install missing packages and try again.")
        return False
    
    return True

def main():
    # Check dependencies
    if not check_dependencies():
        return
    
    # Get ESP32-CAM IP
    esp32_ip = input("Enter ESP32-CAM IP (172.20.10.2): ").strip() or "172.20.10.2"
    
    # Create and run gesture detection system
    gesture_system = ESP32GestureSystem(esp32_ip)
    gesture_system.run_gesture_detection()

if __name__ == "__main__":
    main()