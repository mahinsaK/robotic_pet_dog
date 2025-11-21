# Robot Pet Dog Eyes - Installation and Usage Guide

## Overview
Animated robot eyes for your robotic pet dog with emotional expressions, walking mode, and distance-based reactions using a 3.5-inch Raspberry Pi touch display.

## Hardware Requirements
- Raspberry Pi 4B
- 3.5-inch ILI9486 display (480x320 pixels)
- IR proximity sensor (e.g., Sharp GP2Y0A21YK0F)
- 4x tactile buttons for controls
- Breadboard and jumper wires

## Wiring Connections

### Display (ILI9486)
```
Display Pin  →  Raspberry Pi Pin  →  GPIO/Physical
VCC (5V)     →  5V                →  Pin 2 or 4
GND          →  GND               →  Pin 6, 9, 14, etc.
MOSI         →  GPIO 10           →  Pin 19
SCLK         →  GPIO 11           →  Pin 23  
CS           →  GPIO 8 (CE0)      →  Pin 24
DC           →  GPIO 25           →  Pin 22
RST          →  GPIO 17           →  Pin 11
```

### IR Proximity Sensor
```
Sensor Pin   →  Raspberry Pi Pin
VCC          →  5V (Pin 4)
GND          →  GND (Pin 9)
OUT          →  GPIO 18 (Pin 12)
```

### Control Buttons
```
Button Function      →  GPIO Pin  →  Physical Pin
Walking Mode Toggle  →  GPIO 23   →  Pin 16
Mood Cycle          →  GPIO 24   →  Pin 18
Animation Trigger   →  GPIO 25   →  Pin 22
Cyclops Mode Toggle →  GPIO 26   →  Pin 37
```

Connect each button between the GPIO pin and GND with internal pull-up resistors enabled.

## Software Installation

### 1. Enable SPI Interface
```bash
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
sudo reboot
```

### 2. Install Required Python Libraries
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python packages
pip3 install --upgrade pip
pip3 install luma.lcd
pip3 install luma.core
pip3 install pillow
pip3 install RPi.GPIO
pip3 install numpy

# Install additional system libraries
sudo apt install python3-dev python3-pip python3-pil python3-numpy
sudo apt install fonts-dejavu-core  # For better text rendering
```

### 3. Install Display Driver (if needed)
```bash
# Clone the luma.lcd repository for latest drivers
git clone https://github.com/rm-hull/luma.lcd.git
cd luma.lcd
sudo python3 setup.py install
```

## Configuration

### Display Configuration
Edit the `robot_eyes_config.json` file to match your display setup:

```json
{
  "display_config": {
    "width": 480,
    "height": 320,
    "rotate": 1,
    "gpio_dc": 25,
    "gpio_rst": 17,
    "spi_port": 0,
    "spi_device": 0
  }
}
```

### GPIO Pin Configuration
Modify GPIO pins in the config file if your wiring differs:

```json
{
  "gpio_pins": {
    "ir_sensor": 18,
    "walking_toggle": 23,
    "mood_cycle": 24,
    "animation": 25,
    "cyclops_toggle": 26
  }
}
```

## Usage

### Running the Robot Eyes
```bash
cd /home/ubuntu/without_ros
python3 robot_pet_eyes.py
```

### Controls
- **Button 23**: Toggle walking mode (rhythmic eye movements)
- **Button 24**: Cycle through moods (Default, Happy, Tired, Angry, Curious, Sad, Afraid, Excited, Sleepy)
- **Button 25**: Trigger random animations (laugh, confused, wink, blink)
- **Button 26**: Toggle cyclops mode (single eye display)

### Automatic Features
- **Auto-blinking**: Eyes blink automatically at random intervals (2-8 seconds)
- **Distance reactions**: Eyes react to objects detected by IR sensor
  - Close (<20cm): Afraid or very curious expression
  - Medium (20-50cm): Curious or happy expression  
  - Far (>50cm): Return to default behavior
- **Idle behavior**: Random eye movements when not in walking mode
- **Walking mode**: Bouncing and tilting movements to simulate dog walking

### Mood System
The robot eyes express different emotions:

- **Default**: Neutral blue eyes
- **Happy**: Wider, green-tinted eyes with slight smile shape
- **Tired**: Droopy, warm-colored eyes
- **Angry**: Narrower, red-tinted eyes
- **Curious**: Large, cyan-colored eyes
- **Sad**: Smaller, blue-tinted droopy eyes
- **Afraid**: Very wide, yellow-tinted eyes with small pupils
- **Excited**: Large, magenta-tinted eyes with big pupils
- **Sleepy**: Very narrow, purple-tinted eyes

## Integration with Robot Control

### Adding to Existing Robot Scripts
To integrate with your existing robot control system (like p12-7.py), add these lines:

```python
# At the top of your robot script
import threading
from robot_pet_eyes import RobotPetEyes, EyeConfig, Mood

