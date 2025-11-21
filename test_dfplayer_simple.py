import serial
import time

print("🎵 Simple DFPlayer Test")
print("=" * 30)

try:
    # Connect to DFPlayer
    ser = serial.Serial('/dev/ttyAMA0', 9600)
    print("✅ Connected to DFPlayer")
    
    # Simple command to play first song
    # Format: [Start, Ver, Len, CMD, Feedback, ParamH, ParamL, CheckH, CheckL, End]
    play_cmd = bytes([0x7E, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x01, 0xFF, 0xF6, 0xEF])
    
    print("🎶 Playing first song...")
    ser.write(play_cmd)
    
    print("⏰ Playing for 5 seconds...")
    time.sleep(5)
    
    # Stop command
    stop_cmd = bytes([0x7E, 0xFF, 0x06, 0x16, 0x00, 0x00, 0x00, 0xFF, 0xEA, 0xEF])
    ser.write(stop_cmd)
    print("⏹️ Stopped")
    
    ser.close()
    print("✅ Test completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n📝 Check:")
    print("- DFPlayer connected to /dev/ttyAMA0")
    print("- SD card inserted with MP3 files")
    print("- Files named: 0001.mp3, 0002.mp3, etc.")
