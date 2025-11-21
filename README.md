# 🐕 Robotic Pet Dog Project

A comprehensive quadruped robot dog control system with mobile web interface, gesture recognition, and advanced movement capabilities.

## 🚀 Quick Start (Ubuntu CLI on Raspberry Pi)

### Prerequisites
- Raspberry Pi 4 (recommended) with Ubuntu Server/Desktop
- Python 3.8 or higher
- Git installed

### Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/mahinsaK/robotic_pet_dog.git
cd robotic_pet_dog
```

2. **Install Python dependencies:**
```bash
sudo apt update
sudo apt install python3-pip python3-venv
pip3 install asyncio websockets numpy RPi.GPIO adafruit-circuitpython-pca9685 board busio
```

3. **Set up permissions for GPIO:**
```bash
sudo usermod -a -G gpio $USER
sudo chmod 666 /dev/gpiomem
```

### 🎮 Running the Robot Control System

#### Method 1: Using the startup script (Recommended)
```bash
cd /path/to/robotic_pet_dog
chmod +x start_mobile_robot.sh
./start_mobile_robot.sh
```

#### Method 2: Manual startup commands
```bash
# Start HTTP server for web interface
cd /path/to/robotic_pet_dog && python3 -m http.server 8080 &

# Kill any existing processes
pkill -f "robot_mobile_backend.py" && pkill -f "http.server"

# Start the robot control system
cd /path/to/robotic_pet_dog && ./start_mobile_robot.sh
```

#### Method 3: Individual component startup
```bash
# Terminal 1: Start web server
cd /path/to/robotic_pet_dog
python3 -m http.server 8080

# Terminal 2: Start robot backend
cd /path/to/robotic_pet_dog
python3 robot_mobile_backend.py
```

### 🌐 Accessing the Control Interface

After starting the system:

1. **Web Interface**: Open your browser and navigate to:
   - Local access: `http://localhost:8080/robot_mobile_control.html`
   - Remote access: `http://[PI_IP_ADDRESS]:8080/robot_mobile_control.html`

2. **WebSocket Connection**: In the web interface, set the WebSocket URL to:
   - `ws://localhost:8765` (local)
   - `ws://[PI_IP_ADDRESS]:8765` (remote)

## 🤖 Hardware Requirements

### Essential Components
- **Raspberry Pi 4** (4GB+ RAM recommended)
- **PCA9685 PWM Driver Board**
- **12x Servo Motors** (SG90 or similar)
- **HC-SR04 Ultrasonic Sensor**
- **DFPlayer Mini MP3 Module**
- **TFT Display** (for robot eyes)
- **Touch Sensor** (GPIO 26)
- **Speaker** (for audio feedback)

### Servo Configuration (12 servos total)
```
Front Left Leg:  CH0 (Shoulder), CH1 (Thigh), CH2 (Knee)
Front Right Leg: CH4 (Shoulder), CH5 (Thigh), CH6 (Knee)
Rear Left Leg:   CH8 (Shoulder), CH9 (Thigh), CH10 (Knee)
Rear Right Leg:  CH12 (Shoulder), CH13 (Thigh), CH14 (Knee)
```

### Wiring Connections
```
PCA9685 -> Raspberry Pi:
- VCC -> 5V
- GND -> GND
- SDA -> GPIO 2 (SDA)
- SCL -> GPIO 3 (SCL)

Ultrasonic Sensor:
- TRIG -> GPIO 23
- ECHO -> GPIO 24
- VCC -> 5V
- GND -> GND

Touch Sensor:
- Signal -> GPIO 26
- VCC -> 3.3V
- GND -> GND
```

## 🎯 Features

### 🚶 Movement Capabilities
- **Basic Poses**: Stand, Sit
- **Walking**: Forward with obstacle avoidance
- **Turning**: Left and Right rotation
- **Backward Movement**: Reverse walking
- **Dance Modes**: 4 different dance routines

### 🎮 Control Methods
- **Web Interface**: Mobile-responsive control panel
- **Gesture Recognition**: Hand gesture control via camera
- **Touch Sensor**: Toggle between stand/sit
- **WebSocket API**: Real-time command processing

### 🎵 Audio & Visual
- **DFPlayer Integration**: Background music and sound effects
- **Robot Eyes**: TFT display with mood expressions
- **Status Feedback**: Real-time robot status updates

