#!/bin/bash

# Servo Control Interface Launcher
# This script launches the interactive servo control program

echo "🤖 Starting Quadruped Robot Servo Control Interface..."
echo "========================================================"
echo ""
echo "This program allows you to:"
echo "• Control each of the 12 servos individually"
echo "• View current, default, and maximum angles for each servo"
echo "• Reset to standing position"
echo "• Set all servos to the same angle"
echo ""
echo "Make sure your robot is powered and ready!"
echo ""

read -p "Press Enter to start the servo control interface..."

cd /home/ubuntu/without_ros
python3 servo_control_interface.py
