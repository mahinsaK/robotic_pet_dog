# 📱 Mobile Robot Control Setup Guide

## 🚀 Quick Start (Recommended)

### Step 1: Start Both Servers
```bash
cd /home/ubuntu/without_ros
./start_robot_servers.sh
```

### Step 2: Access from Your Phone
Open your phone's browser and go to:
**http://10.236.10.48:8080/mobile_robot_control.html**

---

## 🔧 Manual Setup (Alternative)

### Option A: Start Servers Separately

1. **Start WebSocket Server** (Terminal 1):
```bash
cd /home/ubuntu/without_ros
python3 working_robot_server.py
```

2. **Start Web Server** (Terminal 2):
```bash
cd /home/ubuntu/without_ros
python3 web_server.py
```

### Option B: Access HTML Files Directly

Copy the HTML file to your phone or access via:
- **Desktop version**: `http://10.236.10.48:8080/robot_control.html`
- **Mobile version**: `http://10.236.10.48:8080/mobile_robot_control.html`

---

## 📱 Phone Access Instructions

### 1. Network Connection
- Ensure your phone is connected to the **same WiFi network** as the Raspberry Pi
- The Pi should have IP: **10.236.10.48**

### 2. Open Browser
- Use any mobile browser (Chrome, Safari, Firefox, etc.)
- Go to: **http://10.236.10.48:8080/mobile_robot_control.html**

### 3. Connect to Robot
- The WebSocket URL should auto-fill: `ws://10.236.10.48:8765`
- Tap **"Connect"** button
- Wait for green "Connected" status

### 4. Control Your Robot
- **🏠 Stand**: Move to standing position
- **🪑 Sit**: Move to sitting position  
- **🚶 Walk**: Start walking forward (with obstacle avoidance)
- **↪️ Turn Right**: Turn right in place
- **↩️ Turn Left**: Turn left in place
- **📏 Distance**: Check ultrasonic sensor reading
- **🛑 Emergency Stop**: Stop all robot operations

---

## 🌐 Available URLs

### 🏠 Direct Connection (Current Setup)
| Purpose | URL | Description |
|---------|-----|-------------|
| **Mobile Control** | http://10.236.10.48:8080/mobile_robot_control.html | Touch-optimized interface |
| **Desktop Control** | http://10.236.10.48:8080/robot_control.html | Full desktop interface |
| **WebSocket** | ws://10.236.10.48:8765 | Robot command server |

### 🌐 Relay Server (Recommended for Dynamic IP)
| Purpose | URL | Description |
|---------|-----|-------------|
| **Mobile Control** | http://10.236.10.48:8080/mobile_robot_control_relay.html | Relay-enabled interface |
| **Relay WebSocket** | ws://YOUR-RELAY-SERVER:8765 | Stable relay server |

---

## � Relay Server Setup (Solves Dynamic IP Issues)

### Why Use a Relay Server?
The Raspberry Pi's IP address can change due to DHCP lease renewals, making direct connections unreliable. A relay server with a stable IP/domain solves this by acting as an intermediary.

### Step 1: Deploy Relay Server
Deploy `enhanced_relay_server.py` on a cloud server (AWS EC2, DigitalOcean, etc.) with a stable IP:

```bash
# On your cloud server
python3 enhanced_relay_server.py
```

### Step 2: Update Robot to Use Relay
On the Raspberry Pi, use the relay client instead:

```bash
cd /home/ubuntu/without_ros
# Edit robot_relay_client.py and set RELAY_URL
python3 robot_relay_client.py
```

### Step 3: Update Web App
Update your web app to connect to the relay server:

```javascript
// Instead of: ws://10.236.10.48:8765
const RELAY_URL = 'ws://your-server-domain.com:8765';
```

### Benefits:
- ✅ **Stable Connection**: No IP address changes
- ✅ **Works Behind NAT**: Robot initiates outbound connection
- ✅ **Auto-Reconnect**: Robot reconnects automatically
- ✅ **Multiple Controllers**: Multiple phones can control one robot
- ✅ **Status Monitoring**: Real-time connection status

---

## �🔍 Troubleshooting

### Phone Can't Access Website
- ✅ Check WiFi: Phone and Pi on same network?
- ✅ Check IP: Pi actually has 10.236.10.48?
- ✅ Check servers: Both HTTP and WebSocket running?
- ✅ Try: http://10.236.10.48:8080 (without filename)

### Robot Commands Don't Work
- ✅ WebSocket connected? (Green status)
- ✅ Robot powered? (Servos and Pi)
- ✅ Check servo connections
- ✅ Try distance sensor first (safest test)

### Connection Issues
- ✅ Restart servers: `./start_robot_servers.sh`
- ✅ Check firewall: `sudo ufw status`
- ✅ Try different browser on phone
- ✅ Check Pi IP: `hostname -I`

---

## 🛡️ Safety Tips

1. **Always test distance sensor first** - Safe way to verify system
2. **Start with "Stand" or "Sit"** - Before attempting movement
3. **Keep Emergency Stop ready** - Red stop button stops everything
4. **Ensure clear space** - Robot will move when commanded
5. **Monitor servo power** - Ensure adequate power supply

---

## 📊 Server Status

When running `./start_robot_servers.sh`, you should see:
```
✅ Both servers are running!

📱 PHONE ACCESS INSTRUCTIONS:
   Go to: http://10.236.10.48:8080/mobile_robot_control.html
```

**Both servers must be running for mobile control to work!**

---

# 🌐 Relay Server Architecture (Advanced Setup)

