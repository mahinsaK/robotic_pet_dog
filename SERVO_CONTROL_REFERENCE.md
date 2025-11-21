# 🤖 Quadruped Robot Servo Control - Quick Reference

## 🔄 Servo Rotation Directions

### Front Left Leg (FL)
- **Ch0 - FL Shoulder (270°)**: `- outwards` (decreasing angle moves leg outward)
- **Ch1 - FL Thigh (270°)**: `+ backwards` (increasing angle moves thigh backward)
- **Ch2 - FL Knee (270°)**: `- bending` (decreasing angle bends the knee)

### Front Right Leg (FR)
- **Ch4 - FR Shoulder (270°)**: `+ outwards` (increasing angle moves leg outward)
- **Ch5 - FR Thigh (270°)**: `- backwards` (decreasing angle moves thigh backward)
- **Ch6 - FR Knee (180°)**: `+ bending` (increasing angle bends the knee)

### Rear Left Leg (RL)
- **Ch8 - RL Shoulder (180°)**: `- outwards` (decreasing angle moves leg outward)
- **Ch9 - RL Thigh (270°)**: `+ backwards` (increasing angle moves thigh backward)
- **Ch10 - RL Knee (180°)**: `- bending` (decreasing angle bends the knee)

### Rear Right Leg (RR)
- **Ch12 - RR Shoulder (180°)**: `+ outwards` (increasing angle moves leg outward)
- **Ch13 - RR Thigh (270°)**: `- backwards` (decreasing angle moves thigh backward)
- **Ch14 - RR Knee (180°)**: `+ bending` (increasing angle bends the knee)

## 🏠 Default Angles (Standing Position)
- FL: Shoulder=200°, Thigh=10°, Knee=145°
- FR: Shoulder=100°, Thigh=115°, Knee=10°
- RL: Shoulder=150°, Thigh=19°, Knee=150°
- RR: Shoulder=120°, Thigh=110°, Knee=5°

## 🎮 Control Commands
- **Individual servo**: Enter channel number (0, 1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14)
- **Stand position**: Type `stand`
- **Set all servos**: Type `all`
- **Show directions**: Type `help`
- **Quit**: Type `q`

## 🚀 How to Run
```bash
cd /home/ubuntu/without_ros
./run_servo_control.sh
```

## 💡 Tips
- Start with small angle changes (±10°) to observe movement
- Use 'stand' command to return to safe position anytime
- Visual indicators: ✅ Default | 🟡 Close to default | 🔴 Away from default
- Always ensure robot is properly powered before starting
