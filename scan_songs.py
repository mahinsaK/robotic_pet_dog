import serial
import time

print("🎵 Scan and Play All Songs")
print("=" * 30)

try:
    ser = serial.Serial('/dev/ttyAMA0', 9600)
    print("✅ Connected!")
    
    # Set SD card mode
    ser.write(b'\x7E\xFF\x06\x09\x00\x00\x02\xFF\xEF\xEF')
    time.sleep(1)
    
    print("🔍 Scanning for songs...")
    
    # Try to play songs from 1 to 50 (most SD cards won't have more)
    songs_found = 0
    
    for i in range(1, 51):
        print(f"Trying song {i}...", end="")
        
        # Play command
        cmd = [0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, i]
        checksum = 0 - sum(cmd[1:7])
        cmd.extend([(checksum >> 8) & 0xFF, checksum & 0xFF, 0xEF])
        ser.write(bytes(cmd))
        
        time.sleep(2)  # Let it play for 2 seconds
        
        print(" ✅ Found!")
        songs_found += 1
        
        # Stop
        ser.write(b'\x7E\xFF\x06\x16\x00\x00\x00\xFF\xEA\xEF')
        time.sleep(0.5)
        
        # Ask user if they want to continue
        response = input("Press ENTER to continue, 'q' to quit: ")
        if response.lower() == 'q':
            break
    
    print(f"🎵 Found {songs_found} songs total!")
    ser.close()
    
except KeyboardInterrupt:
    print("\n⏹️ Stopped by user")
    ser.close()
except Exception as e:
    print(f"❌ Error: {e}")