## 🎯 Problem This Solves
Your Raspberry Pi's IP address (`10.236.10.48`) may change over time due to DHCP, making direct connections unreliable. The relay server provides a stable intermediary.

## 🏗️ New Architecture
```
📱 Mobile App ←→ 🌐 Relay Server (Stable IP) ←→ 🤖 Raspberry Pi
```

## 🚀 Quick Relay Setup

### 1. Enhanced Relay Server (Already Created)
Your `relay_server.py` can be enhanced. Here's how to use it:

```bash
# On a cloud server (AWS EC2, DigitalOcean, etc.)
python3 -m pip install websockets
python3 relay_server.py
```

### 2. Robot Relay Client
Create a new file `robot_relay_client.py`:

```python
#!/usr/bin/env python3
"""Robot that connects TO relay server (instead of hosting its own server)"""
import asyncio
import websockets
import json
import time

RELAY_URL = "ws://YOUR_CLOUD_SERVER_IP:8765"  # Update this!

# TODO: Import your actual robot functions here
# from working_robot_server import walk_trot, set_pose, get_distance, etc.

class RobotRelayClient:
    def __init__(self):
        self.websocket = None
        self.running = True

    async def connect_to_relay(self):
        while self.running:
            try:
                print(f"🔄 Connecting to relay: {RELAY_URL}")
                self.websocket = await websockets.connect(RELAY_URL)
                
                # Identify as robot
                await self.websocket.send(json.dumps({
                    "type": "identify",
                    "client_type": "robot",
                    "client_info": {"name": "SpotMicro Robot Dog"}
                }))
                
                print("🤖✅ Connected to relay server!")
                await self.handle_messages()
                
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                print("⏰ Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def handle_messages(self):
        """Handle commands from web app via relay"""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                if data.get('type') == 'robot_command':
                    command = data.get('command', '').lower()
                    print(f"📥 Received command: {command}")
                    
                    # Execute command and send response
                    result = await self.execute_command(command)
                    response = {
                        "type": "response", 
                        "message": result,
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')
                    }
                    await self.websocket.send(json.dumps(response))
                    
            except Exception as e:
                print(f"❌ Message error: {e}")

    async def execute_command(self, command):
        """Execute robot commands - REPLACE WITH YOUR ACTUAL ROBOT CODE"""
        # TODO: Replace these with your actual robot functions
        if command in ['walk', 'forward']:
            # walk_trot(30, True)  # Your actual function
            print("🚶 Mock: Walking forward")
            return "Started walking with obstacle avoidance"
        elif command == 'stand':
            # set_pose(standing_angles)  # Your actual function  
            print("🏠 Mock: Standing")
            return "Standing pose set"
        elif command == 'sit':
            print("🪑 Mock: Sitting")
            return "Sitting pose set"
        elif command == 'distance':
            # dist = get_distance()  # Your actual function
            print("📏 Mock: Checking distance")
            return "Distance: 45.2 cm"  # Mock reading
        else:
            return f"Unknown command: {command}"

if __name__ == "__main__":
    print("🐕 SpotMicro Robot - Relay Client Mode")
    print("=" * 50)
    client = RobotRelayClient()
    asyncio.run(client.connect_to_relay())
```

### 3. Web App Update
Your web app needs minimal changes:

```javascript
// Change this line in your HTML/JavaScript:
// OLD: const socket = new WebSocket('ws://10.236.10.48:8765');
// NEW: const socket = new WebSocket('ws://YOUR_CLOUD_SERVER_IP:8765');

// Add identification after connection:
socket.onopen = () => {
    socket.send(JSON.stringify({
        type: 'identify',
        client_type: 'controller',
        client_info: { name: 'Mobile Controller' }
    }));
    console.log('Connected to relay server');
};

// Commands stay the same:
function sendCommand(cmd) {
    socket.send(JSON.stringify({
        type: 'robot_command',
        command: cmd
    }));
}
```

## 🌐 Deployment Options

### Option A: AWS EC2 (Recommended)
```bash
# 1. Create EC2 Ubuntu instance
# 2. Configure security group: Allow port 8765
# 3. SSH into instance:
sudo apt update
sudo apt install python3-pip
pip3 install websockets
# 4. Upload relay_server.py and run:
python3 relay_server.py
```

### Option B: DigitalOcean Droplet  
```bash
# 1. Create Ubuntu droplet
# 2. Configure firewall: Allow port 8765
# 3. Install and run relay server
```

### Option C: ngrok (Quick Testing)
```bash
# On your laptop/PC:
# Terminal 1:
python3 relay_server.py

# Terminal 2: 
ngrok tcp 8765
# Use the ngrok URL in your robot and web app
```

## ✅ Benefits

- **🔄 Auto-Reconnect**: Robot reconnects if connection drops
- **🌐 Stable Address**: Cloud server IP doesn't change  
- **🛡️ NAT Friendly**: Robot connects outbound (works behind routers)
- **📱 Multi-Device**: Multiple phones can control same robot
- **📊 Status Monitoring**: Real-time connection status

## 🧪 Testing

1. **Start relay server** on cloud server
2. **Run robot client** on Pi (with correct RELAY_URL)
3. **Open web app** with relay server URL
4. **Test commands** - should work from anywhere!

## 📋 Migration Checklist

- [ ] Deploy relay server to cloud platform  
- [ ] Update RELAY_URL in robot_relay_client.py
- [ ] Test robot connection to relay
- [ ] Update web app WebSocket URL
- [ ] Test web app → relay → robot communication
- [ ] Keep original setup as backup during testing

This setup makes your robot accessible from anywhere with internet! 🎉
