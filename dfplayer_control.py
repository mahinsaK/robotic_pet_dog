import serial
import time

SERIAL_PORT = '/dev/serial0'  # Use GPIO UART (ttyS0)

try:
    ser = serial.Serial(SERIAL_PORT, 9600, timeout=1)
    print(f"✅ Successfully connected to {SERIAL_PORT}")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    exit()

def send_command(cmd, param_high=0, param_low=0):
    data = [0x7E, 0xFF, 0x06, cmd, 0x00, param_high, param_low]
    checksum = -sum(data[1:])
    data += [(checksum >> 8) & 0xFF, checksum & 0xFF, 0xEF]
    try:
        ser.write(bytes(data))
        print(f"✅ Sent command: {data}")
    except Exception as e:
        print(f"❌ Error sending command: {e}")
    time.sleep(0.2)

# Set maximum volume (30 is max)
print("Setting volume to maximum (30)...")
send_command(0x06, 0, 30)
time.sleep(0.5)

# Interactive control loop - songs play until you give next command
print("DFPlayer Mini Control - Songs will play fully until you enter a command")
print("Commands: play <track>, next, prev, stop, exit")
print("Example: 'play 1' to play 001.mp3")

while True:
    try:
        cmd = input("Enter command: ").lower().strip()
        
        if cmd.startswith("play"):
            try:
                track = int(cmd.split()[1])
                print(f"Playing track {track} (00{track}.mp3)...")
                send_command(0x03, 0, track)
            except (IndexError, ValueError):
                print("Usage: play <track number> (e.g., 'play 1' for 001.mp3)")
        
        elif cmd == "next":
            print("Next track...")
            send_command(0x01)
        
        elif cmd == "prev" or cmd == "previous":
            print("Previous track...")
            send_command(0x02)
        
        elif cmd == "stop":
            print("Stopping playback...")
            send_command(0x16)
        
        elif cmd == "exit" or cmd == "quit":
            print("Exiting...")
            break
        
        else:
            print("Invalid command. Use: play <track>, next, prev, stop, exit")
            
    except KeyboardInterrupt:
        print("\nCaught Ctrl+C, exiting...")
        break

ser.close()
print("✅ Serial closed")