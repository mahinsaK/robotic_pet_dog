#!/usr/bin/env python3
import serial
import time
import sys
import os

class DFPlayerMini:
    def __init__(self):
        self.ser = None
        self.connected = False
        
    def connect(self):
        """Try to connect to DFPlayer via available serial ports"""
        serial_ports = ['/dev/ttyAMA0', '/dev/serial0', '/dev/ttyS0']
        
        for port in serial_ports:
            try:
                print(f"🔌 Trying to connect to {port}...")
                self.ser = serial.Serial(port, 9600, timeout=0.5)
                print(f"✅ Successfully connected to {port}")
                self.connected = True
                return True
            except serial.SerialException as e:
                print(f"❌ Failed to connect to {port}: {e}")
                continue
        
        print("❌ Could not connect to any serial port!")
        self.print_troubleshooting()
        return False
    
    def print_troubleshooting(self):
        """Print troubleshooting steps"""
        print("\n📝 Troubleshooting steps:")
        print("1. Enable UART: sudo raspi-config > Interface Options > Serial Port")
        print("   - Enable serial hardware: YES")
        print("   - Enable login shell over serial: NO")
        print("2. Add user to dialout group: sudo usermod -a -G dialout $USER")
        print("3. Reboot: sudo reboot")
        print("4. Check wiring:")
        print("   - DFPlayer VCC → Pi 3.3V (pin 1)")
        print("   - DFPlayer GND → Pi GND (pin 6)")
        print("   - DFPlayer RX → Pi GPIO14 (pin 8)")
        print("   - DFPlayer TX → Pi GPIO15 (pin 10)")
        print("5. Insert SD card with MP3 files in /01/ folder")
        
    def send_command(self, cmd, param=0, feedback=0):
        """Send command to DFPlayer"""
        if not self.connected:
            print("❌ Not connected to DFPlayer")
            return False
            
        try:
            data = [0x7E, 0xFF, 0x06, cmd, feedback, (param >> 8) & 0xFF, param & 0xFF]
            checksum = 0 - sum(data[1:7])
            data.extend([(checksum >> 8) & 0xFF, checksum & 0xFF, 0xEF])
            self.ser.write(bytes(data))
            return True
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return False
    
    def initialize(self):
        """Initialize DFPlayer"""
        print("🔄 Initializing DFPlayer...")
        self.send_command(0x09, 0x02)  # Set to SD card mode
        time.sleep(0.3)
        self.send_command(0x0C)  # Reset
        print("✅ DFPlayer initialized")
        time.sleep(0.5)
    
    def set_volume(self, volume):
        """Set volume (0-30)"""
        if 0 <= volume <= 30:
            self.send_command(0x06, volume)
            print(f"🔊 Volume set to {volume}")
        else:
            print("❌ Volume must be between 0-30")
    
    def play_folder_file(self, folder, file_num):
        """Play specific file from folder"""
        param = folder * 256 + file_num
        self.send_command(0x0F, param)
        print(f"🎵 Playing folder {folder:02d}, file {file_num:03d}")
    
    def play_next(self):
        """Play next track"""
        self.send_command(0x01)
        print("⏭️ Playing next track")
    
    def play_previous(self):
        """Play previous track"""
        self.send_command(0x02)
        print("⏮️ Playing previous track")
    
    def pause(self):
        """Pause playback"""
        self.send_command(0x0E)
        print("⏸️ Paused")
    
    def resume(self):
        """Resume playback"""
        self.send_command(0x0D)
        print("▶️ Resumed")
    
    def stop(self):
        """Stop playback"""
        self.send_command(0x16)
        print("⏹️ Stopped")
    
    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()
            print("🔌 Serial connection closed")
            self.connected = False

def main():
    """Main function - demo sequence"""
    df = DFPlayerMini()
    
    if not df.connect():
        sys.exit(1)
    
    try:
        # Initialize DFPlayer
        df.initialize()
        
        # Set volume
        df.set_volume(20)
        time.sleep(0.2)
        
        print("\n🎵 Starting demo sequence...")
        
        # Play file 1 from folder 1
        df.play_folder_file(1, 1)
        time.sleep(2)
        
        # Pause
        df.pause()
        time.sleep(1)
        
        # Resume
        df.resume()
        time.sleep(2)
        
        # Play next file
        df.play_next()
        time.sleep(2)
        
        # Stop
        df.stop()
        
        print("✅ Demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        df.stop()
    except Exception as e:
        print(f"❌ Error during operation: {e}")
    finally:
        df.close()

if __name__ == "__main__":
    main()
