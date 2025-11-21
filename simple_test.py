import serial

print("🎵 Super Simple DFPlayer Test")

# Connect
ser = serial.Serial('/dev/ttyAMA0', 9600)
print("Connected!")

# Just send raw commands
print("Setting SD card mode...")
ser.write(b'\x7E\xFF\x06\x09\x00\x00\x02\xFF\xEF\xEF')

print("Playing first song...")
ser.write(b'\x7E\xFF\x06\x03\x00\x00\x01\xFF\xF6\xEF')

print("Done! Check if you hear music...")
ser.close()
