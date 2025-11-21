# SpotMicro Robot p12-7.py Control Guide

## Overview
The `p12-7.py` script is an enhanced version of the original robot control system that adds **touch sensor toggle functionality** to switch between standing and sitting modes. This creates a more interactive pet robot experience.

## Key Changes from p12-6.py

### 1. Mode Renaming
- **"standing mode"** → **"straight mode"** (fully extended position)
- **"sitting mode"** → **"standing mode"** (ready for walking position)
- **NEW "sitting mode"** → **Low power relaxed position**

### 2. New Sitting Mode Angles
```python
sitting_angles = {
    0: 207, 1: 90, 2: 30,    # Front Left: shoulder, thigh, knee
    4: 90, 5: 35, 6: 130,    # Front Right: shoulder, thigh, knee
    8: 150, 9: 99, 10: 30,   # Rear Left: shoulder, thigh, knee
    12: 115, 13: 25, 14: 125 # Rear Right: shoulder, thigh, knee
}
```

### 3. Touch Sensor Integration
- **Hardware**: TTP223 touch sensor connected to GPIO26
- **Function**: Toggle between standing and sitting modes
- **Interaction**: Touch sensor acts like a pet's "belly button" for pose changes

## Hardware Configuration

### Servo Layout
```
Channel 0  -> FL shoulder -> 270° servo
Channel 1  -> FL thigh   -> 270° servo  
Channel 2  -> FL knee    -> 270° servo
Channel 4  -> FR shoulder -> 270° servo
Channel 5  -> FR thigh   -> 270° servo
Channel 6  -> FR knee    -> 180° servo
Channel 8  -> RL shoulder -> 180° servo
Channel 9  -> RL thigh   -> 270° servo
Channel 10 -> RL knee    -> 180° servo
Channel 12 -> RR shoulder -> 180° servo
Channel 13 -> RR thigh   -> 270° servo
Channel 14 -> RR knee    -> 180° servo
```

### Sensor Connections
- **Touch Sensor (TTP223)**: GPIO26 (with pull-down resistor)
- **Ultrasonic Sensor (HC-SR04)**: TRIG=GPIO23, ECHO=GPIO24
- **Servo Driver (PCA9685)**: I2C address 0x40

## Available Commands

### Basic Poses
- `straight` - Extended standing position (maximum height)
- `standing` - Ready position for walking (balanced stance) 
- `sitting` - Low power relaxed position (energy saving)

### Movement Commands
- `walk` - Trot walking with obstacle avoidance
- `right` - Turn right in place
- `left` - Turn left in place

### Interactive Features
- `toggle` - **👆 Touch sensor mode** (standing ⟷ sitting)
- `speed` - Change walking speed (slow/normal/fast/turbo)
- `distance` - Test ultrasonic sensor

### System Commands
- `q` - Quit program with safe servo shutdown

## Touch Toggle Mode

### How It Works
1. Enter toggle mode with `toggle` command
2. Robot initializes in **standing mode** (ready position)
3. Touch the TTP223 sensor to switch to **sitting mode** (relaxed)
4. Touch again to return to **standing mode**
5. Continue touching to toggle between poses
6. Press `Ctrl+C` to exit toggle mode

### Visual Feedback
```
🟢 STANDING MODE - robot ready for walking
🔴 SITTING MODE - robot in low power position
👆 Touch sensor to switch modes
```

### Touch Detection
- Uses GPIO rising edge detection
- 500ms debounce delay to prevent multiple triggers
- 50ms polling rate for responsive touch detection

## Safety Features

### Servo Safety
- Smooth transitions with configurable timing
- Neutral position reset on startup and shutdown
- PWM disable after movement completion
- Safe cleanup on program exit

### Obstacle Avoidance
- Automatic right turn when obstacles detected <30cm
- Real-time distance monitoring during walking
- Timeout protection for sensor failures

### Error Handling
- I2C initialization error checking
- GPIO cleanup on exit (signal handlers)
- Servo channel error protection

## Usage Examples

### Basic Operation
```bash
python3 p12-7.py

# Select commands:
straight   # Full extension
standing   # Ready for walking  
sitting    # Relaxed position
walk       # Forward walking
toggle     # Touch sensor mode
```

### Touch Sensor Interaction
```bash
# Start robot
python3 p12-7.py

# Enter toggle mode
> toggle

# Now touch the TTP223 sensor to switch poses
# Touch 1: Standing → Sitting
# Touch 2: Sitting → Standing  
# Touch 3: Standing → Sitting
# Continue...

# Press Ctrl+C to exit toggle mode
```

### Speed Control
```bash
# Enter speed menu
> speed
> fast      # Set to fast speed

# Walk with current speed  
> walk

# Or walk with specific speed
> walk slow
```

## Technical Implementation

### Touch Sensor Code
```python
# Initialize touch sensor
TOUCH_PIN = 26
GPIO.setup(TOUCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Detect touch (rising edge)
current_touch_state = GPIO.input(TOUCH_PIN)
if current_touch_state and not last_touch_state:
    # Touch detected - toggle pose
    toggle_state = not toggle_state
    if toggle_state:
        set_pose(sitting_angles, transition_time=0.8)
    else:
        set_pose(standing_angles, transition_time=0.8)
```

### Signal Handling
```python
def cleanup_gpio(signum=None, frame=None):
    # Reset servos to neutral
    # Disable PWM outputs  
    # Cleanup GPIO
    # Safe exit
```

## Pet Robot Behavior

### Interactive Features
1. **Touch Response**: Like petting a real dog's belly
2. **Pose Memory**: Remembers last position
3. **Smooth Transitions**: Natural movement between poses
4. **Visual Feedback**: Clear status messages

### Behavioral Patterns
- **Standing Mode**: Alert, ready for action
- **Sitting Mode**: Relaxed, energy-saving position  
- **Touch Response**: Immediate pose change
- **Obstacle Awareness**: Automatic avoidance during walking

## Troubleshooting

### Touch Sensor Issues
- Check GPIO26 connection
- Verify TTP223 power (3.3V)
- Test sensor with `test_touch_sensor.py`

### Servo Problems  
- Verify PCA9685 I2C connection
- Check servo power supply
- Test individual channels

### Walking Issues
- Verify ultrasonic sensor connections
- Check servo angle calibration
- Test distance sensor function

## Files Created
- `p12-7.py` - Main robot control script with touch toggle
- `test_p12-7.sh` - Test script for verification
- This documentation guide

The p12-7.py script successfully transforms the SpotMicro robot into an interactive pet with touch-responsive behavior while maintaining all original functionality.