# Initialize eyes system
eyes_config = EyeConfig()
robot_eyes = RobotPetEyes(eyes_config)

# Start eyes in a separate thread
eyes_thread = threading.Thread(target=robot_eyes.run, kwargs={'fps': 30}, daemon=True)
eyes_thread.start()

# Control eyes based on robot actions
def robot_walk():
    robot_eyes.toggle_walking_mode()  # Enable walking mode
    # Your existing walk code here
    robot_eyes.toggle_walking_mode()  # Disable walking mode

def robot_detect_obstacle():
    robot_eyes.set_mood(Mood.AFRAID)
    # Your obstacle avoidance code here
```

### Synchronized Robot Behaviors
```python
# Mood changes based on robot actions
robot_eyes.set_mood(Mood.HAPPY)     # When robot starts walking
robot_eyes.set_mood(Mood.CURIOUS)   # When robot detects something
robot_eyes.set_mood(Mood.TIRED)     # When robot stops/sits
robot_eyes.set_mood(Mood.EXCITED)   # When robot receives pet/touch
```

## Troubleshooting

### Display Issues
```bash
# Check SPI is enabled
lsmod | grep spi

# Test SPI connection
ls /dev/spi*

# Check display initialization
python3 -c "from luma.lcd.device import ili9486; print('Display driver available')"
```

### GPIO Issues
```bash
# Check GPIO pin status
gpio readall

# Test button connections
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('Button state:', GPIO.input(23))
GPIO.cleanup()
"
```

### Performance Optimization
- Reduce FPS if display updates are slow: `robot_eyes.run(fps=20)`
- Disable unused features in config file
- Use smaller eye sizes for better performance
- Consider overclocking Raspberry Pi for smoother animations

## Customization

### Adding New Moods
Edit the `_get_mood_parameters()` method in `robot_pet_eyes.py`:

```python
Mood.CUSTOM: {
    'width_mod': 1.0, 'height_mod': 1.0,
    'color': (255, 128, 0), 'pupil_size': 1.0
}
```

### Custom Animations
Add new animation methods:

```python
def custom_animation(self, duration: float = 2.0):
    """Your custom animation"""
    # Animation code here
    pass
```

### Different Eye Shapes
Modify the `_draw_eye()` method to create different eye shapes (oval, angular, etc.).

## File Structure
```
/home/ubuntu/without_ros/
├── robot_pet_eyes.py          # Main robot eyes script
├── robot_eyes_config.json     # Configuration file
├── display1.py               # Original display test (reference)
└── ROBOT_EYES_README.md      # This file
```

## Support
For issues or customizations, check:
1. Wiring connections match the pin configuration
2. All required libraries are installed
3. SPI interface is enabled
4. Display driver compatibility
5. GPIO permissions (run with sudo if needed)

## License
This code is part of the Robot Pet Dog project and is provided for educational and personal use.
