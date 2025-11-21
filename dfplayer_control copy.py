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


if __name__ == "__main__":
    # Interactive control loop - songs play until you give next command
    print("DFPlayer Mini Control - Moods will play repeatedly until you stop or change")
    print("Commands: dancing, aggressive, happy, tired, angry, sad, barking, howl, stop, exit")
    print("Example: 'dancing' to loop dancing.mp3, 'stop' to end current mood")

    while True:
        try:
            cmd = input("Enter command: ").lower().strip()
            
            if cmd == "dancing":
                print("Entering dancing mood - looping dancing.mp3 (track 1)...")
                send_command(0x08, 0, 1)  # Loop track 1 (dancing.mp3)
            
            elif cmd == "aggressive":
                print("Entering aggressive mood - looping aggressive.mp3 (track 2)...")
                send_command(0x08, 0, 2)  # Loop track 2 (aggressive.mp3)
            
            elif cmd == "happy":
                print("Entering happy mood - looping happy.mp3 (track 3)...")
                send_command(0x08, 0, 3)  # Loop track 3 (happy.mp3)
            
            elif cmd == "tired":
                print("Entering tired mood - looping tired.mp3 (track 4)...")
                send_command(0x08, 0, 4)  # Loop track 4 (tired.mp3)
            
            elif cmd == "angry":
                print("Entering angry mood - looping angry.mp3 (track 5)...")
                send_command(0x08, 0, 5)  # Loop track 5 (angry.mp3)
            
            elif cmd == "sad":
                print("Entering sad mood - looping sad.mp3 (track 6)...")
                send_command(0x08, 0, 6)  # Loop track 6 (sad.mp3)
            
            elif cmd == "barking":
                print("Entering barking mood - looping barking.mp3 (track 7)...")
                send_command(0x08, 0, 7)  # Loop track 7 (barking.mp3)
            
            elif cmd == "howl":
                print("Entering howl mood - looping howl.mp3 (track 8)...")
                send_command(0x08, 0, 8)  # Loop track 8 (howl.mp3)
            
            elif cmd == "stop":
                print("Stopping playback...")
                send_command(0x16)  # Stop current loop
            
            elif cmd == "exit" or cmd == "quit":
                print("Exiting...")
                break
            
            else:
                print("Invalid command. Use: dancing, aggressive, happy, tired, angry, sad, barking, howl, stop, exit")
                
        except KeyboardInterrupt:
            print("\nCaught Ctrl+C, exiting...")
            break

    ser.close()
    print("✅ Serial closed")