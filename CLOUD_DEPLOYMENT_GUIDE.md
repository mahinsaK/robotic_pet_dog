# Instructions for Cloud Deployment

## Deploy Relay Server to Cloud (Choose one):

### 1. **AWS EC2 (Free Tier Available)**
1. Launch EC2 instance (Ubuntu)
2. Install Python: `sudo apt update && sudo apt install python3 python3-pip`
3. Install websockets: `pip3 install websockets`
4. Upload relay_server.py
5. Run: `python3 relay_server.py`
6. Configure Security Group: Allow inbound port 8765
7. Use Elastic IP for permanent IP address
8. Access via: `ws://YOUR-EC2-IP:8765` or use Route 53 for domain

### 2. **DigitalOcean Droplet**
1. Create $5/month droplet (Ubuntu)
2. Same setup as AWS EC2
3. Access via: `ws://YOUR-DROPLET-IP:8765`

### 3. **Google Cloud Platform (Free Tier)**
1. Create Compute Engine instance
2. Same setup process
3. Use static IP address

### 4. **Heroku (Free Tier - Good for testing)**
1. Create Procfile: `web: python relay_server.py`
2. Modify relay_server.py to use PORT environment variable
3. Deploy via git
4. Access via: `wss://your-app-name.herokuapp.com` (note: wss for secure)

### 5. **Railway.app or Render.com (Modern alternatives)**
- Easy deployment from GitHub
- Automatic HTTPS/WSS
- Free tiers available

## Example Cloud-Ready Relay Server:
```python
# relay_server_cloud.py
import asyncio
import websockets
import json
import time
import os

PORT = int(os.environ.get('PORT', 8765))
HOST = '0.0.0.0'

# ... rest of relay server code ...

if __name__ == "__main__":
    print(f"Starting on {HOST}:{PORT}")
    asyncio.run(main())
```

## Usage:
1. Deploy relay server to cloud
2. Update robot: RELAY_URL = "ws://your-cloud-server.com:8765"
3. Update mobile app: value="ws://your-cloud-server.com:8765"
4. Access from anywhere in the world!