### 🚨 Safety Features
- **Obstacle Avoidance**: Ultrasonic sensor integration
- **Emergency Stop**: Immediate halt functionality
- **Hardware Simulation**: Safe testing without hardware

## 📱 Web Interface Commands

### Basic Controls
- **Stand**: `{"type": "robot_command", "command": "stand"}`
- **Sit**: `{"type": "robot_command", "command": "sit"}`
- **Walk**: `{"type": "robot_command", "command": "walk"}`
- **Stop**: `{"type": "robot_command", "command": "stop"}`

### Advanced Controls
- **Turn Right**: `{"type": "robot_command", "command": "right"}`
- **Turn Left**: `{"type": "robot_command", "command": "left"}`
- **Backward**: `{"type": "robot_command", "command": "backward"}`
- **Dance**: `{"type": "robot_command", "command": "dance", "mode": 1}`

### Sensor Commands
- **Distance Check**: `{"type": "robot_command", "command": "distance"}`

### Audio Controls
- **Play Music**: `{"type": "robot_command", "command": "music_play"}`
- **Pause Music**: `{"type": "robot_command", "command": "music_pause"}`
- **Stop Music**: `{"type": "robot_command", "command": "music_stop"}`

## 🤝 Gesture Recognition

Supported gestures (when enabled):
- **Open Hand** → Walk forward
- **Fist** → Stop movement
- **Thumbs Up** → Walk backward
- **Peace Sign** → Sit down

## 🔧 Configuration Files

### Key Files
- `robot_mobile_backend.py` - Main robot control server
- `start_mobile_robot.sh` - Startup script
- `robot_mobile_control.html` - Web interface
- `robot_eyes_config.json` - Display configuration
- `mpu6050_calibration.json` - Balance sensor calibration

### Servo Angle Customization
Edit the angle dictionaries in `robot_mobile_backend.py`:
```python
STANDING_ANGLES = {
    0: 160, 1: 70, 2: 50,    # Front Left
    4: 100, 5: 55, 6: 110,   # Front Right
    8: 150, 9: 83, 10: 50,   # Rear Left
    12: 120, 13: 57, 14: 105 # Rear Right
}
```

## 🐛 Troubleshooting

### Common Issues

**GPIO Permission Error:**
```bash
sudo usermod -a -G gpio $USER
sudo chmod 666 /dev/gpiomem
```

**I2C Not Enabled:**
```bash
sudo raspi-config
# Navigate to Interfacing Options > I2C > Enable
```

**Port Already in Use:**
```bash
sudo lsof -i :8080  # Check what's using port 8080
sudo lsof -i :8765  # Check what's using port 8765
pkill -f "http.server"  # Kill HTTP server
pkill -f "robot_mobile_backend.py"  # Kill robot backend
```

**Servo Not Moving:**
- Check power supply (servos need 5V with sufficient current)
- Verify PCA9685 connections
- Test with individual servo test scripts

## 📚 Project Structure

```
robotic_pet_dog/
├── robot_mobile_backend.py     # Main control server
├── start_mobile_robot.sh       # Startup script
├── robot_mobile_control.html   # Web interface
├── dfplayer_control.py         # Audio control
├── display_sanduni.py          # Robot eyes display
├── balance*.py                 # Balance control algorithms
├── dance*.py                   # Dance choreography
├── test_*.py                   # Hardware test scripts
├── Mpart/                      # Additional components
│   ├── MPU1/                   # Balance sensor code
│   └── esp32cam/              # Camera integration
└── README.md                   # This file
```

## 🌟 Advanced Features

### Custom Dance Creation
Add new dance routines by editing dance phase dictionaries:
```python
custom_dance_phases = {
    1: {0: 160, 1: 70, 2: 50, ...},  # Phase 1 angles
    2: {0: 180, 1: 90, 2: 30, ...},  # Phase 2 angles
    # Add more phases...
}
```

### Gesture Control Setup
1. Connect ESP32-CAM module
2. Run gesture detection script
3. Enable gesture control in web interface

### Remote Access via ngrok
```bash
# Install ngrok
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm.zip
unzip ngrok-stable-linux-arm.zip
./ngrok http 8080
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built for Raspberry Pi and Ubuntu systems
- Uses Adafruit CircuitPython libraries
- Web interface built with vanilla HTML/CSS/JavaScript
- Gesture recognition powered by OpenCV and MediaPipe

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed description and logs

---

**Happy Robot Building! 🤖🐕**