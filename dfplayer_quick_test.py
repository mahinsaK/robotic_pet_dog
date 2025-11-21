#!/usr/bin/env python3
import serial
import time

def send_command(ser, cmd, param=0):
    """Send command to DFPlayer quickly"""
    data = [0x7E, 0xFF, 0x06, cmd, 0, (param >> 8) & 0xFF, param & 0xFF]
    checksum = 0 - sum(data[1:7])
    data.extend([(checksum >> 8) & 0xFF, checksum & 0xFF, 0xEF])
    ser.write(bytes(data))

# Quick connection test
print("🔌 Quick DFPlayer test...")
try:
    ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=0.1)
    print("✅ Connected!")
    
    # Minimal initialization
    send_command(ser, 0x09, 0x02)  # SD card mode
    time.sleep(0.1)
    send_command(ser, 0x06, 25)    # Volume 25
    time.sleep(0.1)
    
    print("🎵 Playing file...")
    send_command(ser, 0x0F, 1 * 256 + 1)  # Play folder 1, file 1
    
    print("▶️ Playing for 3 seconds...")
    time.sleep(3)
    
    print("⏹️ Stopping...")
    send_command(ser, 0x16)  # Stop
    
    ser.close()
    print("✅ Quick test completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure DFPlayer is connected and SD card has MP3s in /01/ folder")
