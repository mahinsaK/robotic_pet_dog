#!/usr/bin/env python3

import asyncio
import websockets
import json
import serial
import time

ser = serial.Serial('/dev/serial0', 9600, timeout=1)

def send_command(cmd, param_high=0, param_low=0):
    data = [0x7E, 0xFF, 0x06, cmd, 0x00, param_high, param_low]
    checksum = -sum(data[1:])
    data += [(checksum >> 8) & 0xFF, checksum & 0xFF, 0xEF]
    ser.write(bytes(data))
    time.sleep(0.1)

# Set volume (0-30)
send_command(0x06, 0, 20)

# Play track 1 (001.mp3)
send_command(0x03, 0, 1)

ser.close()

if __name__ == "__main__":
    asyncio.run(simple_test())
