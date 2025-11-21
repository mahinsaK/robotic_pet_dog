import serial
import time

print("🎵 Play All Songs on SD Card")
print("=" * 30)

try:
    # Connect
    ser = serial.Serial('/dev/ttyAMA0', 9600)
    print("✅ Connected to DFPlayer")
    
    # Set SD card mode
    print("📀 Setting SD card mode...")
    ser.write(b'\x7E\xFF\x06\x09\x00\x00\x02\xFF\xEF\xEF')
    time.sleep(1)
    
    # Play songs 1 to 10 (you can change this number)
    for song_num in range(1, 11):
        print(f"🎶 Playing song {song_num}...")
        
        # Play command for song number
        cmd = [0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, song_num]
        checksum = 0 - sum(cmd[1:7])
        cmd.extend([(checksum >> 8) & 0xFF, checksum & 0xFF, 0xEF])
        
        ser.write(bytes(cmd))
        time.sleep(3)  # Play each song for 3 seconds
        
        # Stop current song
        ser.write(b'\x7E\xFF\x06\x16\x00\x00\x00\xFF\xEA\xEF')
        time.sleep(0.5)
    
    print("✅ Finished playing all songs!")
    ser.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure SD card is inserted with MP3 files")
